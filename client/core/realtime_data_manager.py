import copy
import time
import math
import threading
import numpy as np
from numba import njit
import logging
import matplotlib.pyplot as plt
from collections import deque
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from client.utils.util import run_time_decorator, action_chunk_2_joint_chunk, get_closest_index, get_action_layout_info
from client.core.inter_chunk_fusion import InterChunkFusion


@njit(fastmath=True, cache=True)
def _smooth_velocity_transition_numba(joint_seq, init_pos, init_vel, init_acc, dt=0.005, max_vel=2.0, max_acc=5.0, kp=5.0, kd=2.0):
    # max_vel=2.0, max_acc=4.0, kp=20.0, kd=6.0
    # max_vel=2.0, max_acc=4.0, kp=30.0, kd=10.0
    """
    This strategy uses position error and velocity feedback to compute acceleration in real time, generating a continuous and smooth velocity sequence.
    Note: Under the same parameter settings, the robot's operation speed using this strategy is slower than 'search_action' and 'poly'. 
    Please refer to [this YuQue docs](https://www.yuque.com/zhaoyongsheng-qjvyk/wkh5s4/ghfyxptztpot0pyt) for acceleration, or contact the developers for assistance.

    This function is **accelerated by Numba** using `@njit`, which compiles the
    Python code into optimized machine code in *nopython mode*.
    Key acceleration strategies:
      1. `@njit`: eliminates Python interpreter overhead by compiling to native code.
      2. Loop-based implementation (no Python objects or dynamic typing),
         enabling efficient JIT optimization.
      3. `fastmath=True`: allows aggressive floating-point optimizations
         (acceptable for control / smoothing tasks with tolerance to small
         numerical errors).
      4. `cache=True`: caches the compiled binary to disk to avoid recompilation
         on subsequent runs.

    Note:
      - All inputs must be NumPy arrays with fixed dtypes (e.g., float32/float64).
      - Dynamic Python features and object operations are intentionally avoided
        to ensure compatibility with Numba's nopython mode.

    Parameters
    ----------
    joint_seq : ndarray of shape (dof, T)
        Target joint position sequence to be tracked.
    init_pos : ndarray of shape (dof,)
        Initial joint positions.
    init_vel : ndarray of shape (dof,)
        Initial joint velocities.
    init_acc : ndarray of shape (dof,)
        Initial joint accelerations.
    dt : float, optional
        Time step for discrete integration.
    max_vel : float, optional
        Maximum allowed joint velocity (symmetric bound).
    max_acc : float, optional
        Maximum allowed joint acceleration (symmetric bound).
    kp : float, optional
        Proportional gain of the PD controller.
    kd : float, optional
        Derivative gain of the PD controller.

    Returns
    -------
    pos_seq : ndarray of shape (dof, T)
        Smoothed joint position sequence.
    vel_seq : ndarray of shape (dof, T)
        Corresponding joint velocity sequence.
    acc_seq : ndarray of shape (dof, T)
        Corresponding joint acceleration sequence.
    """

    # Number of degrees of freedom and time steps
    dof, T = joint_seq.shape

    # Current joint states (copied to avoid modifying inputs)
    pos = init_pos.copy()
    vel = init_vel.copy()
    acc = init_acc.copy()

    # Output buffers
    pos_seq = np.zeros((dof, T))
    vel_seq = np.zeros((dof, T))
    acc_seq = np.zeros((dof, T))

    # Time integration loop
    for i in range(T):
        # Target joint positions at current timestep
        target = joint_seq[:, i]

        # Per-joint PD control and state update
        for j in range(dof):
            # PD control law (position error + velocity damping)
            acc[j] = kp * (target[j] - pos[j]) - kd * vel[j]

            # Acceleration saturation
            if acc[j] > max_acc:
                acc[j] = max_acc
            elif acc[j] < -max_acc:
                acc[j] = -max_acc

            # Velocity integration
            vel[j] += acc[j] * dt

            # Velocity saturation
            if vel[j] > max_vel:
                vel[j] = max_vel
            elif vel[j] < -max_vel:
                vel[j] = -max_vel

            # Position integration
            pos[j] += vel[j] * dt

            # Record states
            pos_seq[j, i] = pos[j]
            vel_seq[j, i] = vel[j]
            acc_seq[j, i] = acc[j]

    return pos_seq, vel_seq, acc_seq


