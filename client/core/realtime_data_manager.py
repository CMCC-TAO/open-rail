import time
import threading
import numpy as np
import logging
from collections import deque
from ml_collections import ConfigDict
from client.utils.util import run_time_decorator, get_closest_index


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
        # Raw actions are stored as [dof, chunk] float32 arrays from receipt.
        self.action_chunks = np.empty((0, 0), dtype=np.float32)
        self.timestamp_chunks = np.empty(0, dtype=np.float32)
        self.raw_action_count = 0
        # ── Locking model ────────────────────────────────────────────────────
        # Two locks, chosen so that each lock boundary matches a data boundary.
        #
        # observe_thread_lock
        #   Guards : observe_buffer, observe_add_timestamps, observe_fps,
        #            frame_count
        #   Writer : process_observe thread (~30 Hz)
        #   Reader : inference thread        (~30 Hz)
        #
        # action_lock
        #   Guards : ALL action state -- raw chunks (action_chunks,
        #            timestamp_chunks, raw_action_count), fitted chunks
        #            (action/vel/acc_chunk_fitted, timestamps_fitted),
        #            action_chunk_index, prob_progress, mode, infer_count and
        #            the timing/average markers.
        #   Writer : inference thread (~30 Hz)
        #   Reader : control timer thread (266.7 Hz), inference thread,
        #            api thread (clear()).
        #
        # Action state used to be split across action_thread_lock and
        # polynomial_thread_lock, but update_action_chunk_raw() wrote the raw
        # chunks under the former while get_action_fitted() read them under the
        # latter -- two different locks, i.e. no mutual exclusion at all. All
        # action-related fields now live under a single lock.
        self.action_lock = threading.Lock()
        self.observe_thread_lock = threading.Lock()
        # Condition variable to wait/notify on action index / chunk updates
        self.action_cond = threading.Condition(self.action_lock)
        
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
        # frame_count / observe_add_timestamps / observe_fps are only ever
        # touched by the process_observe thread, but they are kept inside
        # observe_thread_lock anyway: at 30 Hz the cost is negligible, and it
        # keeps the lock contract documented in __init__ honest instead of
        # relying on an implicit single-writer convention that a later edit
        # could silently break.
        with self.observe_thread_lock:
            self.frame_count += 1
            # Skip the first few frames as they may be unstable
            if self.frame_count > 5:
                now = time.perf_counter()
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
        action_array = np.asarray(action_chunk, dtype=np.float32)
        if action_array.ndim != 2:
            raise ValueError(f'action_chunk must be 2D, got shape {action_array.shape}')
        action_array = np.ascontiguousarray(action_array.T)

        timestamp_array = np.array(timestamp_chunk, dtype=np.float32, copy=True)
        if timestamp_array.ndim != 1 or timestamp_array.size != action_array.shape[1]:
            raise ValueError(
                'timestamp_chunk must be 1D with one timestamp per action '
                f'(got shape {timestamp_array.shape}, actions {action_array.shape})'
            )
        if timestamp_array.size == 0:
            raise ValueError('action_chunk must not be empty')

        # Preserve the existing behavior: only the first timestamp is reset;
        # subsequent timestamps remain relative to the original chunk input.
        timestamp_array[0] = 0.0

        # Ensure thread safety when updating action chunks. All three fields are
        # published together under one lock, and get_action_fitted() reads them
        # under the same lock, so it can never observe a mismatched pair.
        with self.action_lock:
            self.action_chunks = action_array
            self.timestamp_chunks = timestamp_array
            self.raw_action_count = action_array.shape[1]

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
        
        if self.raw_action_count == 0:
            self.logger.error("No valid data in action chunk, please check time_offset.")
            return None, None

        # Equivalent to the previous Python loop: find the first timestamp
        # strictly greater than target_time.
        valid_index = int(np.searchsorted(self.timestamp_chunks, target_time, side='right'))
        if valid_index >= self.raw_action_count:
            self.logger.error("No valid data in action chunk, please check time_offset.")
            return None, None
        
        # Data fitting needs to look back a few frames to prevent non-smooth fitting results
        start_index = max(0, valid_index-1)
        end_index = self.raw_action_count
        # end_index = min(len(self.action_chunks), start_index + num_samples)
        
        return (
            self.timestamp_chunks[start_index:end_index],
            self.action_chunks[:, start_index:end_index],
        )

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
        with self.action_lock:
            self.action_chunk_index = target_chunk_index if self.action_chunk_index is not None else 0
            self.action_chunk_fitted = action_chunk_smoothed
            self.vel_chunk_fitted = vel_chunk_smoothed
            self.acc_chunk_fitted = acc_chunk_smoothed
            self.timestamps_fitted = timestamps_smoothed
            self.prob_progress = prob_progress
            # Publishing a new chunk resets action_chunk_index below the last
            # column, so it can never satisfy wait_for_next()'s predicate by
            # itself -- but a waiter may be blocked on the *previous* chunk's
            # predicate and must re-evaluate against the new one.
            self.action_cond.notify_all()

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
        # Grab references under the lock, copy outside it. The fitted chunks are
        # replaced (never mutated in place) by update_action_chunk_fitted(), so
        # the local references stay valid after the lock is released. This keeps
        # ~1.5 us of array copying out of a critical section that the control
        # timer thread contends for 533 times/s.
        with self.action_lock:
            idx = self.action_chunk_index
            act_chunk, vel_chunk, acc_chunk = (
                self.action_chunk_fitted, self.vel_chunk_fitted, self.acc_chunk_fitted
            )
        # idx stays None until the first fitted chunk is published.
        currt_act = act_chunk[:, idx].copy() if act_chunk is not None and idx is not None else None
        currt_vel = vel_chunk[:, idx].copy() if vel_chunk is not None and idx is not None else None
        currt_acc = acc_chunk[:, idx].copy() if acc_chunk is not None and idx is not None else None
        return currt_act, currt_vel, currt_acc
    def get_action_fitted(self, mode='control'):
        """Get the current action (fitted and raw) indexed by action_chunk_index.

        Returns:
            np.array: The current action.
        """
        with self.action_lock:
            if self.action_chunk_index is None:
                return None, None, None, None
            if self.raw_action_count == 0:
                return None, None, None, None
            if self.action_chunk_fitted.shape[1] == 0:
                return None, None, None, None
            if self.mode != 'control' and mode == 'control':
                # print(f"Switching to control mode, current action_chunk_index={self.action_chunk_index}, reset action_chunk_index to 0.")
                self.action_chunk_index = 0
            self.mode = mode
            last_index = self.action_chunk_fitted.shape[1] - 1
            prev_index = self.action_chunk_index
            self.action_chunk_index = min(prev_index + 1, last_index)
            # Notify only on the transition into the final column -- that is the
            # sole predicate wait_for_next(mode='sync') blocks on. Broadcasting
            # on every increment fired 266.7 times/s from the control timer,
            # almost always with zero waiters (the default rdm.mode is 'async'),
            # and otherwise waking the inference thread only to re-evaluate a
            # predicate that is still false.
            if prev_index < last_index and self.action_chunk_index == last_index:
                self.action_cond.notify_all()
            # print(self.action_chunk_fitted.shape, len(self.action_chunks), self.action_chunks[0].shape, "!"*50)
            action_raw_index = int(
                self.action_chunk_index
                / (self.action_chunk_fitted.shape[1] / self.raw_action_count)
            )
            action_raw_index = min(action_raw_index, self.raw_action_count - 1)
            # action_chunks and raw_action_count are published together under
            # this same lock, so they can no longer be observed as a stale pair.
            action_raw_index = max(0, min(action_raw_index, self.action_chunks.shape[1] - 1))
            # print(action_raw_index)
            action_raw = self.action_chunks[:, action_raw_index]
            action_fitted = self.action_chunk_fitted[:, self.action_chunk_index]
            vel_fitted = self.vel_chunk_fitted[:, self.action_chunk_index]
            acc_fitted = self.acc_chunk_fitted[:, self.action_chunk_index]
            return action_fitted, action_raw, vel_fitted, acc_fitted
    
    def get_prob_progress(self):
        """Get the current prob_progress value indexed by action_chunk_index.

        Returns:
            float: The current prob_progress value, or None if not available.
        """
        with self.action_lock:
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
        # Every action-related field must be reset inside a SINGLE acquisition
        # of action_lock. This used to be split across action_thread_lock and
        # polynomial_thread_lock, which left a window in which the control timer
        # thread could enter get_action_fitted(), see action_chunk_index is not
        # None and raw_action_count > 0, and then index into an already-emptied
        # action_chunks -> IndexError. clear() runs on the web API thread
        # (reset / stop) while the control thread is live, so that window was
        # reachable in practice.
        with self.action_lock:
            self.action_chunks = np.empty((0, 0), dtype=np.float32)
            self.timestamp_chunks = np.empty(0, dtype=np.float32)
            self.raw_action_count = 0
            self.infer_count = 0
            self.start_infer_marker = 0.0
            self.start_intra_traj_marker = 0.0
            self.start_inter_traj_marker = 0.0
            self.start_ctrl_marker = 0.0
            self.avg_infer_time = 0.0
            self.avg_comm_time = 0.0
            self.avg_intra_traj_time = 0.0
            self.avg_inter_traj_time = 0.0
            self.action_chunk_fitted = None
            self.vel_chunk_fitted = None
            self.acc_chunk_fitted = None
            self.timestamps_fitted = None
            self.action_chunk_index = None
            self.prob_progress = None
            # Wake anyone blocked in wait_for_next() so it re-evaluates against
            # the cleared state instead of hanging on a chunk that is gone.
            self.action_cond.notify_all()

        with self.observe_thread_lock:
            self.observe_buffer.clear()
            self.observe_add_timestamps.clear()
            self.observe_fps = 0.0
            
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
            with self.action_cond:
                if self.action_chunk_fitted is None:
                    result = False
                else:
                    target_index = max(0, self.action_chunk_fitted.shape[1] - 1)
                    self.action_cond.wait_for(
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
