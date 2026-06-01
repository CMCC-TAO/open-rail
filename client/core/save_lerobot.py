import os
import numpy as np
from PIL import Image
import json
import cv2
import time
from ml_collections import ConfigDict
from collections import deque
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import threading
from multiprocessing import Process, Manager,Queue
from queue import Empty
from typing import Any, Dict, List, Optional, Union
import copy
import logging
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
import traceback
class LeRobotDatasetWriter:
    """
    A class to manage writing robotic observation and action data to disk in a structured format.

    This class handles the synchronization, storage, and serialization of high-frequency robot sensor data,
    including images, states, actions, and associated metadata. It supports multiprocessing for efficient I/O
    operations and writes data into Parquet files along with corresponding video recordings.
    """

    def __init__(self, record_config: ConfigDict ) -> None:
        """
        Initializes the LeRobotDatasetWriter instance with the given configuration.

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
        self.task_language_dict = {}
        meta_dir_exists = self._check_meta_path_and_dir(self.config["save_path"])
        if meta_dir_exists:
            self._update_config_from_meta_file()
        self._parse_config_info_features(self.config["info"]["features"])

        # Shared Queue
        self.record_queue = Queue()

        # Action recording queues
        self.action_lock = threading.Lock()
        self.action_frame_queue = deque(maxlen=10)

        self.record_obs_executor = ThreadPoolExecutor(max_workers=2)
        self.record_action_executor = ThreadPoolExecutor(max_workers=4)

        # Writer process initialization
        self.writer_process = Process(target=self._write_process_fun, daemon=True)

    def _init_shared_data(self):
        """
        Initializes shared data variables for multiprocessing.

        This method sets up the necessary shared variables and data structures that will be used
        across multiple processes for synchronization and data sharing.
        """
        self.manager = Manager()
        self.shared_data = self.manager.Namespace()
        # Shared state and counters
        # self.shared_data.start_write_time = self.manager.Value('b', False)
        # self.shared_data.stop = self.manager.Value('b', False)
        # self.shared_data.close = self.manager.Value('b', False)
        # self.shared_data.init_write = self.manager.Value('b', True)
        self.shared_data.total_frames = self.manager.Value('i', 0)
        self.shared_data.episode_chunk = self.manager.Value('i', 0)
        self.shared_data.episode_index = self.manager.Value('i', 0)
        self.shared_data.running = self.manager.Value('b', False)
        # self.shared_data.episode_parquet_list = self.manager.list()
        self.shared_data.save_video_path_list = self.manager.list()
        # Task and language information storage
        # self.shared_data.episode_task_list = self.manager.list()
        # self.shared_data.task_language_dict = self.manager.dict()
    
    def _check_meta_path_and_dir(self, save_path: str) -> bool:
        # save_path_cfg = str(self.config["save_path"])
        self.project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.save_path = os.path.abspath(
            save_path if os.path.isabs(save_path) else os.path.join(self.project_root_path, save_path)
        )
        self.config["save_path"] = self.save_path
        # TODO: support for chunk-001
        self.meta_dir = os.path.join(self.save_path, 'meta')
        if not os.path.exists(self.meta_dir):
            # Create directories
            os.makedirs(self.meta_dir, exist_ok=True)
            self.logger.info(f"{self.meta_dir} not exists, create it")
            return False
        else:
            return True

    def _update_config_from_meta_file(self):
        """
        Checks whether the directory `self.meta_dir` exists.

        If it exists and contains required files (info.json, episodes.jsonl, tasks.jsonl),
        updates the configuration using these files. Otherwise, raises an error due to missing files.

        Raises:
            AssertionError: If any of the required files are missing in the existing directory.
        """
        
        # Check for required files
        required_files = ['info.json', 'episodes.jsonl', 'tasks.jsonl']
        missing_files = []

        for filename in required_files:
            file_path = os.path.join(self.meta_dir, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        # Raise error if any required file is missing
        if missing_files:
            self.logger.error(f"{self.meta_dir} is missing the following required files: {', '.join(missing_files)}")
            assert False, "Missing required meta files."
            return

        # Load info.json and update dataset info
        info_file_path = os.path.join(self.meta_dir, 'info.json')
        self._update_dataset_info_from_meta_file(info_file_path)
        self.shared_data.total_frames = self.config['info']['total_frames']
        self.shared_data.episode_index = self.config['info']['total_episodes']
        self.shared_data.episode_chunk = self.config['info']['total_episodes'] // self.config['info']['chunks_size']

        # Load tasks.jsonl and update task languages
        task_file_path = os.path.join(self.meta_dir, 'tasks.jsonl')
        self._update_task_languages_from_meta_file(task_file_path)

    def _update_dataset_info_from_meta_file(self, file_path: str) -> None:
        """
        Updates the dataset info using the provided JSON file.
        """
        # Open the specified JSON file and load its contents
        with open(file_path, 'r') as file:
            data = json.loads(file.read())
        
        # Update the dataset info in the config using the loaded JSON data
        self.config["info"] = ConfigDict(data, allow_dotted_keys=True)
        # self._normalize_record_features_cam()

        # Print a success message indicating that the meta files have updated the config
        self.logger.info("update dataset info from meta info file success.")
    
    def _update_task_languages_from_meta_file(self, file_path: str) -> None:
        """
        Updates the task-language mapping using the provided JSONL file.
        """
        with open(file_path, 'r') as file:
            for line in file:
                data = json.loads(line)
                task_index = data['task_index']
                task_name = data['tasks'] 
                if task_name not in self.task_language_dict:
                    self.task_language_dict[task_name] = task_index
        self.logger.info(f"Update task languages from meta task file success, task_language_dict={self.task_language_dict}.")
    
    def _parse_config_info_features(self, features_config: ConfigDict) -> None:
        self.camera_name_list = []
        self.camera_shape_dict = {}
        for camera_name in features_config.keys():
            if str(camera_name).startswith("cam."):
                self.camera_name_list.append(camera_name)
            shape_list = features_config[camera_name]["shape"]
            self.camera_shape_dict[camera_name] = tuple(shape_list)

        self.action_shape = features_config["action"]['shape'][0]
        self.state_shape = features_config["observation.state"]['shape'][0]
    def add_observation_async(self, observation: Dict[str, np.ndarray], language_instruction: str, timestamp: int | float):
        """
        Asynchronously writes observation data into the dataset.

        Args:
            observations (dict):A dictionary containing observation with the following keys:
                - 'cam.*': np.ndarray,
                - 'obs.state': np.ndarray
            language (str): The language instruction associated with the observation.
            time_now (int | float): The current timestamp.
        """
        self.record_obs_executor.submit(self._add_observation_fun, observation, language_instruction, timestamp)

    def add_action_async(self, action: np.ndarray, timestamp: int | float) -> None:
        """
        Asynchronously writes action data into the dataset.

        Args:
            action (np.ndarray): A dictionary containing action data from the environment.
        """
        self.record_action_executor.submit(self._add_action_fun, action, timestamp)
    
    def start_recording(self):
        """
        Starts the recording process by launching the writer process.

        This method should be called before adding any observations or actions to ensure that
        the writer process is running and ready to handle incoming data.
        """
        try:
            self.shared_data.running.value = True
            self._clear_queues()
            self.writer_process.start()
            self.logger.info("Writer process started successfully.")
        except Exception as e:
            self.logger.error(f"Failed to start writer_process: {e}")
    def stop_recording(self):
        """
        Stops the recording process by signaling the writer process to terminate.

        This method sets the 'running' flag to False, which should cause the writer process
        to finish processing any remaining data and exit gracefully.
        """
        if self.shared_data.running.value:
            self.shared_data.running.value = False
            self.logger.info("Signaled writer process to stop.")
            if self.writer_process.is_alive():
                self.writer_process.join(timeout=2)
                if self.writer_process.is_alive():
                    self.logger.warning("Writer thread still alive after timeout, terminating...")
                    self.writer_process.terminate()
                    self.writer_process.join()
        else:
            self.logger.warning("stop_recording called but writer process is not running.")
    def _add_observation_fun(self, observation: Dict[str, np.ndarray], language_instruction: str, timestamp: int | float) -> None:
        """
        Process and store observation data including camera images, robot state, and time frame.

        Args:
            observation (Dict[str, np.ndarray]): Dictionary containing observation data with the following keys:
                - 'cam.head': np.ndarray
                - 'cam.hand_left': np.ndarray
                - 'cam.hand_right': np.ndarray
                - 'loc_timestamp': int
                - 'obs.state': np.ndarray
            language_instruction (str): Natural language instruction associated with the observation.
            timestamp (int): Timestamp of the current observation.

        Raises:
            AssertionError: If the provided timestamp is not greater than the last recorded timestamp.
        """
        # When action_frame_queue is empty, discard the observation frame
        action = None
        with self.action_lock:
            if not self.action_frame_queue:
                self.logger.warning("Action frame queue is empty, discarding observation frame.")
                return
            else:
                action, _ = self.action_frame_queue.pop()
        
        observation['language_instruction'] = language_instruction
        # check state shape 
        if observation['obs.state'].shape[0] != self.state_shape:
            self.logger.warning(f"obs shape {observation['obs.state'].shape[0]} is not correct, config shape is {self.state_shape}, add 0 to obs.state")
            # assert state['obs.state'].shape[0] <= self.state_shape, \
            # f"obs shape {state['obs.state'].shape[0]} is bigger than config shape {self.state_shape}"
            observation['obs.state'] = np.concatenate([
                observation['obs.state'],
                np.zeros(self.state_shape - observation['obs.state'].shape[0], dtype=observation['obs.state'].dtype)
            ], axis=0)
        self.record_queue.put((observation, action))
                # print(f"Write successful: {timestamp}")

    def _add_action_fun(self, action: np.ndarray, timestamp: int | float) -> None:
        """
        Process and store the action data along with its timestamp.

        Args:
            action (np.ndarray): The action data to be stored, typically representing joint torques or target positions.
            timestamp (int): The timestamp associated with this action.

        Raises:
            AssertionError: If the provided timestamp is not strictly increasing compared to the last recorded one.
        """
        # check action shape 
        if action.shape[0]!= self.action_shape:
            # self.logger.warning(f"Action shape {action.shape[0]} is not correct, config shape is {self.action_shape} , add 0 to the action")
            self.logger.warning(f"Action shape {action.shape[0]} is bigger than config shape {self.action_shape}")
            action = np.concatenate([action, np.zeros(self.action_shape-action.shape[0])], axis=0)
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
        # Wait until the first data arrives
        self.logger.info("Starting write process loop...")

        try:
            episode_chunk = self.shared_data.episode_chunk.value
            episode_index = self.shared_data.episode_index.value
            total_frames = self.shared_data.total_frames.value
            self.video_writers = self._create_video_writer(
                episode_chunk=episode_chunk,
                episode_index=episode_index
            )
            self.parquet_schema, self.parquet_writer = self._create_parquet_writer(
                episode_chunk=episode_chunk,
                episode_index=episode_index
            )
            self.parquet_frame_list = list()
            self.parquet_lock = threading.Lock()
            # copy task dict
            # self.shared_data.last_task_language_dict = self.copy_shared_data_dict(self.shared_data.task_language_dict)
            frame_index = 0
            episode_task_list = []
            step_task_index = 0
            # Use a thread to write parquet file
            write_parquet_thread = threading.Thread(self._write_parquet_fun, daemon = True)
            try:
                write_parquet_thread.start()
            except Exception as e:
                self.logger.error("Write parquet thread can't start.")
                return
            while self.shared_data.running.value:
                # Get state and action data from queue
                try:
                    step_state, step_action = self.record_queue.get_nowait()
                except Empty:
                    self.logger.info("Record queue empty, waiting for data...")
                    time.sleep(0.1)
                    continue
                step_language = step_state['language_instruction']
                
                # Track new language instructions per episode
                if step_language not in episode_task_list:
                    episode_task_list.append(step_language)
                
                # Assign task index based on unique language instruction
                if step_language not in self.task_language_dict.keys():
                    step_task_index = len(self.task_language_dict.keys())
                    self.task_language_dict[step_language] = step_task_index
                else:
                    step_task_index = self.task_language_dict[step_language]
                
                # Write image frames to video files
                for camera_name in self.camera_name_list:
                    expected_shape = self.camera_shape_dict[camera_name]
                    raw_frame = step_state.get(camera_name)
                    frame = self._prepare_video_frame(raw_frame, expected_shape)
                    if frame is None:
                        self.logger.warning(f"{camera_name} frame invalid, skip this frame")
                        continue

                    writer = self.video_writers.get(camera_name, None)
                    if writer is None or (not writer.isOpened()):
                        self.logger.error(f"Video writer is not opened for {camera_name}, skip write")
                        continue

                    writer.write(frame)
                    self.logger.info(f"{camera_name} writes a frame.")
                # Construct record dictionary for Parquet file
                parquet_frame = {
                    'observation.state': step_state['obs.state'].tolist(),
                    'action': step_action.tolist(),
                    'episode_index': episode_index,
                    'frame_index': frame_index,
                    'index': total_frames+frame_index,
                    'task_index': 0,  # Placeholder for task index, can be updated based on actual task mapping
                    'timestamp': 1/30 * frame_index,  # Fixed frame rate assumption
                }
                with self.parquet_lock:
                    self.parquet_frame_list.append(parquet_frame)
                
                # Update counters
                frame_index += 1
                if frame_index % 120 == 0:
                    self.logger.info(
                        f"write-loop progress: episode={self.shared_data.episode_index.value}, "
                        f"frame_index={frame_index}, cached_records={len(self.parquet_frame_list)}"
                    )
                # print('Write successful ——————————————————')

                # self.logger.info('write process stopped!!! ')
            self.shared_data.episode_index.value = episode_index + 1
            self.shared_data.total_frames.value = total_frames + frame_index
            self._write_meta_files(total_frames=self.shared_data.total_frames.value,
                                total_episodes=self.shared_data.episode_index.value,
                                episode_length=frame_index,
                                episode_task_list=episode_task_list)
            # stop recording for current episode: flush video files immediately
            write_parquet_thread.join(timeout=1.0)
            self._release_video_writers()
            # self._clear_queues()
            # print(f'self.shared_data.task_language_dict {self.shared_data.task_language_dict}')
        
        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
            # self.release_writers()
        
        except Exception as e:
            self.logger.error(f"Writing thread exited with exception: {e}")
            # self.release_writers()
        
        finally:
            self.logger.info("Writing thread exited.")
            # self.release_writers()

    # def end_write(self):
    #     """
    #     - Deletes any partially written video files
    #     - Deletes the Parquet file if it exists
    #     """
    #     for path in self.shared_data.save_video_path_list:
    #         print(f"path {path}")
    #         if os.path.exists(path):
    #             print(f"Deleting file {path}")
    #             os.remove(path)
    #     if os.path.exists(self.parquet_file_path):
    #         os.remove(self.parquet_file_path)
    
    # def copy_shared_data_dict(self,input_dict):
    #     """
        
    #     """
    #     output_dict = self.manager.dict()
    #     for key, value in input_dict.items():
    #         output_dict[key] = value
    #     return output_dict

    def close(self):
        """
        Gracefully shuts down the writer and finalizes data writing.

        This method signals the writer thread to stop by setting the 'stop' flag,
        releases all video writers, increments the episode counter, updates the total
        number of frames, and triggers the finalization process (`end_write`) to save
        all buffered data to disk.

        Should be called when ending data collection to ensure all data is flushed
        and resources are properly released.
        """
        # self.shared_data.stop.value = True
        # self.shared_data.close.value = True
        # time.sleep(1)
        # print(f"[Main] Writer alive? {self.writer_process.is_alive()}")
        self.shared_data.running.value = False
        # self.record_obs_executor.shutdown(wait=True)
        # self.record_action_executor.shutdown(wait=True)
        if self.writer_process.is_alive():
            self.writer_process.join(timeout=2)
            if self.writer_process.is_alive():
                self.logger.warning("Writer thread still alive after timeout, terminating...")
                self.writer_process.terminate()
                self.writer_process.join()

        # self.end_write()

        # Clean up resources
        # if self.record_queue:
        #     self.record_queue.close()
        #     self.record_queue.join_thread()

        # if self.manager:
        #     self.manager.shutdown()

        # self.logger.info("LeRobotDatasetWriter closed successfully.")
        
    
    # def save_writed_data(self):
    #     """
    #     Gracefully shuts down the writer and finalizes data writing.

    #     This method signals the writer thread to stop by setting the 'stop' flag,
    #     releases all video writers, increments the episode counter, updates the total
    #     number of frames, and triggers the finalization process (`end_write`) to save
    #     all buffered data to disk.

    #     Should be called when ending data collection to ensure all data is flushed
    #     and resources are properly released.
    #     """
    #     print(f"save_writed_data called, writer alive? {self.writer_process.is_alive()}")
    #     # stop record
    #     # self.shared_data.stop.value = True

    #     time.sleep(1)
    #     # self.writer_process.join(timeout=1)
    #     ## The relevant variables increase
    #     # self.logger.info(f"LAST writer_process IS alive: {self.writer_process.is_alive()}")
    #     # self.episode_length = len(self.shared_data.episode_parquet_list) 
    #     # self.total_frames += len(self.shared_data.episode_parquet_list)
    #     # Write to parquet file
    #     # self.write_parquet_file()
    #     # Write meta files
    #     # self.write_meta_files()
    #     # clean record data
    #     # self.clean_record_data()
    #     self.logger.info("Abandon the current recording data and start a new one.")
    #     # self.clean_record_data()
    #     # self.shared_data.counter.value += 1
        
    #     # self.shared_data.save_video_path_list = self.manager.list()

    # def abandon_record_data(self):
    #     """
    #     Abandon the current recording data and start a new one.
    #     """
    #     self.shared_data.stop.value = True
    #     time.sleep(1)
    #     # self.writer_process.join(timeout=1)
    #     # print("Abandon the current recording data and start a new one.")
    #     # clean record data
    #     self.logger.info("Abandon the current recording data and start a new one.")
    #     self.clean_record_data()

    #     # modify task language equals last task language
    #     # print(f'last task language: {self.shared_data.last_task_language_dict}')
    #     self.shared_data.task_language_dict = self.copy_shared_data_dict(self.shared_data.last_task_language_dict)
    #     # # new parquet file
    #     # self.parquet_file_path = os.path.join(
    #     #     self.save_path,
    #     #     self.config.info.data_path.format(episode_chunk=self.episode_chunk, episode_index=self.shared_data.counter.value)
    #     # )
    #     # self.parquet_writer = pq.ParquetWriter(self.parquet_file_path, self.schema)
    #     # Writer process initialization
    #     self.shared_data.init_write.value = True
    #     self.shared_data.stop.value = False
        

    # def clean_record_data(self):
    #     """ 
    #     Clean up the record data.
    #     """
    #     del self.shared_data.save_video_path_list[:]
    #     # del self.shared_data.episode_parquet_list[:]
    #             # clean episode task list
    #     # del self.shared_data.episode_task_list[:]
    #     # self.obs_time.clear()
    #     # self.action_list.clear()
    #     # self.action_time.clear()
    #     ## clean queues (record_queue + action_frame_queue)
    #     self._clear_queues()
    #     self.logger.info("cleaning data finished")

    # def clear_record_queue(self):
    #     """
    #     clear record queue
    #     """
    #     while not self.record_queue.empty():
    #         try:
    #             self.record_queue.get_nowait()
    #         except Empty:
    #             break
    #     self.logger.info("record_queue is clear.")

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

    def _prepare_video_frame(self, frame: Any, expected_shape: tuple[int, int, int]) -> Optional[np.ndarray]:
        """Normalize input frame to contiguous uint8 HWC(BGR-compatible) for VideoWriter."""
        if isinstance(frame, Image.Image):
            frame = np.array(frame)
        if not isinstance(frame, np.ndarray):
            return None

        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.ndim == 3 and frame.shape[0] in (1, 3, 4) and frame.shape[-1] not in (1, 3, 4):
            frame = np.transpose(frame, (1, 2, 0))

        if frame.ndim != 3:
            return None

        if frame.shape[2] == 1:
            frame = np.repeat(frame, 3, axis=2)
        elif frame.shape[2] >= 4:
            frame = frame[:, :, :3]

        exp_h, exp_w = expected_shape[0], expected_shape[1]
        if frame.shape[0] != exp_h or frame.shape[1] != exp_w:
            frame = cv2.resize(frame, (exp_w, exp_h), interpolation=cv2.INTER_LINEAR)

        if frame.dtype != np.uint8:
            if np.issubdtype(frame.dtype, np.floating):
                max_val = float(np.nanmax(frame)) if frame.size else 0.0
                if max_val <= 1.0:
                    frame = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
                else:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)
            else:
                frame = np.clip(frame, 0, 255).astype(np.uint8)

        return np.ascontiguousarray(frame)

    def _create_video_writer(self, episode_chunk: int = 0, episode_index: int = 0) -> Dict[str, Any]:
        """
        Generates video writers for each camera stream.

        Creates OpenCV VideoWriter objects for each camera specified in the configuration.

        Returns:
            dict: A dictionary mapping camera names to their respective VideoWriter objects.
        """
        # Video writing setup
        save_video_path = os.path.join(self.save_path, 'videos', f'chunk-{episode_chunk:03d}')
        filename = f"{'episode'}_{episode_index:06d}.{'mp4'}"
        video_write_dict = {}
        self.camera_shape_dict = {}
        fps = float(self.config['info'].get('fps', 30))

        for camera_name in self.camera_name_list:
            shape_list = self.camera_shape_dict[camera_name]
            height, width = int(shape_list[0]), int(shape_list[1])
            os.makedirs(os.path.join(save_video_path, camera_name), exist_ok=True)
            video_path = os.path.join(save_video_path, camera_name, filename)
            self.shared_data.save_video_path_list.append(video_path)

            writer = None
            for codec in ('mp4v', 'avc1', 'XVID', 'MJPG'):
                fourcc = cv2.VideoWriter_fourcc(*codec)
                candidate = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                if candidate is not None and candidate.isOpened():
                    writer = candidate
                    break
                if candidate is not None:
                    candidate.release()
            if writer is None:
                raise RuntimeError(f"Failed to open VideoWriter for {camera_name}: {video_path}")

            video_write_dict[camera_name] = writer
        return video_write_dict
    
    def _create_parquet_writer(self, episode_chunk: int = 0, episode_index: int = 0):
        """
        Initializes the schema for the Parquet file.

        Defines the structure of the Parquet table including observation, action, timestamps, and metadata.
        """
        parquet_schema = pa.schema([
        ('observation.state', pa.list_(pa.float32())),  # NumPy array -> list[float]
        ('action', pa.list_(pa.float32())),              # NumPy array -> list[float]
        ('episode_index', pa.int32()),
        ('frame_index', pa.int32()),
        ('index', pa.int32()),
        ('task_index', pa.int32()),
        ('timestamp', pa.float64())])

        parquet_file_path = os.path.join(
            self.save_path,
            self.config['info']['data_path'].format(episode_chunk=episode_chunk, episode_index=episode_index)
        )
        os.makedirs(os.path.dirname(parquet_file_path), exist_ok=True)
        parquet_writer = pq.ParquetWriter(parquet_file_path, parquet_schema)
        # return parquet_schema, parquet_file_path, parquet_writer
        return parquet_schema, parquet_writer

    def _release_video_writers(self):
        """Release all opened video writers safely."""
        video_writers = getattr(self, 'video_writers', None)
        if not video_writers:
            return
        for writer in video_writers.values():
            writer.close()
            writer.release()
        video_writers = {}
        self.logger.info("All video writers released.")
    
    # def write_parquet_file(self):
    #     """Writes the Parquet file containing the collected data."""
    #     try:
    #         records = list(self.shared_data.episode_parquet_list)
    #         if not records:
    #             self.logger.warning("No episode records to write, parquet will be empty.")
    #             return
    #         df = pd.DataFrame(records)
    #         table = pa.Table.from_pandas(df, schema=self.schema)
    #         self.parquet_writer.write_table(table)
    #     finally:
    #         self.parquet_writer.close()
    #         self.logger.info(f"Successfully wrote Parquet file to: {self.parquet_file_path}")

    def _write_parquet_fun(self):
        """Writes the Parquet file containing the collected data."""
        while self.shared_data.running.value:
            # Write a batch of records to Parquet file every 1 seconds
            time.sleep(1.0)
            with self.parquet_lock:
                if not self.parquet_frame_list:
                    self.logger.warning("No episode records to write, parquet will be empty.")
                    continue
                df = pd.DataFrame(self.parquet_frame_list)
                table = pa.Table.from_pandas(df, schema=self.parquet_schema)
                self.parquet_writer.write_table(table)
                self.logger.info(f"Wrote {len(self.parquet_frame_list)} records to Parquet file.")
                self.parquet_frame_list.clear()
        # Write any remaining records when stopping
        time.sleep(0.1) # make sure all data is recorded.
        with self.parquet_lock:
            if self.parquet_frame_list:
                df = pd.DataFrame(self.parquet_frame_list)
                table = pa.Table.from_pandas(df, schema=self.parquet_schema)
                self.parquet_writer.write_table(table)
                self.logger.info(f"Wrote remaining {len(self.parquet_frame_list)} records to Parquet file before closing.")
                self.parquet_frame_list.clear()
                self.parquet_frame_list = None  # Help GC
        self.parquet_writer.close()
        self.parquet_writer = None
        self.logger.info(f"Successfully wrote Parquet file.")
            

    def _write_meta_files(self, total_episodes: int, total_frames: int, episode_length: int, episode_task_list: list[str]):
        """
        Writes metadata files including info.json, episodes.jsonl, and tasks.jsonl.

        These files contain global dataset statistics, per-episode information, and task mappings respectively.
        """
        try:
            os.makedirs(self.meta_dir, exist_ok=True)

            # Write info.json file (always overwrite to keep metadata in sync)
            info_file_path = os.path.join(self.meta_dir, 'info.json')
            self.config['info']["total_episodes"] = total_episodes
            self.config['info']["total_frames"] = total_frames
            self.config['info']["total_videos"] += len(self.camera_name_list)
            self.config['info']["splits"] = {"test": f"0:{total_episodes-1}"}

            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config['info'].to_dict(), f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"info.json has been written to: {info_file_path}")

            # Write episodes.jsonl file
            episodes_file_path = os.path.join(self.meta_dir, 'episodes.jsonl')
            episodes_content = {
                "episode_index": total_episodes - 1,
                "tasks": episode_task_list,
                "length": episode_length
            }
            with open(episodes_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(episodes_content, ensure_ascii=False) + '\n')

            self.logger.info(f"episodes.jsonl has been written to: {episodes_file_path}")

            # Write tasks.jsonl file
            tasks_file_path = os.path.join(self.meta_dir, 'tasks.jsonl')
            with open(tasks_file_path, 'w', encoding='utf-8') as f:
                for task_language in self.task_language_dict.keys():
                    tasks_content = {
                        "task_index": self.task_language_dict[task_language],
                        "tasks": task_language
                    }
                    f.write(json.dumps(tasks_content, ensure_ascii=False) + '\n')
            self.logger.info(f"tasks.jsonl has been written to: {tasks_file_path}")

        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error(f"Exception in write_meta_files: {e}\n{tb}")
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
    import sys
    print(f"Current working directory: {os.getcwd()}")
    sys.path.append('/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer')
    from conf.client_conf import get_client_config

    save_dir = "/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test"
    config = get_client_config()

    # Initialize writer
    writer = LeRobotDatasetWriter(config.record)

    print("Starting to simulate data writing...")

    start_time = time.time()
    languege_instruction = 'test ok'
    # Simulate writing 100 observations and 200 actions (higher action frequency)
    for i in range(100):
        obs_data = generate_mock_observation()  # ~30Hz
        if i >50:
            languege_instruction = 'test 50'
        writer.add_obs(obs_data,languege_instruction,start_time + i * 0.033)
        if i ==60 :
            print('start save')
            writer.save_writed_data()
            print('saved')
            # time.sleep(6)
        if i ==30 :
            print('start abandoned')
            writer.abandon_record_data()

            print('abandoned')
            # time.sleep(6)
        # Insert multiple actions per observation (~200Hz)
        for j in range(2):
            action_data = generate_mock_action()
            writer.add_action(action_data,start_time + i * 0.033 + j * 0.005)

    print("Waiting for write operations to complete...")
    time.sleep(2)  # Allow thread time to process remaining data
    writer.close()
    writer.writer_process.terminate()
    print("Test completed. Check output files:")
    print(f"- Video files path: {os.path.join(save_dir, 'videos')}")
    print(f"- Parquet file path: {os.path.join(save_dir, 'data')}")
    print(f"- Meta file path: {os.path.join(save_dir, 'meta')}")

    assert os.path.exists(os.path.join(save_dir, 'meta', 'info.json')), "info.json not generated"
    assert os.path.exists(os.path.join(save_dir, 'meta', 'episodes.jsonl')), "episodes.jsonl not generated"
    print("✅ All files verified successfully!")