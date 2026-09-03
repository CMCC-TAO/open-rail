import time
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
        self.observe_buffer = deque(maxlen=max(10, rdm_config.max_len))
        self.observe_add_timestamps = deque(maxlen=max(2, rdm_config.observe_fps_window_size))
        self.observe_fps = 0.0
        self.action_chunks = []
        self.timestamp_chunks = []
        self.action_thread_lock = threading.Lock()
        self.observe_thread_lock = threading.Lock()
        self.polynomial_thread_lock = threading.Lock()
        # Condition variable to wait/notify on polynomial/action index updates
        self.polynomial_cond = threading.Condition(self.polynomial_thread_lock)
        
        # Timestamp of the first observe data for inference
        self.init_observe_timestamp = None
        self.frame_count = 0
        self.action_chunk_fitted = None
        self.vel_chunk_fitted = None
        self.acc_chunk_fitted = None
        self.timestamps_fitted = None
        self.action_chunk_index = None
        self.prob_progress = None

        # Timing markers for inference, trajectory fitting and control
        self.start_infer_marker = 0.0
        self.start_intra_traj_marker = 0.0
        self.start_inter_traj_marker = 0.0
        self.start_ctrl_marker = 0.0
        self.avg_comm_infer_time = 0.0
        self.avg_intra_traj_time = 0.0
        self.avg_inter_traj_time = 0.0
        self.avg_infer_time = 0.0
        self.avg_comm_time = 0.0 # communication latency between vla_client and vla_server
        self.infer_count = 0

        # Synchronous Running Flag
        self.mode = 'control'

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
        
    def set_intra_traj_time_marker(self):
        """Set the local timestamp when start intra chunk process. Used for calculating the trajectory fitting time.
        """
        self.start_intra_traj_marker = time.perf_counter()
        # print(f"Start intra chunk process at {self.start_intra_traj_marker:.4f} s")
        
    def set_inter_traj_time_marker(self):
        """Set the local timestamp when start inter chunk process. Used for calculating the inter chunk fusion time.
        """
        self.start_inter_traj_marker = time.perf_counter()
        # print(f"Start inter chunk process at {self.start_inter_traj_marker:.4f} s")
    def set_control_time_marker(self):
        """Set the local timestamp when start control. Used for calculating the control time.
        """
        self.start_ctrl_marker = time.perf_counter()
    
    def compute_avg_comm_infer_time(self):
        """Compute the average inference time. The average inference time is used to set the offset of the action chunk.
        """
        # self.last_infer_time = self.currt_infer_time
        currt_comm_infer_time = self.start_intra_traj_marker - self.start_infer_marker
        # self.avg_comm_infer_time = (self.avg_comm_infer_time * (self.infer_count - 1) + currt_infer_time) / self.infer_count if self.infer_count > 0 else currt_infer_time
        self.avg_comm_infer_time = self.avg_comm_infer_time * 0.8 + currt_comm_infer_time * 0.2 if self.avg_comm_infer_time > 0 else currt_comm_infer_time
        self.logger.debug(f'avg communication and inference time: {self.avg_comm_infer_time:.4f}s')
        # print(f"avg infer time: {self.avg_comm_infer_time}, infer count: {self.infer_count}")
    
    def compute_avg_comm_time(self, avg_infer_time):
        """Compute the average communication time between vla_client and vla_server.

        Args:
            avg_infer_time (float): The average inference time return from vla_server
        """
        self.avg_infer_time = self.avg_infer_time * 0.8 + avg_infer_time * 0.2 if self.avg_infer_time > 0.0 else avg_infer_time
        self.avg_comm_time = self.avg_comm_infer_time - avg_infer_time

    def compute_avg_intra_traj_time(self):
        """Compute the average intra chunk process time. The average trajectory fitting time is used to set the offset of the action chunk.
        """
        # self.last_traj_time = self.currt_traj_time
        currt_intra_traj_time = self.start_inter_traj_marker - self.start_intra_traj_marker
        # self.avg_intra_traj_time = (self.avg_intra_traj_time * (self.infer_count - 1) + currt_intra_traj_time) / self.infer_count if self.infer_count > 0 else currt_intra_traj_time
        self.avg_intra_traj_time = self.avg_intra_traj_time * 0.8 + currt_intra_traj_time * 0.2 if self.avg_intra_traj_time > 0 else currt_intra_traj_time
        self.logger.debug(f'avg intra traj time: {self.avg_intra_traj_time:.4f}s')
        # self.logger.debug(f'avg traj time: {self.avg_intra_traj_time}')
    def compute_avg_inter_traj_time(self):
        """Compute the average trajectory fitting time. The average trajectory fitting time is used to set the offset of the action chunk.
        """
        # self.last_traj_time = self.currt_traj_time
        currt_inter_traj_time = self.start_ctrl_marker - self.start_inter_traj_marker
        # self.avg_inter_traj_time = (self.avg_intra_traj_time * (self.infer_count - 1) + currt_inter_traj_time) / self.infer_count if self.infer_count > 0 else currt_inter_traj_time
        self.avg_inter_traj_time = self.avg_intra_traj_time * 0.8 + currt_inter_traj_time * 0.2 if self.avg_inter_traj_time > 0 else currt_inter_traj_time
        self.logger.debug(f'avg inter traj time: {self.avg_inter_traj_time:.4f}s')
 
    def add_observe_data(self, frame):
        """Add observe data to buffer. The observe data is a dictionary containing the robot state, camera images and timestamps.

        Args:
            frame (dict): The observe data frame. The keys of the dictionary are 'robot_state', 'camera_images' and 'timestamps'.
        """
        self.frame_count += 1
        # Skip the first few frames as they may be unstable
        if self.frame_count > 5:
            now = time.perf_counter()
            with self.observe_thread_lock:
                self.observe_buffer.append(frame)
            self.observe_add_timestamps.append(now)
            if len(self.observe_add_timestamps) >= 2:
                duration = self.observe_add_timestamps[-1] - self.observe_add_timestamps[0]
                if duration > 1e-6:
                    observe_fps_tmp = (len(self.observe_add_timestamps) - 1) / duration
                    self.observe_fps = observe_fps_tmp * 0.8 + self.observe_fps * 0.2 if self.observe_fps > 0 else observe_fps_tmp

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

    def pop_action_chunk(self, time_offset = 0.0):
        """Returns the action chunk and timestamp chunk with the given time offset and number of samples for trajectory fitting.

        Args:
            time_offset (float, optional): The action data is discarded if its timestamp is smaller the time offset. Defaults to 0.0.

        Returns:
            np.array: The timestamp chunks in numpy array format.
            np.array: The action chunks in numpy array format.
        """
        # TODO: compute current time according to the infer time
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
            self.logger.error("No valid data in action chunk, please check time_offset.")
            return None, None
        
        # Data fitting needs to look back a few frames to prevent non-smooth fitting results
        start_index = max(0, valid_index-1)
        end_index = len(self.action_chunks)
        # end_index = min(len(self.action_chunks), start_index + num_samples)
        
        timestamp_chunks_np = np.array(self.timestamp_chunks[start_index:end_index])
        action_chunks_np = np.array(action_chunk_2_joint_chunk(self.action_chunks[start_index:end_index]))
        return timestamp_chunks_np, action_chunks_np

    @staticmethod
    def _apply_gripper_offset(action_chunk, step_indices, gripper_offset):
        source = np.asarray(action_chunk)
        if source.ndim != 2:
            raise ValueError(f'action_chunk must be 2D, got shape {source.shape}')
        shifted = source.copy()
        offset = int(gripper_offset)
        indices = [] if step_indices is None else list(step_indices)
        chunk_length = shifted.shape[1]
        if not indices or offset == 0 or abs(offset) >= chunk_length:
            return shifted
        if offset > 0:
            shifted[indices, :-offset] = source[indices, offset:]
        else:
            shifted[indices, -offset:] = source[indices, :chunk_length + offset]
        return shifted

    def update_action_chunk_fitted(self,
                                action_chunk_smoothed,
                                vel_chunk_smoothed,
                                acc_chunk_smoothed,
                                timestamps_smoothed,
                                target_chunk_index,
                                prob_progress=None,
                                step_indices=None,
                                gripper_offset=0):
        """Update action chunk with the new fitted action chunk.

        Args:
            action_chunk_smoothed (np.array): Smoothed action chunk to update.
            vel_chunk_smoothed (np.array): Smoothed velocity chunk to update.
            acc_chunk_smoothed (np.array): Smoothed accelerated velocity chunk to update.
            timestamps_smoothed ()
            target_chunk_index
            prob_progress (np.array, optional): Array of prob_progress values aligned with action chunk. Defaults to None.
            step_indices (list[int], optional): Stepwise action dimensions.
            gripper_offset (int): Frames to shift stepwise commands forward/backward.
        """
        action_chunk_smoothed = self._apply_gripper_offset(
            action_chunk_smoothed, step_indices, gripper_offset
        )
        with self.polynomial_thread_lock:
            self.action_chunk_index = target_chunk_index if self.action_chunk_index is not None else 0
            self.action_chunk_fitted = action_chunk_smoothed
            self.vel_chunk_fitted = vel_chunk_smoothed
            self.acc_chunk_fitted = acc_chunk_smoothed
            self.timestamps_fitted = timestamps_smoothed
            self.prob_progress = prob_progress
            # notify waiters about the updated fitted chunk
            self.polynomial_cond.notify_all()

    def get_start_chunk_index(self, next_timestamps):
        start_chunk_index = 0
        time_offset = self.start_ctrl_marker - self.observe_marker
        self.logger.debug(f'total inference time: {time_offset:.3f}s')
        
        for index in range(len(next_timestamps)):
            if next_timestamps[index] > time_offset:
                start_chunk_index = index
                break
        return start_chunk_index

    def get_current_state(self):
        # TODO: Consider the inter chunk fusion time offset
        with self.polynomial_thread_lock:
            currt_act = self.action_chunk_fitted[:, self.action_chunk_index].copy() if self.action_chunk_fitted is not None else None
            currt_vel = self.vel_chunk_fitted[:, self.action_chunk_index].copy() if self.vel_chunk_fitted is not None else None
            currt_acc = self.acc_chunk_fitted[:, self.action_chunk_index].copy() if self.acc_chunk_fitted is not None else None
        return currt_act, currt_vel, currt_acc
    def get_action_fitted(self, mode='control'):
        """Get the current action (fitted and raw) indexed by action_chunk_index.

        Returns:
            np.array: The current action.
        """
        with self.polynomial_thread_lock:
            if self.action_chunk_index is None:
                return None, None, None, None
            if len(self.action_chunks) == 0:
                return None, None, None, None
            if self.action_chunk_fitted.shape[1] == 0:
                return None, None, None, None
            if self.mode != 'control' and mode == 'control':
                # print(f"Switching to control mode, current action_chunk_index={self.action_chunk_index}, reset action_chunk_index to 0.")
                self.action_chunk_index = 0
            self.mode = mode
            self.action_chunk_index = min(self.action_chunk_index + 1, self.action_chunk_fitted.shape[1] - 1)
            # notify any waiter that the action index advanced
            self.polynomial_cond.notify_all()
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
                # print(f"Debug: return task progress when none.")
                return 0
            # Ensure index is within bounds
            index = min(self.action_chunk_index, len(self.prob_progress) - 1)
            return self.prob_progress[index]
    
    def pop_observe_data(self, num_samples = 1):
        """Pop the latest observe data from the buffer.

        Args:
            num_samples (int, optional): The number of data frames to pop. Defaults to 1. If num_samples is greater than 1, a list of data frames will be returned.

        Returns:
            dict | list: The observe data frame. None if the buffer is empty.
        """
        data = None
        with self.observe_thread_lock:
            if len(self.observe_buffer) >= num_samples:
                data = self.observe_buffer.pop() if num_samples == 1 else [self.observe_buffer.pop() for _ in range(num_samples)]
        return data
    
    def clear(self):
        """Clear all action-related data to ensure fresh action retrieval.
        
        This method resets action chunks, fitted trajectories, and related indices
        to ensure that subsequent get_action_fitted() calls return the most recent actions.
        """
        with self.action_thread_lock:
            self.action_chunks = []
            self.timestamp_chunks = []
            self.infer_count = 0
            self.start_infer_marker = 0.0
            self.start_intra_traj_marker = 0.0
            self.start_inter_traj_marker = 0.0
            self.start_ctrl_marker = 0.0
            self.avg_infer_time = 0.0
            self.avg_comm_time = 0.0
            self.avg_intra_traj_time = 0.0
            self.avg_inter_traj_time = 0.0

        with self.observe_thread_lock:
            self.observe_buffer.clear()
            self.observe_add_timestamps.clear()
            self.observe_fps = 0.0
        
        with self.polynomial_thread_lock:
            self.action_chunk_fitted = None
            self.vel_chunk_fitted = None
            self.acc_chunk_fitted = None
            self.timestamps_fitted = None
            self.action_chunk_index = None
            self.prob_progress = None
            # notify waiters that action data has been cleared
            self.polynomial_cond.notify_all()
            
        self.logger.debug("All data cleared for fresh inference")
    @property
    def runtime_status(self):
        return {
            "infer_count": self.infer_count,
            "avg_infer_time": self.avg_infer_time,
            "avg_comm_time": self.avg_comm_time,
            "avg_intra_traj_time": self.avg_intra_traj_time,
            "avg_inter_traj_time": self.avg_inter_traj_time,
            "obv_fps": self.observe_fps
        }
    def wait_for_next(self, mode: str = 'sync', wait_time: float = 0.01) -> bool:
        """Wait for next action/frame according to mode.

        Args:
            mode (str): 'async' -> sleep for `wait_time`; 'sync' -> block until the fitted
                        action chunk index reaches the last available index.
            wait_time (float): Sleep time for async mode (seconds).

        Returns:
            bool: True if the wait condition was satisfied (or sleep completed). False if
                  there was no fitted action chunk to wait on.
        """
        # start_time = time.perf_counter()
        result = False
        if mode == 'async':
            time.sleep(wait_time)
            result = True
        elif mode == 'sync':
            with self.polynomial_cond:
                if self.action_chunk_fitted is None:
                    result = False
                else:
                    target_index = max(0, self.action_chunk_fitted.shape[1] - 1)
                    self.polynomial_cond.wait_for(
                        lambda: (self.action_chunk_index is not None
                                 and self.action_chunk_fitted is not None
                                 and self.action_chunk_index >= target_index)
                    )
                    result = True
        else:
            raise ValueError("mode must be 'async' or 'sync'")

        # actual_wait_time = (time.perf_counter() - start_time) * 1000.0
        # self.logger.debug(f"mode={mode}, real_wait_time={actual_wait_time:.3f} ms.")
        return result
