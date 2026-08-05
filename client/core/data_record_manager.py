import os
import time
import logging
import threading
import numpy as np
from queue import Empty
from datetime import datetime
from collections import deque
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Manager,Queue
from typing import Any, Dict, List, Optional, Union, Tuple
from client.utils.util import run_time_decorator
from client.core.lerobot_dataset_recorder import LeRobotDatasetRecorder
from client.core.evaluation_result_recorder import EvaluationResultRecorder

class DataRecordManager:
    """
    A class to manage writing robotic observation and action data to disk in a structured format.

    This class handles the synchronization, storage, and serialization of high-frequency robot sensor data,
    including images, states, actions, and associated metadata. It supports multiprocessing for efficient I/O
    operations and writes data into Parquet files along with corresponding video recordings.
    """

    def __init__(self, record_config: ConfigDict) -> None:
        """
        Initializes the DataRecordManager instance with the given configuration.

        Sets up directories, loads or initializes metadata, prepares video writers, and starts
        the writer process for asynchronous disk writing.

        Args:
            record_config (dict): Configuration dictionary.
                                For more information, see ./conf/save_conf.py
        """
        # Define logger
        self.logger = logging.getLogger(__name__)
        self.config = record_config
        self._init_shared_data()
        self.lerobot_recorder = LeRobotDatasetRecorder(lerobot_config=self.config.lerobot)
        self.eval_recorder = EvaluationResultRecorder(evaluation_config=self.config.evaluation)
        # self.task_language_dict = {}
        # self._parse_config_info(self.config["lerobot"])

        # Shared Queue
        self.record_queue = Queue()
        self.writer_command_queue = Queue()

        # Action recording queues
        self.action_lock = threading.Lock()
        self.action_frame_queue = deque(maxlen=10)

        self.record_obs_executor = ThreadPoolExecutor(max_workers=2)
        self.record_action_executor = ThreadPoolExecutor(max_workers=4)

        # Writer process initialization (resident process)
        self.writer_process = None
        self._ensure_writer_process()
        self._closed = False

        # Session id used to drop stale async tasks across stop/start cycles.
        self._session_lock = threading.Lock()
        self._recording_session_id = 0

    def _init_shared_data(self):
        """
        Initializes shared data variables for multiprocessing.

        This method sets up the necessary shared variables and data structures that will be used
        across multiple processes for synchronization and data sharing.
        """
        self.manager = Manager()
        self.shared_data = self.manager.Namespace()
        # Shared state and counters
        self.shared_data.total_frames = self.manager.Value('i', 0)
        self.shared_data.total_videos = self.manager.Value('i', 0)
        self.shared_data.total_episodes = self.manager.Value('i', 0)
        self.shared_data.episode_chunk = self.manager.Value('i', 0)
        self.shared_data.episode_index = self.manager.Value('i', 0)
        self.shared_data.eval_record_id = self.manager.Value('i', 0) # record_id for new record
        self.shared_data.sub_task_id = self.manager.Value('i', 0) # sub_task_id for new record
        self.shared_data.running = self.manager.Value('b', False)
    
    def _sanitize_task_name(self, task: Optional[str]) -> str:
        task_name = str(task).strip() if task is not None else ""
        if not task_name:
            task_name = "default"
        for ch in ('/', '\\', ' ', ':'):
            task_name = task_name.replace(ch, '_')
        return task_name

    def _build_full_save_path(self, save_dir: str, task_dir: str) -> str:
        self.project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        rel_save_dir = str(save_dir).strip().lstrip('/').lstrip('\\')
        return os.path.join(self.project_root_path, rel_save_dir, task_dir)

    def set_task(self, task_dir: str, sub_task_id: int, is_record_episode: bool = False, is_record_eval_log: bool = False, is_record_expe_data: bool = False) -> None:
        """Update save path by task/date before a new recording starts. Called in the writer process."""
        self.config.is_record_episode = is_record_episode
        self.config.is_record_eval_log = is_record_eval_log
        self.config.is_record_expe_data = is_record_expe_data
        self.save_dir = self.config.get("save_dir", "data/recording")     # relative path
        self.save_path = self._build_full_save_path(self.save_dir, task_dir)  # full path
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
            self.logger.info(f"{self.save_path} not exists, create it")
        
        if self.config.get('is_record_episode', False):
            total_frames, total_videos, total_episodes, chunks_size, episode_index = self.lerobot_recorder.set_task(save_path=self.save_path)
            self._sync_shared_data(total_frames=total_frames,
                                total_videos=total_videos,
                                total_episodes=total_episodes,
                                chunks_size=chunks_size,
                                episode_index=episode_index)
        else:
            self.logger.info("Recording lerobot episode is disabled, skip recording.")
        
        if self.config.get('is_record_eval_log', False):
            record_id = self.eval_recorder.set_task(save_path=self.save_path, episode_id=self.shared_data.episode_index.value)
            # Keep next eval record id consistent across processes.
            if record_id is not None:
                self._sync_shared_data(eval_record_id = record_id + 1)
            self._sync_shared_data(sub_task_id = sub_task_id)
        else:
            self.logger.info("Recording evaluation log is disabled, skip recording.")
    
    def _sync_shared_data(self, total_frames: int = None, total_videos: int = None, total_episodes: int = None, chunks_size: int = 1000, episode_index: int = None, eval_record_id: int = None, sub_task_id: int = None) -> None:
        """Sync record lerobot values to shared_data."""
        if total_frames is not None:
            self.shared_data.total_frames.value = total_frames
        if total_videos is not None:
            self.shared_data.total_videos.value = total_videos
        if total_episodes is not None:
            self.shared_data.total_episodes.value = total_episodes
        if episode_index is not None:
            self.shared_data.episode_index.value = episode_index
            self.shared_data.episode_chunk.value = episode_index // chunks_size
        if eval_record_id is not None:
            self.shared_data.eval_record_id.value = eval_record_id
        if sub_task_id is not None:
            self.shared_data.sub_task_id.value = sub_task_id
        # if eval_record_duration is not None:
        #     self.shared_data.eval_record_duration.value = eval_record_duration
        # self.logger.info(f"total_frames={self.shared_data.total_frames.value}, total_videos={self.shared_data.total_videos.value}, total_episodes={self.shared_data.episode_index.value}")

    def update_camera_shape_dict(self, shape_dict: Dict[str, Union[tuple[int, int, int], list[int]]]) -> None:
        """Update camera shape settings for current recording session and metadata.

        Args:
            shape_dict: Mapping from camera name (e.g. ``cam.head``) to HWC shape.
        """
        self.lerobot_recorder.update_camera_shape_dict(shape_dict)

    def _get_recording_session_id(self) -> int:
        with self._session_lock:
            return self._recording_session_id

    def _bump_recording_session_id(self) -> int:
        with self._session_lock:
            self._recording_session_id += 1
            return self._recording_session_id

    def _ensure_writer_process(self) -> None:
        """Ensure resident writer process is alive."""
        if self.writer_process is not None and self.writer_process.is_alive():
            return

        self.writer_process = Process(target=self._writer_process_loop, daemon=True)
        self.writer_process.start()
        self.logger.info("Resident writer process started.")

    def _writer_process_loop(self) -> None:
        """Resident process loop: receives start/shutdown commands and dispatches write tasks in thread executor."""
        self.logger.info("Writer resident process loop started.")
        self.lerobot_recorder.start_episode_record_crud_listener()
        self.eval_recorder.start_eval_record_crud_listener()
        write_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="writer_worker")
        write_future = None

        try:
            while True:
                if write_future is not None and write_future.done():
                    try:
                        write_future.result()
                    except Exception as e:
                        self.logger.exception(f"writer_worker thread exited with exception: {e}")
                    finally:
                        write_future = None

                try:
                    command = self.writer_command_queue.get(timeout=0.2)
                except Empty:
                    continue

                if command.get("command", "") == "start":
                    if write_future is not None and (not write_future.done()):
                        self.logger.warning("Receive start command while previous write task is still running, skip.")
                        continue
                    self.set_task(task_dir = command.get("task_dir", "default"),
                                sub_task_id = command.get("sub_task_id", 0),
                                is_record_episode = command.get("is_record_episode", False),
                                is_record_eval_log = command.get("is_record_eval_log", False),
                                is_record_expe_data = command.get("is_record_expe_data", False))
                    write_future = write_executor.submit(self._write_process_fun)
                elif command.get("command", "") == "stop":
                    self.shared_data.running.value = False
                    if write_future is not None:
                        try:
                            write_future.result()
                            self._clear_queues()
                        except Exception as e:
                            self.logger.exception(f"writer_worker thread exited with exception during stop recording: {e}")
                elif command.get("command", "") == "shutdown":
                    self.shared_data.running.value = False
                    if write_future is not None:
                        try:
                            write_future.result()
                        except Exception as e:
                            self.logger.exception(f"writer_worker thread exited with exception during shutdown: {e}")
                    break
                else:
                    self.logger.warning(f"Unknown writer command: {command}")
        except KeyboardInterrupt:
            self.logger.warning("Writer resident process interrupted by keyboard.")
        except Exception:
            self.logger.exception("Writer resident process loop exited with exception")
        finally:
            write_executor.shutdown(wait=True, cancel_futures=True)
            self.eval_recorder.stop_eval_record_crud_listener()
            self.lerobot_recorder.stop_episode_record_crud_listener()
            self.logger.info("Writer resident process loop exited.")

    def _shutdown_writer_process(self) -> None:
        """Shutdown resident writer process safely."""
        if self.writer_process is None:
            return

        try:
            if self.writer_process.is_alive():
                self.writer_command_queue.put({"command": "shutdown"})
                self.writer_process.join(timeout=5.0)
                if self.writer_process.is_alive():
                    self.logger.warning("Writer process still alive after graceful shutdown, terminate it.")
                    self.writer_process.terminate()
                    self.writer_process.join(timeout=2.0)
        except Exception as e:
            self.logger.exception(f"Failed to shutdown writer process gracefully: {e}")
        finally:
            self.writer_process = None

    def add_observation_async(self, observation: Dict[str, Any], extra_info: Dict[str, Any], timestamp: int | float):
        """
        Asynchronously writes observation data into the dataset.

        Args:
            observations (Dict[str, Any]):A dictionary containing observation with the following keys:
                - 'cam.*': np.ndarray,
                - 'obs.state': np.ndarray
            extra_info (Dict[str, Any]): A dictionary containing extra information such as language status, server status, runtime status, etc.
            time_now (int | float): The current timestamp.
        """
        session_id = self._get_recording_session_id()
        self.record_obs_executor.submit(self._add_observation_fun, observation, extra_info, timestamp, session_id)

    def add_action_async(self, action: np.ndarray, timestamp: int | float) -> None:
        """
        Asynchronously writes action data into the dataset.

        Args:
            action (np.ndarray): A dictionary containing action data from the environment.
        """
        session_id = self._get_recording_session_id()
        self.record_action_executor.submit(self._add_action_fun, action, timestamp, session_id)
    
    def start_recording(self, task_id: str, sub_task_id: int) -> str:
        """
        Starts the recording process by dispatching write task in resident writer process.

        This method should be called before adding any observations or actions to ensure that
        the writer process is running and ready to handle incoming data.
        """
        try:
            session_id = self._bump_recording_session_id()
            self._clear_queues()

            self.shared_data.running.value = True
            task_dir = self._sanitize_task_name(task_id) + '_' + datetime.now().strftime("%Y%m%d")
            command = {
                "command": "start",
                "task_dir": task_dir,
                "task_id": task_id,
                "sub_task_id": sub_task_id,
                "is_record_episode": self.config.is_record_episode,
                "is_record_eval_log": self.config.is_record_eval_log,
                "is_record_expe_data": self.config.is_record_expe_data
            }
            self.writer_command_queue.put(command)
            self.logger.info(f"Writer task dispatched successfully. task_dir={task_dir}, session_id={session_id}")
            return task_dir
        except Exception as e:
            self.logger.exception(f"Failed to start writer task: {e}")
            return None

    def _wait_for_record_data(self, get_timeout_s: float = 0.05, max_attempts: int = 20) -> Optional[Any]:
        """Best-effort: read one record payload from queue and put it back unchanged."""
        timeout = max(0.001, get_timeout_s)
        max_attempts = max(1, max_attempts)

        for _ in range(max_attempts):
            payload = None
            try:
                payload = self.record_queue.get(timeout=timeout)
            except Empty:
                continue
            except Exception as e:
                self.logger.exception(f"Failed to read record_queue at recording start: {e}")
                return None

            try:
                return payload
            finally:
                try:
                    if payload is not None and self.record_queue.empty():
                        self.record_queue.put(payload)
                    else:
                        self.logger.warning("Data skip put back because record queue is not empty.")
                except Exception as requeue_e:
                    self.logger.exception(f"Failed to requeue payload after queue read: {requeue_e}")
                    return None

        return None

    def stop_recording(self):
        """
        Stops recording and waits for all queued data to be written before exiting.

        Behavior:
        - Set ``running=False`` to stop accepting new records.
        - Let resident writer task continue draining ``record_queue``.
        """
        self._bump_recording_session_id()
        if self.shared_data.running.value:
            self.shared_data.running.value = False
            self.logger.info("Signaled writer task to stop after draining queue.")

        command = {
            "command": "stop",
        }
        self.writer_command_queue.put(command)

    def _add_observation_fun(self, observation: Dict[str, Any], extra_info: Dict[str, Any], timestamp: int | float, session_id: int) -> None:
        """
        Process and store observation data including camera images, robot state, and time frame.

        Args:
            observation (Dict[str, Any]): Dictionary containing observation data with the following keys:
                - 'cam.head': np.ndarray
                - 'cam.hand_left': np.ndarray
                - 'cam.hand_right': np.ndarray
                - 'loc_timestamp': int
                - 'obs.state': np.ndarray
            extra_info (Dict[str, Any]): Dictionary containing extra information such as language status, server status, runtime status, etc.
            timestamp (int): Timestamp of the current observation.

        Raises:
            AssertionError: If the provided timestamp is not greater than the last recorded timestamp.
        """
        if (not self.shared_data.running.value) or (session_id != self._get_recording_session_id()):
            return

        # When action_frame_queue is empty, discard the observation frame
        action = None
        with self.action_lock:
            if not self.action_frame_queue:
                self.logger.warning("Action frame queue is empty, discarding observation frame.")
                return
            else:
                action, _ = self.action_frame_queue.pop()
        
        # observation['language_instruction'] = language_instruction
        # observation['language_instruction'] = 'Test'
        # check state shape 

        self.record_queue.put((observation, action, extra_info))

    def _add_action_fun(self, action: np.ndarray, timestamp: int | float, session_id: int) -> None:
        """
        Process and store the action data along with its timestamp.

        Args:
            action (np.ndarray): The action data to be stored, typically representing joint torques or target positions.
            timestamp (int): The timestamp associated with this action.

        Raises:
            AssertionError: If the provided timestamp is not strictly increasing compared to the last recorded one.
        """
        if (not self.shared_data.running.value) or (session_id != self._get_recording_session_id()):
            return

        # check action shape 
        # if action.shape[0] < self.action_shape:
        #     action = np.concatenate([action, np.zeros(self.action_shape-action.shape[0])], axis=0)
        self.action_frame_queue.append((action, timestamp))

    def _write_process_fun(self):
        """
        Main loop for the writer process responsible for writing data to disk.

        Continuously pulls data from the shared queue and writes it to video files and Parquet file buffer.
        The loop runs until `self.shared_data.stop` is set to True. Each iteration processes one observation-action pair:
            - Appends new language instructions to the episode task list
            - Assigns a unique task index based on instruction text
            - Writes camera images to corresponding video files
            - Constructs a record dictionary and appends it to the shared Parquet buffer

        Frame index is incremented with each successful write.

        Raises:
            KeyboardInterrupt: If user interrupts execution via keyboard (e.g., Ctrl+C)
            Exception: Any other exception during writing will terminate the thread
        """
        self.logger.info("Starting recording process loop...")

        try:
            # prepare recording for all recorders
            if self.config.get('is_record_eval_log', False):
                self.eval_recorder.begin_recording(eval_record_id=self.shared_data.eval_record_id.value,
                                                sub_task_id=self.shared_data.sub_task_id.value)
            
            if self.config.get('is_record_episode', False):
                self.lerobot_recorder.begin_recording(episode_chunk = self.shared_data.episode_chunk.value,
                                                    episode_index = self.shared_data.episode_index.value,
                                                    total_frames = self.shared_data.total_frames.value,
                                                    total_videos = self.shared_data.total_videos.value,
                                                    total_episodes = self.shared_data.total_episodes.value,
                                                    save_raw=self.config.save_raw)
                self.lerobot_recorder._sync_browse_on_record_start(
                    episode_chunk=self.shared_data.episode_chunk.value,
                    episode_index=self.shared_data.episode_index.value,
                )
            # print(f"DEBUG: Mark1")    
            # recording in the loop for all recorders
            while self.shared_data.running.value or (not self.record_queue.empty()):
                # Get state and action data from queue
                try:
                    step_state, step_action, step_extra = self.record_queue.get(timeout=0.1)
                    if self.config.get('is_record_episode', False):
                        self.lerobot_recorder.add_frame_async(step_state=step_state,
                                                            step_action=step_action,
                                                            step_extra=step_extra)
                    if self.config.get('is_record_eval_log', False):
                        self.eval_recorder.add_frame_async(step_extra=step_extra)
                except Empty as e:
                    if self.shared_data.running.value:
                        self.logger.exception(f"Record queue empty, waiting for data: {e}")
                        # time.sleep(0.03)
                    else:
                        break
                    # continue
                # print('Write successful ——————————————————')
            # print(f"DEBUG: Mark2")    

                # self.logger.info('write process stopped!!! ')
            # finish recording for all recorders
            if self.config.get('is_record_episode', False):
                episode_index, total_frames, total_videos, total_episodes = self.lerobot_recorder.end_recording()
                self._sync_shared_data(total_frames=total_frames,
                                    total_videos=total_videos,
                                    total_episodes=total_episodes,
                                    episode_index=episode_index) # chunks_size doesn't change
            if self.config.get('is_record_eval_log', False):
                currt_record_id = self.eval_recorder.end_recording()
                self._sync_shared_data(eval_record_id=currt_record_id + 1)

        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
            # self.release_writers()
        except Exception as e:
            self.logger.exception(f"Writing thread exited with exception: {e}")
            # self.release_writers()
        finally:
            # if self.config.get('is_record_eval_log', False):
            #     try:
            #         self.eval_recorder.stop_eval_record_crud_listener()
            #     except Exception as e:
            #         self.logger.warning(f"Failed to stop eval record CRUD listener in finally: {e}")
            self.logger.info("Writing thread exited.")
            # self.release_writers()

    def close(self):
        """Release all dataset writer resources safely and idempotently."""
        self.logger.info("Closing DataRecordManager...")

        try:
            self.stop_recording()
        except Exception:
            self.logger.debug("stop_recording failed during close", exc_info=True)

        self.logger.info("Closing DataRecordManager, recording stopped.")
        try:
            self._shutdown_writer_process()
        except Exception:
            self.logger.debug("shutdown writer process failed during close", exc_info=True)

        try:
            if getattr(self, "record_obs_executor", None) is not None:
                self.record_obs_executor.shutdown(wait=True, cancel_futures=True)
        except Exception:
            self.logger.debug("record_obs_executor shutdown failed", exc_info=True)
        self.logger.info("Closing DataRecordManager, observation executor shutdown.")

        try:
            if getattr(self, "record_action_executor", None) is not None:
                self.record_action_executor.shutdown(wait=True, cancel_futures=True)
        except Exception:
            self.logger.debug("record_action_executor shutdown failed", exc_info=True)
        self.logger.info("Closing DataRecordManager, action executor shutdown.")

        try:
            if getattr(self, "record_queue", None) is not None:
                self.record_queue.close()
                self.record_queue.cancel_join_thread()
        except Exception:
            self.logger.debug("record_queue close/join failed", exc_info=True)

        try:
            if getattr(self, "writer_command_queue", None) is not None:
                self.writer_command_queue.close()
                self.writer_command_queue.cancel_join_thread()
        except Exception:
            self.logger.debug("writer_command_queue close/join failed", exc_info=True)

        self.logger.info("Closing DataRecordManager, record queue closed.")
        try:
            if getattr(self, "manager", None) is not None:
                self.manager.shutdown()
        except Exception:
            self.logger.debug("manager shutdown failed", exc_info=True)

        self.logger.info("DataRecordManager closed successfully.")
        
    def _clear_queues(self):
        """
        Safely clear both the multiprocessing `record_queue` and the `action_frame_queue`.

        - Drains `record_queue` using non-blocking `get_nowait()`.
        - Clears `action_frame_queue` under `action_lock`.
        """
        # Drain multiprocessing queue
        try:
            while not self.record_queue.empty():
                try:
                    self.record_queue.get_nowait()
                except Empty:
                    break
        except Exception:
            # Fallback: keep calling get_nowait until it fails
            try:
                while True:
                    self.record_queue.get_nowait()
            except Exception:
                pass

        # Clear in-process deque with lock
        with self.action_lock:
            try:
                self.action_frame_queue.clear()
            except Exception:
                # Fallback: pop until empty
                while self.action_frame_queue:
                    try:
                        self.action_frame_queue.pop()
                    except IndexError:
                        break

        self.logger.info("All queues cleared.")

# Mock observation data generator
def generate_mock_observation():
    """
    Simulates an observation data input.
    Returns:
        dict: A dictionary containing simulated observation data.
    """
    state = np.random.rand(20).astype(np.float32)  # 20-dimensional state
    image1 = (np.random.rand(720, 1280, 3) * 255).astype(np.uint8)  # RGB image
    image2 = (np.random.rand(480, 848, 3) * 255).astype(np.uint8)
    image3 = (np.random.rand(480, 848, 3) * 255).astype(np.uint8)

    return {
        "cam.head": image1,
        "cam.hand_left": image2,
        "cam.hand_right": image3,
        'obs.state': state    }


# Mock action data generator
def generate_mock_action():
    """
    Simulates an action data input.
    Returns:
        dict: A dictionary containing simulated action data.
    """
    action = np.random.rand(20).astype(np.float32)  # 20-dimensional action
    return action


if __name__ == "__main__":
    pass