class RealtimeDataManager():
    """Real-time data manager for handling observation data and action chunks in VLA inference system.
    
    This class manages the buffering and processing of observation data from robots,
    action chunks from VLA models, and provides thread-safe access to these data structures.
    It also handles trajectory fitting and timing synchronization between observation and control.
    """
    
    def __init__(self, rdm_config: ConfigDict):
        """Initialize the RealtimeDataManager.
        
        Args:
            rdm_config (ConfigDict): Configuration dictionary containing buffer sizes and other parameters.
        """
        self.logger = logging.getLogger(__name__)
        self.rdm_config = rdm_config
        self.action_layout = dict(rdm_config.action_layout) if hasattr(rdm_config, 'action_layout') else {}
        self.action_dim, self.joint_indices, self.step_indices = get_action_layout_info(self.action_layout)
        self.observe_buffer = deque(maxlen=rdm_config.max_len)
        self.action_chunks = []
        self.timestamp_chunks = []
        self.action_thread_lock = threading.Lock()
        self.observe_thread_lock = threading.Lock()
        self.polynomial_thread_lock = threading.Lock()
        
        # Timestamp of the first observe data for inference
        self.init_observe_timestamp = None
        self.frame_count = 0
        self.action_chunk_fitted = None
        self.vel_chunk_fitted = None
        self.acc_chunk_fitted = None
        self.timestamps_fitted = None
        self.action_chunk_index = None
        self.prob_progress = None
        self.old_buffer = None

        # For visualization purposes
        self.action_chunk_last = None
        self.timestamp_last = None
        self.isDraw = False

        # Timing markers for inference, trajectory fitting and control
        self.start_infer_marker = 0.0
        self.start_traj_marker = 0.0
        self.start_ctrl_marker = 0.0
        self.avg_infer_time = 0.0
        self.avg_traj_time = 0.0
        self.infer_count = 0

        # Syncchronous Runing Flag
        self.sync_running = False

        # Inter-chunk transition / fusion helper
        self.inter_chunk_fusion = InterChunkFusion(logger=self.logger)

    def add_infer_count(self):
        """Add one to infer count for each inference step.
        Returns:
            None.
        """
        self.infer_count += 1

    def set_init_observe_timestamp(self, timestamp):
        """Set the timestamp of the first observe data to inference. The timestamp comes from robot observations.

        Args:
            timestamp (int): The timestamp of the first observe data to inference in nano seconds.
        """
        self.init_observe_timestamp = timestamp
    
    def set_observe_time_marker(self, timestamp):
        """Set the local timestamp when received the observe frame from robot. Used for calculating the inference time.

        Args:
            timestamp (float): The local timestamp in seconds.
        """
        self.observe_marker = timestamp
        
    def set_infer_time_marker(self):
        """Set the local timestamp when start inference. Used for calculating the inference time.
        """
        self.start_infer_marker = time.perf_counter()
        print(f"Start inference at {self.start_infer_marker:.4f} s")
        
    def set_traj_time_marker(self):
        """Set the local timestamp when start trajectory fitting. Used for calculating the trajectory fitting time.
        """
        self.start_traj_marker = time.perf_counter()
        # print(f"Start trajectory fitting at {self.start_traj_marker:.4f} s")
        
    def set_control_time_marker(self):
        """Set the local timestamp when start control. Used for calculating the control time.
        """
        self.start_ctrl_marker = time.perf_counter()
    
    def compute_avg_infer_time(self):
        """Compute the average inference time. The average inference time is used to set the offset of the action chunk.
        """
        # self.last_infer_time = self.currt_infer_time
        currt_infer_time = self.start_traj_marker - self.start_infer_marker
        self.avg_infer_time = (self.avg_infer_time * (self.infer_count - 1) + currt_infer_time) / self.infer_count
        self.logger.debug(f'avg infer time: {self.avg_infer_time}')
        # print(f"avg infer time: {self.avg_infer_time}, infer count: {self.infer_count}")

    def compute_avg_traj_time(self):
        """Compute the average trajectory fitting time. The average trajectory fitting time is used to set the offset of the action chunk.
        """
        # self.last_traj_time = self.currt_traj_time
        currt_traj_time = self.start_ctrl_marker - self.start_traj_marker
        self.avg_traj_time = (self.avg_traj_time * (self.infer_count - 1) + currt_traj_time) / self.infer_count
        # self.logger.debug(f'avg traj time: {self.avg_traj_time}')

    def _get_joint_indices(self, action_chunk):
        if self.joint_indices:
            return self.joint_indices
        return list(range(action_chunk.shape[0]))

    def _get_step_indices(self, action_chunk):
        if self.step_indices:
            return self.step_indices
        joint_indices = set(self._get_joint_indices(action_chunk))
        return [index for index in range(action_chunk.shape[0]) if index not in joint_indices]
    
    def add_observe_data(self, frame):
        """Add observe data to buffer. The observe data is a dictionary containing the robot state, camera images and timestamps.

        Args:
            frame (dict): The observe data frame. The keys of the dictionary are 'robot_state', 'camera_images' and 'timestamps'.
        """
        self.frame_count += 1
        # Skip the first few frames as they may be unstable
        if self.frame_count > 5:
            with self.observe_thread_lock:
                self.observe_buffer.append(frame)

    def update_action_chunk_raw(self, action_chunk, timestamp_chunk):
        """Update the raw action chunk and timestamp chunk predicted by the VLA model.

        Args:
            action_chunk (list): The action chunk predicted by the VLA model. It is a list of actions, each action is an np array of joint angles.
            timestamp_chunk (list): The timestamp chunk corresponding to the action chunk. It is a list of timestamps, each timestamp is a float. The unit is second.
        """
        # Ensure thread safety when updating action chunks
        with self.action_thread_lock:
            # Align action chunk timestamps with observation data timestamps
            # First frame starts at 0.0, subsequent frames are relative to the first frame
            timestamp_chunk[0] = 0.0
            for index in range(1, len(timestamp_chunk)):
                timestamp_chunk[index] = timestamp_chunk[index] + timestamp_chunk[0]
            self.action_chunks = action_chunk
            self.timestamp_chunks = timestamp_chunk
        
        rounded = [round(x, 4) for x in self.timestamp_chunks]

    @run_time_decorator
    def fusionActionChunks(self, action_chunk, timestamp_chunk):
        """Fuse new action chunk with existing action chunks.
        
        This method is deprecated and should not be used in new code.
        Use 'update_action_chunk_raw' instead.
        
        Args:
            action_chunk (list): New action chunk to fuse.
            timestamp_chunk (list): Corresponding timestamp chunk.
        """
        candidate_index = 0
        for index in range(len(timestamp_chunk)):
            if timestamp_chunk[index] > self.timestamp_chunks[0]:
                candidate_index = index
                break
        assign_index = get_closest_index(self.timestamp_chunks, timestamp_chunk[candidate_index])
        
        # Perform fusion
        target_chunk_len = len(self.timestamp_chunks)
        currt_chunk_len = len(action_chunk)
        for index in range(currt_chunk_len - candidate_index):
            if assign_index + index < target_chunk_len:
                self.action_chunks[assign_index + index] = (self.action_chunks[assign_index + index] + action_chunk[candidate_index + index]) / 2.0
                self.timestamp_chunks[assign_index + index] = (self.timestamp_chunks[assign_index + index] + timestamp_chunk[candidate_index + index]) / 2.0
            else:
                self.action_chunks.append(action_chunk[candidate_index + index])
                self.timestamp_chunks.append(timestamp_chunk[candidate_index + index])
        
    def popActionData(self, num_samples=32):
        """Pop action data from the action chunks buffer.
        
        This method is deprecated and should not be used in new code.
        Use 'update_action_chunk_raw' instead.
        
        Args:
            num_samples (int): Number of samples (unused parameter).
            
        Returns:
            tuple: (action, timestamp) or (None, None) if buffer is empty.
        """
        with self.action_thread_lock:
            if self.action_chunks:
                return self.action_chunks.pop(0), self.timestamp_chunks.pop(0)
            else:
                return None, None
    
    def pop_action_chunk(self, time_offset = 0.0, num_samples=32):
        """Returns the action chunk and timestamp chunk with the given time offset and number of samples for trajectory fitting.

        Args:
            time_offset (float, optional): The action data is discarded if its timestamp is smaller the time offset. Defaults to 0.0.
            num_samples (int, optional): The number of samples to return. Defaults to 32.

        Returns:
            np.array: The timestamp chunks in numpy array format.
            np.array: The action chunks in numpy array format.
        """
        currt_time = 0.0
        target_time = currt_time + time_offset
        self.logger.debug(f'currt_time: {currt_time}, target_time: {target_time}')
        
        # Find the first valid data frame index
        valid_index = None
        for index, timestamp in enumerate(self.timestamp_chunks):
            if timestamp > target_time:
                valid_index = index
                break
        if valid_index is None:
            print("[Error] No valid data in action chunk.")
            return None, None
        
        # Data fitting needs to look back a few frames to prevent non-smooth fitting results
        start_index = max(0, valid_index-1)
        end_index = min(len(self.action_chunks), start_index + num_samples)
        
        timestamp_chunks_np = np.array(self.timestamp_chunks[start_index:end_index])
        action_chunks_np = np.array(action_chunk_2_joint_chunk(self.action_chunks[start_index:end_index]))
        return timestamp_chunks_np, action_chunks_np

    def getCurrentTime(self):
        """Get the current time based on the fitted timestamps.
        
        This method is deprecated and should not be used in new code.
        
        Returns:
            float: Current time or 0.0 if action_chunk_index is None.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return 0.0
            else:
                return self.timestamps_fitted[self.action_chunk_index]
                
    def getCurrentActionIndex(self):
        """Get the current action index.
        
        Returns:
            int: Current index or 0 if action_chunk_index is None.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return 0
            else:
                return self.action_chunk_index
                
    def getFutureTime(self, index_offset=0):
        """Get the future time based on the fitted timestamps with an index offset.
        
        This method is deprecated and should not be used in new code.
        
        Args:
            index_offset (int): Index offset from current position.
            
        Returns:
            float: Future time or 0.0 if action_chunk_index is None.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return 0.0
            else:
                length = len(self.timestamps_fitted)
                return self.timestamps_fitted[min(length - 1, self.action_chunk_index + index_offset)]
                
    def getFittedActionChunk(self, index_offset=0, num_samples=20):
        """Get fitted action chunk with specified offset and number of samples.
        
        This method is deprecated and should not be used in new code.
        
        Args:
            index_offset (int): Index offset from current position.
            num_samples (int): Number of samples to return.
            
        Returns:
            tuple: (timestamps, action_chunk) or (None, None) if invalid.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None or num_samples <= 0:
                return None, None
            else:
                total_len = len(self.timestamps_fitted)
                start_index = min(self.action_chunk_index + index_offset, total_len-1) 
                end_index = min(self.action_chunk_index + index_offset + num_samples, total_len)
                return self.timestamps_fitted[start_index:end_index], self.action_chunk_fitted[:, start_index:end_index]
    
    @staticmethod
    def _smooth_velocity_transition(joint_seq, init_pos, init_vel, init_acc, dt=0.005, max_vel=2.0, max_acc=5.0, kp=5.0, kd=2.0):
        # max_vel=2.0, max_acc=4.0, kp=20.0, kd=6.0
        # max_vel=2.0, max_acc=4.0, kp=30.0, kd=10.0
        """
        This strategy uses position error and velocity feedback to compute acceleration in real time, generating a continuous and smooth velocity sequence.
        Note: Under the same parameter settings, the robot's operation speed using this strategy is slower than 'search_action' and 'poly'. 
        Please refer to [this YuQue docs](https://www.yuque.com/zhaoyongsheng-qjvyk/wkh5s4/ghfyxptztpot0pyt) for acceleration, or contact the developers for assistance.

        Args:
            joint_seq: np.ndarray, target position sequence
            init_pos: initial joint position
            init_vel: initial joint velocity
            init_acc: initial joint acceleration
            max_vel: maximum allowed velocity
            max_acc: maximum allowed acceleration
            dt: simulation timestep
            kp: proportional gain (position error term)
            kd: damping gain (velocity feedback term)

        Returns:
            pos_seq, vel_seq, acc_seq: simulated smooth position, velocity, and acceleration sequences
        """
        pos = init_pos
        vel = init_vel
        acc = init_acc

        pos_seq = np.zeros_like(joint_seq)
        vel_seq = np.zeros_like(joint_seq)
        acc_seq = np.zeros_like(joint_seq)

        # dt = dt * 2

        for i in range(joint_seq.shape[1]):
            target = joint_seq[:, i]

            # Compute position error
            error = target - pos
            
            # PD controller to compute desired acceleration
            acc = kp * error - kd * vel
            
            # Clip acceleration
            acc = np.clip(acc, -max_acc, max_acc)
            
            # Update velocity
            vel += acc * dt
            vel = np.clip(vel, -max_vel, max_vel)
            
            # Update position
            pos += vel * dt

            pos_seq[:, i] = pos
            vel_seq[:, i] = vel
            acc_seq[:, i] = acc

        return pos_seq, vel_seq, acc_seq
    
    def update_action_chunk_fitted(self,
                                action_chunk_fitted,
                                vel_chunk_fitted,
                                acc_chunk_fitted,
                                timestamps_fitted,
                                prob_progress=None,
                                inter_chunk_mode = None,
                                search_length = 20,
                                smooth_action = False,
                                smooth_length = 20,
                                smooth_base = 0.1,
                                smooth_ratio = 0.5,
                                gripper_offset = 40):
        """Update action chunk with the new fitted action chunk.

        Args:
            action_chunk_fitted (_type_): _description_
            vel_chunk_fitted (_type_): _description_
            timestamps_fitted (_type_): _description_
            prob_progress (np.array, optional): Array of prob_progress values aligned with action chunk. Defaults to None.
            search_action (bool, optional): True to search the start index for new fitted action chunk. Defaults to False.
            search_length (int, optional): Search length. Defaults to 20.
            smooth_action (bool, optional): True to smooth the action between the old action chunk and new action chunk. Defaults to False.
            smooth_length (int, optional): Smooth length. Defaults to 20.
            smooth_base (float, optional): Smooth base value. Defaults to 0.1.
            smooth_ratio (float, optional): Smooth ratio value. Defaults to 0.5.
            gripper_offset (int, optional): Gripper offset to adjust the delay of gripper response. Defaults to 25.
        """
        # update index firstly;
        if self.action_chunk_index is None or self.sync_running:
            with self.polynomial_thread_lock:
                self.action_chunk_index = 0
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
                self.acc_chunk_fitted = acc_chunk_fitted
                self.timestamps_fitted = timestamps_fitted
                self.prob_progress = prob_progress

        else: # update action chunk fitted secondly;
            # Calculate time offset from observation to trajectory fitting completion
            target_chunk_index = 0
            time_offset = self.start_ctrl_marker - self.observe_marker
            self.logger.debug(f'total inference time: {time_offset} s')
            
            for index in range(len(timestamps_fitted)):
                if timestamps_fitted[index] > time_offset:
                    target_chunk_index = index
                    break
            currt_action = None
            currt_vel = None
            joint_indices = self._get_joint_indices(action_chunk_fitted)
            step_indices = self._get_step_indices(action_chunk_fitted)
            with self.polynomial_thread_lock:
                currt_action_full = self.action_chunk_fitted[:, self.action_chunk_index].copy()
                currt_vel_full = self.vel_chunk_fitted[:, self.action_chunk_index].copy()
                currt_acc_full = self.acc_chunk_fitted[:, self.action_chunk_index].copy() if self.acc_chunk_fitted is not None else np.zeros_like(currt_vel_full)
                if self.action_chunk_index > 0 and self.vel_chunk_fitted is not None and self.timestamps_fitted is not None:
                    prev_vel = self.vel_chunk_fitted[:, self.action_chunk_index - 1]
                    dt_prev = self.timestamps_fitted[self.action_chunk_index] - self.timestamps_fitted[self.action_chunk_index - 1]
                    currt_acc_poly = (currt_vel_full - prev_vel) / dt_prev if dt_prev > 0 else np.zeros_like(currt_vel_full)
                else:
                    currt_acc_poly = np.zeros_like(currt_vel_full)

            if inter_chunk_mode == 'search_action':
                candidate_action_chunk = None
                candidate_action_chunk = copy.deepcopy(action_chunk_fitted[:, target_chunk_index:target_chunk_index + search_length])
                currt_action = currt_action_full
                currt_vel = currt_vel_full
                index_offset = self.inter_chunk_fusion.search_smooth_action(currt_action, currt_vel, candidate_action_chunk, search_length)
                target_chunk_index += index_offset
            elif inter_chunk_mode == 'poly':
                # can NOT use with search_action at the same time
                currt_action = currt_action_full
                currt_vel = currt_vel_full
                action_chunk_fitted = self.inter_chunk_fusion.poly_chunk_transition(
                    action_chunk_fitted,
                    vel_chunk_fitted,
                    timestamps_fitted,
                    target_chunk_index,
                    currt_action_full,
                    currt_vel_full,
                    currt_acc_poly,
                    joint_indices=joint_indices,
                )
            elif inter_chunk_mode == 'smooth_velocity':
                currt_action = currt_action_full[joint_indices]
                currt_vel = currt_vel_full[joint_indices]
                currt_acc = currt_acc_full[joint_indices]
                target_action_segment = action_chunk_fitted[joint_indices, target_chunk_index:].copy()
                delat_t = timestamps_fitted[1]
                # sim_action, sim_vel, sim_acc = self._smooth_velocity_transition(target_action_segment, currt_action, currt_vel, currt_acc, delat_t)
                sim_action, sim_vel, sim_acc = _smooth_velocity_transition_numba(target_action_segment, currt_action, currt_vel, currt_acc, delat_t)
                action_chunk_fitted[joint_indices, target_chunk_index:] = sim_action
                # vel_chunk_fitted[joint_indices, target_chunk_index:] = sim_vel
                # acc_chunk_fitted[joint_indices, target_chunk_index:] = sim_acc 
            elif inter_chunk_mode == 'min_jerk':
                currt_action = currt_action_full
                currt_vel = currt_vel_full
                action_chunk_fitted = self.inter_chunk_fusion.min_jerk_chunk_transition(
                    action_chunk_fitted,
                    vel_chunk_fitted,
                    acc_chunk_fitted,
                    timestamps_fitted,
                    target_chunk_index,
                    currt_action_full,
                    currt_vel_full,
                    currt_acc_full,
                    joint_indices=joint_indices,
                )
            elif inter_chunk_mode == 'bspline':
                currt_action = currt_action_full
                currt_vel = currt_vel_full
                action_chunk_fitted = self.inter_chunk_fusion.bspline_chunk_transition(
                    action_chunk_fitted,
                    vel_chunk_fitted,
                    timestamps_fitted,
                    target_chunk_index,
                    currt_action_full,
                    currt_vel_full,
                )
            else:
                pass
            
            # # calculate velocity and acceleration in a unified format
            action_future = action_chunk_fitted[joint_indices, target_chunk_index:].copy()
            action_future_1 = np.concatenate((currt_action_full[joint_indices, None], action_future[:, :-1]), axis=1)
            vel_future = (action_future - action_future_1) / timestamps_fitted[1]
            
            vel_future_1 = np.concatenate((currt_vel_full[joint_indices, None], vel_future[:, :-1]), axis=1)
            acc_future = (vel_future - vel_future_1) / timestamps_fitted[1]

            # # Update velocity and acceleration sequences
            vel_chunk_fitted[joint_indices, target_chunk_index:] = vel_future
            acc_chunk_fitted[joint_indices, target_chunk_index:] = acc_future 

            # weighted smoothing
            if smooth_action:
                if currt_action is None:
                    with self.polynomial_thread_lock:
                        currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                smooth_length = min(smooth_length, len(timestamps_fitted) - target_chunk_index)
                for index in range(smooth_length):
                    ratio = (1 - smooth_base) * math.pow(index / smooth_length, smooth_ratio)
                    action_chunk_fitted[joint_indices, target_chunk_index + index] = (smooth_base + ratio) * action_chunk_fitted[joint_indices, target_chunk_index + index] + (1 - smooth_base - ratio) * currt_action_full[joint_indices]
                    
            with self.polynomial_thread_lock:
                self.action_chunk_index = target_chunk_index
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
                self.acc_chunk_fitted = acc_chunk_fitted
                self.timestamps_fitted = timestamps_fitted
                self.prob_progress = prob_progress
                # Apply gripper offset to compensate for gripper response delay
                if step_indices:
                    if gripper_offset > 0:
                        self.action_chunk_fitted[step_indices, :-gripper_offset] = action_chunk_fitted[step_indices, gripper_offset:]
                    else:
                        chunk_length = self.action_chunk_fitted.shape[-1]
                        self.action_chunk_fitted[step_indices, -gripper_offset:] = action_chunk_fitted[step_indices, :chunk_length + gripper_offset]

    def _poly_chunk_transition(self, new_action_chunk, new_vel_chunk, new_timestamps, target_index, current_index):
        """Smooth transition across action chunks, ensuring continuity of position, velocity, and acceleration.
        
        Args:
            new_action_chunk (np.array): The new action chunk.
            new_vel_chunk (np.array): The new velocity chunk.
            new_timestamps (np.array): The new timestamps.
            target_index (int): The target starting index.
            
        Returns:
            np.array: The action chunk after smooth transition.
        """
        # sleep_time=0.05: target_index=35, current_index=72
        if self.action_chunk_fitted is None or self.vel_chunk_fitted is None:
            return new_action_chunk
            
        with self.polynomial_thread_lock:
            current_pos = self.action_chunk_fitted[:, self.action_chunk_index]
            current_vel = self.vel_chunk_fitted[:, self.action_chunk_index]
            
        # compute current time point acceleration
        if self.action_chunk_index > 0:
            prev_vel = self.vel_chunk_fitted[:, self.action_chunk_index - 1]
            dt = self.timestamps_fitted[self.action_chunk_index] - self.timestamps_fitted[self.action_chunk_index - 1]
            current_acc = (current_vel - prev_vel) / dt if dt > 0 else np.zeros_like(current_vel)
        else:
            current_acc = np.zeros_like(current_vel)
        
        # get new trajectory status at target index
        new_pos = new_action_chunk[:, target_index]
        new_vel = new_vel_chunk[:, target_index]
        
        # compute new trajectory acceleration
        if target_index < new_vel_chunk.shape[1] - 1:
            next_vel = new_vel_chunk[:, target_index + 1]
            dt = new_timestamps[target_index + 1] - new_timestamps[target_index]
            new_acc = (next_vel - new_vel) / dt if dt > 0 else np.zeros_like(new_vel)
        else:
            new_acc = np.zeros_like(new_vel)
            
        # use quintic polynomial to smooth transition, ensuring position, velocity, and acceleration continuity
        transition_length = min(new_action_chunk.shape[1] // 2, new_action_chunk.shape[1] - target_index)
        # transition_length = new_action_chunk.shape[1] // 2
        # transition_length = current_index * 2
        # speed_diff = np.linalg.norm(current_vel - new_vel)
        # transition_length = min(max(50, int(speed_diff * 10)), 300)
        # print(f"transition_length: {transition_length}, {speed_diff}, new_action_chunk.shape: {new_action_chunk.shape}, {target_index}, {current_index}")
        
        if transition_length <= 1:
            return new_action_chunk
            
        # compute smooth transition trajectory for each joint
        smoothed_chunk = new_action_chunk.copy()
        end_index = target_index + transition_length - 1
        joint_indices = self._get_joint_indices(new_action_chunk)
        for joint_idx in joint_indices:
            # boundary conditions: starting point position, velocity, acceleration
            p0, v0, a0 = current_pos[joint_idx], current_vel[joint_idx], current_acc[joint_idx]
            # endpoint position, velocity, acceleration
            pf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index]
            af = new_acc[joint_idx] if end_index < len(new_acc) else 0.0
            
            # normalize transition time to [0,1]
            t_transition = np.linspace(0, 1, transition_length)
            
            # quintic polynomial coefficients calculation (ensure position, velocity, and acceleration continuity)
            # p(t) = a0 + a1*t + a2*t^2 + a3*t^3 + a4*t^4 + a5*t^5
            # boundary conditions: p(0)=p0, p'(0)=v0, p''(0)=a0, p(1)=pf, p'(1)=vf, p''(1)=af
            
            A = np.array([
                [1, 0, 0, 0, 0, 0],      # p(0) = p0
                [0, 1, 0, 0, 0, 0],      # p'(0) = v0  
                [0, 0, 2, 0, 0, 0],      # p''(0) = a0
                [1, 1, 1, 1, 1, 1],      # p(1) = pf
                [0, 1, 2, 3, 4, 5],      # p'(1) = vf
                [0, 0, 2, 6, 12, 20]     # p''(1) = af
            ])
            
            b = np.array([p0, v0, a0, pf, vf, af])
            
            try:
                coeffs = np.linalg.solve(A, b)
                
                # compute transition segment trajectory
                for i, t in enumerate(t_transition):
                    smoothed_pos = (coeffs[0] + coeffs[1]*t + coeffs[2]*t**2 + 
                                  coeffs[3]*t**3 + coeffs[4]*t**4 + coeffs[5]*t**5)
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos
                    
            except np.linalg.LinAlgError:
                # if matrix is singular, use cubic interpolation instead, no acceleration transition
                print(f"Singular matrix for joint {joint_idx}, using cubic interpolation")
                for i, t in enumerate(t_transition):
                    # cubic Hermite interpolation
                    h00 = 2*t**3 - 3*t**2 + 1
                    h10 = t**3 - 2*t**2 + t  
                    h01 = -2*t**3 + 3*t**2
                    h11 = t**3 - t**2
                    
                    smoothed_pos = h00*p0 + h10*v0 + h01*pf + h11*vf
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos
        
        return smoothed_chunk

    def _min_jerk_chunk_transition(self, new_action_chunk, new_vel_chunk, new_acc_chunk, new_timestamps, target_index, current_index):
        """Minimum jerk trajectory minimizes the integral of jerk (time derivative of acceleration) over the entire trajectory:
            J = ∫ (d³x/dt³)² dt
        For boundary conditions [x0, v0, a0] → [xf, vf, af], the minimum jerk trajectory solution is a quintic polynomial:
            x(t) = a0 + a1*t + a2*t² + a3*t³ + a4*t⁴ + a5*t⁵
        
        Compared to ordinary quintic polynomials, the minimum jerk version uses a closed-form solution (Flash & Hogan, 1985).
        
        Args:
            new_action_chunk: New action trajectory [dof, T]
            new_vel_chunk: New velocity trajectory [dof, T]  
            new_acc_chunk: New acceleration trajectory [dof, T]
            new_timestamps: Timestamp sequence
            target_index: Target starting index of new trajectory
            current_index: Current trajectory index
            
        Returns:
            np.array: Smoothly transitioned action trajectory
        """
        if self.action_chunk_fitted is None or self.vel_chunk_fitted is None:
            return new_action_chunk
            
        with self.polynomial_thread_lock:
            current_pos = self.action_chunk_fitted[:, self.action_chunk_index].copy()
            current_vel = self.vel_chunk_fitted[:, self.action_chunk_index].copy()
            current_acc = self.acc_chunk_fitted[:, self.action_chunk_index].copy() if self.acc_chunk_fitted is not None else np.zeros_like(current_vel)
        
        # Get target state
        target_pos = new_action_chunk[:, target_index].copy()
        target_vel = new_vel_chunk[:, target_index].copy()
        target_acc = new_acc_chunk[:, target_index].copy() if new_acc_chunk is not None else np.zeros_like(target_vel)
        
        # Adaptive transition length: based on pos/vel/acc difference
        joint_indices = self._get_joint_indices(new_action_chunk)
        pos_diff = np.linalg.norm(current_pos[joint_indices] - target_pos[joint_indices])
        vel_diff = np.linalg.norm(current_vel[joint_indices] - target_vel[joint_indices])
        acc_diff = np.linalg.norm(current_acc[joint_indices] - target_acc[joint_indices])
        
        # Base transition length + pos/vel/acc difference adjustment
        base_transition = new_action_chunk.shape[1] // 2
        adaptive_factor = min(2.0, 0.5 + pos_diff * 2.0 + vel_diff * 1.5 + acc_diff * 0.3)
        transition_length = min(int(base_transition * adaptive_factor), new_action_chunk.shape[1] - target_index)
        # print('\n', base_transition, adaptive_factor, transition_length)
        
        if transition_length <= 1:
            return new_action_chunk
            
        smoothed_chunk = new_action_chunk.copy()
        
        # Calculate transition time
        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005
        T = transition_length * dt  # Total transition time
        
        # End state (end of transition region)
        end_index = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)
        
        for joint_idx in joint_indices:
            # Boundary conditions
            x0 = current_pos[joint_idx]
            v0 = current_vel[joint_idx] * T  # Normalized velocity
            a0 = current_acc[joint_idx] * T * T  # Normalized acceleration
            
            xf = new_action_chunk[joint_idx, end_index]
            vf = new_vel_chunk[joint_idx, end_index] * T if end_index < new_vel_chunk.shape[1] else 0.0
            af = (new_acc_chunk[joint_idx, end_index] * T * T) if (new_acc_chunk is not None and end_index < new_acc_chunk.shape[1]) else 0.0
            
            # Minimum jerk trajectory closed-form solution (Flash & Hogan, 1985)
            for i in range(transition_length):
                tau = i / (transition_length - 1) if transition_length > 1 else 1.0
                tau2 = tau * tau
                tau3 = tau2 * tau
                tau4 = tau3 * tau
                tau5 = tau4 * tau
                
                # Minimum jerk polynomial basis functions
                h0 = 1 - 10*tau3 + 15*tau4 - 6*tau5  # Position basis function for x0
                h1 = tau - 6*tau3 + 8*tau4 - 3*tau5  # Velocity basis function for v0
                h2 = 0.5*tau2 - 1.5*tau3 + 1.5*tau4 - 0.5*tau5  # Acceleration basis function for a0
                h3 = 10*tau3 - 15*tau4 + 6*tau5  # Position basis function for xf
                h4 = -4*tau3 + 7*tau4 - 3*tau5  # Velocity basis function for vf
                h5 = 0.5*tau3 - tau4 + 0.5*tau5  # Acceleration basis function for af
                
                smoothed_pos = h0*x0 + h1*v0 + h2*a0 + h3*xf + h4*vf + h5*af
                
                # Smooth blending with target trajectory (end gradient)
                blend_start = 0.7  # Start blending at 70%
                if tau > blend_start:
                    blend_ratio = (tau - blend_start) / (1.0 - blend_start)
                    target_pos_at_i = new_action_chunk[joint_idx, target_index + i] if (target_index + i) < new_action_chunk.shape[1] else xf
                    smoothed_pos = (1 - blend_ratio) * smoothed_pos + blend_ratio * target_pos_at_i
                
                if target_index + i < smoothed_chunk.shape[1]:
                    smoothed_chunk[joint_idx, target_index + i] = smoothed_pos
        
        return smoothed_chunk

    def _bspline_chunk_transition(self, new_action_chunk, new_vel_chunk, new_timestamps, target_index, current_index, num_control_points=6):
        """B-Spline is a parametric curve defined by control points and basis functions:
            C(t) = Σ Ni,p(t) * Pi
        Where Pi are control points, Ni,p(t) are p-th order B-Spline basis functions.
        
        Args:
            new_action_chunk: New action trajectory
            new_vel_chunk: New velocity trajectory
            new_timestamps: Timestamp sequence
            target_index: Starting index
            current_index: Current index
            num_control_points: Number of control points, more points = more precise but slower
            
        Returns:
            np.array: Smoothly transitioned action trajectory
        """
        from scipy.interpolate import make_interp_spline
        
        if self.action_chunk_fitted is None:
            return new_action_chunk
            
        with self.polynomial_thread_lock:
            current_pos = self.action_chunk_fitted[:, self.action_chunk_index].copy()
            current_vel = self.vel_chunk_fitted[:, self.action_chunk_index].copy()
        
        transition_length = min(new_action_chunk.shape[1] // 3, new_action_chunk.shape[1] - target_index)
        
        if transition_length <= 3:
            return new_action_chunk
            
        smoothed_chunk = new_action_chunk.copy()
        dt = new_timestamps[1] - new_timestamps[0] if len(new_timestamps) > 1 else 0.005
        
        # Sample control point indices
        control_indices = np.linspace(0, transition_length - 1, num_control_points).astype(int)
        
        for joint_idx in range(min(14, new_action_chunk.shape[0])):
            # Build control points
            control_points = []
            control_times = []
            
            # Starting point (current state)
            control_points.append(current_pos[joint_idx])
            control_times.append(0.0)
            
            # Intermediate control points (sampled from target trajectory)
            for i, idx in enumerate(control_indices[1:], 1):
                actual_idx = min(target_index + idx, new_action_chunk.shape[1] - 1)
                control_points.append(new_action_chunk[joint_idx, actual_idx])
                control_times.append(idx * dt)
            
            control_points = np.array(control_points)
            control_times = np.array(control_times)
            
            try:
                # Cubic B-Spline interpolation, boundary conditions use current velocity
                bc_type = ((1, current_vel[joint_idx]), (1, new_vel_chunk[joint_idx, min(target_index + transition_length - 1, new_vel_chunk.shape[1] - 1)]))
                spline = make_interp_spline(control_times, control_points, k=3, bc_type=bc_type)
                
                # Sample in the transition interval
                sample_times = np.linspace(0, control_times[-1], transition_length)
                smoothed_positions = spline(sample_times)
                
                for i in range(transition_length):
                    if target_index + i < smoothed_chunk.shape[1]:
                        smoothed_chunk[joint_idx, target_index + i] = smoothed_positions[i]
                        
            except Exception as e:
                # Fall back to linear interpolation when B-Spline fails
                self.logger.warning(f"B-Spline failed for joint {joint_idx}: {e}, using linear interpolation")
                for i in range(transition_length):
                    t = i / (transition_length - 1) if transition_length > 1 else 1.0
                    target_idx = min(target_index + transition_length - 1, new_action_chunk.shape[1] - 1)
                    if target_index + i < smoothed_chunk.shape[1]:
                        smoothed_chunk[joint_idx, target_index + i] = (1 - t) * current_pos[joint_idx] + t * new_action_chunk[joint_idx, target_idx]
        
        return smoothed_chunk

    def _search_smooth_action(self, currt_action, currt_vel, candidate_action_chunk, search_length):
        """Search for the best action index to ensure smooth transition.
        
        Args:
            currt_action (np.array): Current action values.
            currt_vel (np.array): Current velocity values.
            candidate_action_chunk (np.array): Candidate action chunk to search from.
            search_length (int): Length of search range.
            
        Returns:
            int: Target index for smooth action transition.
        """
        valid_joints = [index for index, value in enumerate(abs(currt_vel) > 5e-3) if value]
        currt_action = currt_action[valid_joints]
        currt_vel = currt_vel[valid_joints]
        target_index = 0
        valid_joint_num = len(valid_joints)
        qualified_joint_num = 0
        
        for candidate_index in range(0, search_length, 5):
            # add boundary check, ensure candidate_index not out of range
            if candidate_index >= candidate_action_chunk.shape[1]:
                break
            candidate_action = candidate_action_chunk[valid_joints, candidate_index]
            action_diff = candidate_action - currt_action
            qualified_count = 0
            
            for index in range(valid_joint_num):
                # Skip gripper joints (v = 0.0) and stationary joints (very small velocity)
                if action_diff[index] * currt_vel[index] > 0.0:
                    qualified_count += 1
                    
            if qualified_count == valid_joint_num:
                target_index = candidate_index
                qualified_joint_num = qualified_count
                break
            else:
                if qualified_count > qualified_joint_num:
                    target_index = candidate_index
                    qualified_joint_num = qualified_count
                    
        self.logger.debug(f'target_index: {target_index}, qualified dim: {qualified_joint_num}')
        return target_index

    def get_action_fitted(self):
        """Get the current action (fitted and raw) indexed by action_chunk_index.

        Returns:
            np.array: The current action.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return None, None, None, None
            self.action_chunk_index = min(self.action_chunk_index + 1, self.action_chunk_fitted.shape[1] - 1)
            # print(self.action_chunk_fitted.shape, len(self.action_chunks), self.action_chunks[0].shape, "!"*50)
            action_raw_index = int(self.action_chunk_index/(self.action_chunk_fitted.shape[1]/len(self.action_chunks)))
            action_raw_index = min(action_raw_index, len(self.action_chunks)-1)
            # print(action_raw_index)
            action_raw = self.action_chunks[action_raw_index]
            action_fitted = self.action_chunk_fitted[:, self.action_chunk_index]
            vel_fitted = self.vel_chunk_fitted[:, self.action_chunk_index]
            acc_fitted = self.acc_chunk_fitted[:, self.action_chunk_index]
            return action_fitted, action_raw, vel_fitted, acc_fitted
    
    def get_prob_progress(self):
        """Get the current prob_progress value indexed by action_chunk_index.

        Returns:
            float: The current prob_progress value, or None if not available.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None or self.prob_progress is None:
                return None
            # Ensure index is within bounds
            index = min(self.action_chunk_index, len(self.prob_progress) - 1)
            return self.prob_progress[index]
    
    def getActionChunk(self):
        """Get a copy of the current action chunks.
        
        This method is deprecated and should not be used in new code.
        
        Returns:
            list: Copy of action chunks.
        """
        with self.action_thread_lock:
            return copy.copy(self.action_chunks)
    
    def pop_observe_data(self, num_samples = 1):
        """Pop the latest observe data from the buffer.

        Args:
            num_samples (int, optional): The number of data frames to pop. Defaults to 1. If num_samples is greater than 1, a list of data frames will be returned.

        Returns:
            dict | list: The observe data frame. None if the buffer is empty.
        """
        with self.observe_thread_lock:
            if len(self.observe_buffer) >= num_samples:
                data = self.observe_buffer.pop() if num_samples == 1 else [self.observe_buffer.pop() for _ in range(num_samples)]
                return data
            else:
                return None
    
    def read_observe_data(self):
        """Read the latest observe data from the buffer.
        """
        with self.observe_thread_lock:
            if len(self.observe_buffer) > 0:
                data = self.observe_buffer[-1]
                return data
            else:
                return None
    
    def pop_observe_data_left(self):
        """Pop the left most observe data from the buffer.

        Returns:
            dict: The observe data frame. None if the buffer is empty.
        """
        if self.observe_buffer:
            return self.observe_buffer.popleft()
        else:
            return None
    
    def clear_action_data(self):
        """Clear all action-related data to ensure fresh action retrieval.
        
        This method resets action chunks, fitted trajectories, and related indices
        to ensure that subsequent get_action_fitted() calls return the most recent actions.
        """
        with self.action_thread_lock:
            self.action_chunks = []
            self.timestamp_chunks = []
        
        with self.polynomial_thread_lock:
            self.observe_buffer.clear()
            self.action_chunk_fitted = None
            self.vel_chunk_fitted = None
            self.acc_chunk_fitted = None
            self.timestamps_fitted = None
            self.action_chunk_index = None
            
        self.logger.debug("Action data cleared for fresh inference")
