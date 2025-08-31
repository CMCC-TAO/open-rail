import copy
import time
import math
import threading
import numpy as np
import logging
from collections import deque
from ml_collections import ConfigDict
from client.utils.util import run_time_decorator, action_chunk_2_joint_chunk, get_closest_index

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
        self.timestamps_fitted = None
        self.action_chunk_index = None
        self.prob_progress = None

        # For visualization purposes
        self.action_chunk_last = None
        self.timestamp_last = None
        self.isDraw = False

        # Timing markers for inference, trajectory fitting and control
        self.start_infer_marker = None
        self.start_traj_marker = None
        self.start_ctrl_marker = None
        self.avg_infer_time = 0.0
        self.avg_traj_time = 0.0
        self.infer_count = 0

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
        
    def set_traj_time_marker(self):
        """Set the local timestamp when start trajectory fitting. Used for calculating the trajectory fitting time.
        """
        self.start_traj_marker = time.perf_counter()
        
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

    def compute_avg_traj_time(self):
        """Compute the average trajectory fitting time. The average trajectory fitting time is used to set the offset of the action chunk.
        """
        # self.last_traj_time = self.currt_traj_time
        currt_traj_time = self.start_ctrl_marker - self.start_traj_marker
        self.avg_traj_time = (self.avg_traj_time * (self.infer_count - 1) + currt_traj_time) / self.infer_count
        self.logger.debug(f'avg traj time: {self.avg_traj_time}')
    
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
                                timestamps_fitted,
                                prob_progress=None,
                                search_action = False,
                                search_length = 20,
                                smooth_action = False,
                                smooth_length = 20,
                                smooth_base = 0.1,
                                smooth_ratio = 0.5,
                                gripper_offset = 25):
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
        if self.action_chunk_index is None:
            with self.polynomial_thread_lock:
                self.action_chunk_index = 0
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
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
            if search_action:
                candidate_action_chunk = None
                candidate_action_chunk = copy.deepcopy(action_chunk_fitted[:, target_chunk_index:target_chunk_index + search_length])
                with self.polynomial_thread_lock:
                    currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                    currt_vel = self.vel_chunk_fitted[:, self.action_chunk_index]
                index_offset = self._search_smooth_action(currt_action, currt_vel, candidate_action_chunk, search_length)
                target_chunk_index += index_offset

            if smooth_action:
                if currt_action is None:
                    with self.polynomial_thread_lock:
                        currt_action = self.action_chunk_fitted[:, self.action_chunk_index]
                smooth_length = min(smooth_length, len(timestamps_fitted) - target_chunk_index)
                for index in range(smooth_length):
                    ratio = (1 - smooth_base) * math.pow(index / smooth_length, smooth_ratio)
                    action_chunk_fitted[:14, target_chunk_index + index] = (smooth_base + ratio) * action_chunk_fitted[:14, target_chunk_index + index] + (1 - smooth_base - ratio) * currt_action[:14]
                
            with self.polynomial_thread_lock:
                self.action_chunk_index = target_chunk_index
                self.action_chunk_fitted = action_chunk_fitted
                self.vel_chunk_fitted = vel_chunk_fitted
                self.timestamps_fitted = timestamps_fitted
                self.prob_progress = prob_progress
                # Apply gripper offset to compensate for gripper response delay
                self.action_chunk_fitted[14:, :-gripper_offset] = action_chunk_fitted[14:, gripper_offset:]

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

    def smoothActionTrajOLD(self, currt_action, currt_vel, candidate_action_chunk, max_acc, smooth_length=15):
        action_dim = len(currt_action)
        max_accs = np.array([max_acc] * len(currt_action))
        period = 0.005
        
        for index in range(smooth_length):
            candidate_action = candidate_action_chunk[:, index]
            action_diff = candidate_action - currt_action
            acc_flag = np.array([1.0 if joint_diff > 0.0 else -1.0 for joint_diff in action_diff])
            next_max_vel = currt_vel + acc_flag * max_accs * period
            next_max_action = currt_action + currt_vel * period + 0.5 * acc_flag * max_accs * period * period
            
            for joint_index in range(action_dim):
                if acc_flag[joint_index] == 1.0:
                    if candidate_action[joint_index] > next_max_action[joint_index]:
                        candidate_action[joint_index] = next_max_action[joint_index]
                        currt_vel[joint_index] = next_max_vel[joint_index]
                    else:
                        currt_vel[joint_index] = (candidate_action[joint_index] - currt_action[joint_index]) / period
                elif acc_flag[joint_index] == -1.0:
                    if candidate_action[joint_index] < next_max_action[joint_index]:
                        candidate_action[joint_index] = next_max_action[joint_index]
                        currt_vel[joint_index] = next_max_vel[joint_index]
                    else:
                        currt_vel[joint_index] = (candidate_action[joint_index] - currt_action[joint_index]) / period
                        
            currt_action = candidate_action
        return candidate_action_chunk
    
    def get_action_fitted(self):
        """Get the current action indexed by action_chunk_index.

        Returns:
            np.array: The current action.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return None
            self.action_chunk_index = min(self.action_chunk_index + 1, self.action_chunk_fitted.shape[1] - 1)
            return self.action_chunk_fitted[:, self.action_chunk_index]
    
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
            self.action_chunk_fitted = None
            self.vel_chunk_fitted = None
            self.timestamps_fitted = None
            self.action_chunk_index = None
            
        self.logger.debug("Action data cleared for fresh inference")
