import copy
import time
import math
import threading
import numpy as np
import logging
import matplotlib.pyplot as plt
from collections import deque
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from client.utils.util import run_time_decorator, action_chunk_2_joint_chunk, get_closest_index, get_action_layout_info
from client.core.inter_chunk_fusion import InterChunkFusion


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
        # print(f"Start inference at {self.start_infer_marker:.4f} s")
        
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
                sim_action, sim_vel, sim_acc = self.inter_chunk_fusion.smooth_velocity_transition_numba(target_action_segment, currt_action, currt_vel, currt_acc, delat_t)
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
