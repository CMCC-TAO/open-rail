import os
import numpy as np
from PIL import Image
import json
import cv2
import json
import time
from ml_collections import ConfigDict
from collections import deque
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import threading
from multiprocessing import Process, Manager,Queue
from typing import Any, Dict, List, Optional, Union
import copy
import logging
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
# 初始化固定长度队列
MAX_LEN = 900 
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
        # define logger
        self.logger = logging.getLogger(__name__)
        # 设置 logger 的日志级别为 INFO
        self.logger.setLevel(logging.INFO)

        # 创建一个 handler，用于将日志输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)  # 设置 handler 的日志级别为 INFO
        # 定义日志格式并添加到 handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # 将 handler 添加到 logger
        self.logger.addHandler(ch)
        # Configuration and path setup
        self.config = record_config
        self.save_path = self.config["save_path"]
        self.save_meta_path = os.path.join(self.save_path, 'meta')

        # Shared data manager for multiprocessing
        self.manager = Manager()
        self.shared_data = self.manager.Namespace()
        # Shared state and counters
        self.shared_data.counter = self.manager.Value('i', 0)
        self.shared_data.start_write_time = self.manager.Value('b', False)
        self.shared_data.stop = self.manager.Value('b', False)
        self.shared_data.episode_parquet_list = self.manager.list()
        self.shared_data.save_video_path_list = self.manager.list()
        # Task and language information storage
        self.shared_data.episode_task_list = self.manager.list()
        self.shared_data.task_language_dict = self.manager.dict()
        self.lock = self.manager.Lock()

        # Shared Queue
        self.record_queue = Queue()
        

        # Check directory and update config if necessary
        self.checkdir_and_update_config()
        # compute episode_chunk
        self.total_frames = self.config['info']['total_frames']
        self.shared_data.counter.value = self.config['info']['total_episodes']
        self.episode_chunk = self.shared_data.counter.value // self.config.info.chunks_size
        # Extract camera-related keys from features in the config
        self.camera_name_list = []
        for key in self.config["info"]["features"].keys():
            if "cam" in key:
                self.camera_name_list.append(key)

        self.action_shape = self.config["info"]["features"]["action"]['shape'][0]
        self.state_shape = self.config["info"]["features"]["observation.state"]['shape'][0]
        # Time obs deques
        self.obs_time = deque(maxlen=MAX_LEN)

        # Action recording queues
        self.action_list = deque(maxlen=10)
        self.action_time = deque(maxlen=10)

        # Parquet file writing setup
        # Initialize parquet content : self.schema
        self.init_parquet_content()
        self.parquet_savepath = os.path.join(
            self.save_path,
            self.config.info.data_path.format(episode_chunk=self.episode_chunk, episode_index=self.shared_data.counter.value)
        )
        os.makedirs(os.path.dirname(self.parquet_savepath), exist_ok=True)
        self.parquet_writer = pq.ParquetWriter(self.parquet_savepath, self.schema)

        self.record_obs_executor = ThreadPoolExecutor(max_workers=2)
        self.record_action_executor = ThreadPoolExecutor(max_workers=4)

        # Video writing setup
        self.save_video_path = os.path.join(self.save_path, 'videos', f'chunk-{self.episode_chunk:03d}')

        

        # Writer process initialization
        self.writer_thread = Process(target=self.write, daemon=True)
        try:
            self.writer_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start writer_thread: {e}")
    def async_write_obs(self,observations: Dict[str, np.ndarray], language_instruction: str, timestamp: int | float):
        """
        Asynchronously writes observation data into the dataset.

        Args:
            observations (dict):A dictionary containing observation with the following keys:
                - 'cam.*': np.ndarray,
                - 'obs.state': np.ndarray
            language (str): The language instruction associated with the observation.
            time_now (int | float): The current timestamp.
        """
        self.record_obs_executor.submit(self.add_obs, observations, language_instruction,timestamp)

    def async_write_action(self,action: np.ndarray, timestamp: int | float) -> None:
        """
        Asynchronously writes action data into the dataset.

        Args:
            action (np.ndarray): A dictionary containing action data from the environment.
        """
        self.record_action_executor.submit(self.add_action, action, timestamp)
    def add_obs(self, state: Dict[str, np.ndarray], language_instruction: str, timestamp: int | float) -> None:
        """
        Process and store observation data including camera images, robot state, and time frame.

        Args:
            state (Dict[str, np.ndarray]): Dictionary containing observation data with the following keys:
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
        state['language_instruction'] = language_instruction
        # Check if the timestamp is greater than the last recorded timestamp
        if len(self.obs_time) > 0:
            assert self.obs_time[-1] < timestamp, \
                f"Observation timestamp is not increasing: previous={self.obs_time[-1]}, current={timestamp}"
        #check state shape 
        if state['obs.state'].shape[0] != self.state_shape:
            self.logger.warning(f"obs shape {state['obs.state'].shape[0]} is not correct, config shape is {self.state_shape} , add 0 to the action")
            assert state['obs.state'].shape[0] <= self.state_shape, \
            f"obs shape {state['obs.state'].shape[0]} is bigger than config shape {self.state_shape}"
            action = np.concatenate([action, np.zeros(self.state_shape-state['obs.state'].shape[0])], axis=0)
        if self.shared_data.start_write_time.value:
            self.obs_time.append(timestamp)
            with self.lock:
                if not self.action_list:
                    # Handle case where action_list is empty, avoiding pop() error
                    self.logger.warning("Action list is empty. No action to pop.")
                    return
                self.record_queue.put([state, self.action_list.pop()])
                # print(f"Write successful: {timestamp}")

    def add_action(self, action: np.ndarray, timestamp: int | float) -> None:
        """
        Process and store the action data along with its timestamp.

        Args:
            action (np.ndarray): The action data to be stored, typically representing joint torques or target positions.
            timestamp (int): The timestamp associated with this action.

        Raises:
            AssertionError: If the provided timestamp is not strictly increasing compared to the last recorded one.
        """
        if len(self.action_list) == 0 and not self.shared_data.start_write_time.value:
            self.shared_data.start_write_time.value = True

        if len(self.action_time) > 0:
            assert self.action_time[-1] < timestamp, \
                f"Action timestamp is not increasing: previous={self.action_time[-1]}, current={timestamp}"

        #check action shape 
        if action.shape[0]!= self.action_shape:
            # self.logger.warning(f"Action shape {action.shape[0]} is not correct, config shape is {self.action_shape} , add 0 to the action")
            assert action.shape[0] <= self.action_shape,\
            f"Action shape {action.shape[0]} is bigger than config shape {self.action_shape}"
            action = np.concatenate([action, np.zeros(self.action_shape-action.shape[0])], axis=0)
        self.action_list.append(action)
        self.action_time.append(timestamp)

    def write(self):
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
        self.logger.info("waiting for record_queue")
        self.videos_writer = self.gener_video_write_dict()
        # copy task dict
        self.shared_data.last_task_language_dict = self.copy_shared_data_dict(self.shared_data.task_language_dict)
        frame_index = 0
        try:
            while not self.shared_data.stop.value:
                # Skip if queue is empty
                if not self.shared_data.start_write_time.value:
                    time.sleep(0.01)
                    continue
                
                # Get state and action data from queue
                with self.lock:
                    if self.record_queue.empty():
                        time.sleep(0.01)
                        continue
                    one_step_state_and_action_list = self.record_queue.get(timeout=0.5)
                # self.logger.info(f"Get one step state and action from queue")
                step_state, step_action = one_step_state_and_action_list[0], one_step_state_and_action_list[1]
                step_language = step_state['language_instruction']
                
                # Track new language instructions per episode
                if step_language not in self.shared_data.episode_task_list:
                    self.shared_data.episode_task_list.append(step_language)
                
                # Assign task index based on unique language instruction
                if step_language not in self.shared_data.task_language_dict.keys():
                    step_task_index = len(self.shared_data.task_language_dict.keys())
                    self.shared_data.task_language_dict[step_language] = step_task_index
                else:
                    step_task_index = self.shared_data.task_language_dict[step_language]
                
                # Write image frames to video files
                for camera_name in self.camera_name_list:
                    start_time= time.perf_counter()
                    if self.camera_shape_dict[camera_name] != step_state[camera_name].shape:
                        self.logger.warning(f'{camera_name} shape mismatch')
                        self.logger.warning(f"{camera_name} current shape :{step_state[camera_name].shape}")
                        self.logger.warning(f"{camera_name} save MP4 shape :{self.camera_shape_dict[camera_name]}")
                    # print(f"check using time : {(time.perf_counter()-start_time)*1000} ms")
                    self.videos_writer[camera_name].write(step_state[camera_name])
                    # print(f"{camera_name} shape :{step_state[camera_name].shape}")
                # Construct record dictionary for Parquet file
                record = {
                    'observation.state': step_state['obs.state'].tolist(),
                    'action': step_action.tolist(),
                    'episode_index': self.shared_data.counter.value,
                    'frame_index': frame_index,
                    'index': self.total_frames+frame_index+1,
                    'task_index': step_task_index,
                    'timestamp': 1/30 * frame_index,  # Fixed frame rate assumption
                }
                with self.lock:
                    self.shared_data.episode_parquet_list.append(record)
                
                # Update counters
                frame_index += 1
                # print('Write successful ——————————————————')
            
            self.logger.info('write process stopped!!! ')
            # print(f'self.shared_data.task_language_dict {self.shared_data.task_language_dict}')
        
        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
            self.release_writers()
        
        except Exception as e:
            self.logger.error(f"Writing thread exited with exception: {e}")
            self.release_writers()
        
        finally:
            self.logger.info("Writing thread exited.")
            self.release_writers()

    def end_write(self):
        """
        Finalizes the data writing process based on user confirmation.

        Prompts the user to choose whether to save ('y') or discard ('n') the collected data.
        If saving:
            - Saves the video files
            - Converts buffered Parquet data to a DataFrame and writes it to disk
            - Updates metadata files (info.json, episodes.jsonl, tasks.jsonl)
        If discarding:
            - Deletes any partially written video files
            - Deletes the Parquet file if it exists

        The method blocks until valid user input is received. It ensures proper cleanup of resources
        and maintains data consistency based on user decision.
        
        Raises:
            ValueError: If invalid input is provided repeatedly
        """
        while True:
            user_input = input("Please enter 'y' to save data, or 'n' to discard: ").strip().lower()
            
            if user_input == 'y':
                self.logger.info("Video has been saved to: {}".format(self.save_video_path))
                
                # Write to parquet file
                self.write_parquet_file()
                # Write meta files
                self.write_meta_files()
                break
                
            elif user_input == 'n':
                for path in self.shared_data.save_video_path_list:
                    print(f"path {path}")
                    if os.path.exists(path):
                        print(f"删除文件 {path}")
                        os.remove(path)
                if os.path.exists(self.parquet_savepath):
                    os.remove(self.parquet_savepath)
                self.logger.info("Saved video files have been deleted.")
                break
                
            else:
                self.logger.warning("Invalid input. Please try again.")
    
    def copy_shared_data_dict(self,input_dict):
        """
        
        """
        output_dict = self.manager.dict()
        for key, value in input_dict.items():
            output_dict[key] = value
        return output_dict
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
        self.shared_data.stop.value = True
        time.sleep(1)
        # print(f"[Main] Writer alive? {self.writer_thread.is_alive()}")
        self.record_obs_executor.shutdown(wait=True)
        self.record_action_executor.shutdown(wait=True)
        if self.writer_thread.is_alive():
            self.writer_thread.join(timeout=2)
            if self.writer_thread.is_alive():
                self.logger.warning("Writer thread still alive after timeout, terminating...")
                self.writer_thread.terminate()
                self.writer_thread.join()

        # self.shared_data.counter.value += 1
        self.episode_length = len(self.shared_data.episode_parquet_list)
        self.total_frames += len(self.shared_data.episode_parquet_list)

        self.end_write()

        # 清理资源
        if self.record_queue:
            self.record_queue.close()
            self.record_queue.join_thread()

        if self.manager:
            self.manager.shutdown()

        self.logger.info("LeRobotDatasetWriter closed successfully.")
        
    
    def save_writed_data(self):
        """
        Gracefully shuts down the writer and finalizes data writing.

        This method signals the writer thread to stop by setting the 'stop' flag,
        releases all video writers, increments the episode counter, updates the total
        number of frames, and triggers the finalization process (`end_write`) to save
        all buffered data to disk.

        Should be called when ending data collection to ensure all data is flushed
        and resources are properly released.
        """
        # stop record
        self.shared_data.stop.value = True
        time.sleep(1)
        self.writer_thread.join(timeout=1)
        ## The relevant variables increase

        self.episode_length = len(self.shared_data.episode_parquet_list) 
        self.total_frames += len(self.shared_data.episode_parquet_list)
        # Write to parquet file
        self.write_parquet_file()
        # Write meta files
        self.write_meta_files()
        # clean record data
        self.clean_record_data()
        self.shared_data.counter.value += 1
        ### new write data
        # new parquet file
        self.parquet_savepath = os.path.join(
            self.save_path,
            self.config.info.data_path.format(episode_chunk=self.episode_chunk, episode_index=self.shared_data.counter.value)
        )
        self.parquet_writer = pq.ParquetWriter(self.parquet_savepath, self.schema)
        # Writer process initialization
        self.shared_data.stop.value = False
        self.shared_data.save_video_path_list = self.manager.list()
        self.writer_thread = Process(target=self.write, daemon=True)
        try:
            self.writer_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start writer_thread: {e}")
        time.sleep(0.5)
    def abandon_record_data(self):
        """
        Abandon the current recording data and start a new one.
        """
        self.shared_data.stop.value = True
        
        self.writer_thread.join(timeout=1)
        # print("Abandon the current recording data and start a new one.")
        # clean record data
        self.logger.info("Abandon the current recording data and start a new one.")
        self.clean_record_data()
        
        # modify task language equals last task language
        # print(f'last task language: {self.shared_data.last_task_language_dict}')
        self.shared_data.task_language_dict = self.copy_shared_data_dict(self.shared_data.last_task_language_dict)
        # new parquet file
        self.parquet_savepath = os.path.join(
            self.save_path,
            self.config.info.data_path.format(episode_chunk=self.episode_chunk, episode_index=self.shared_data.counter.value)
        )
        self.parquet_writer = pq.ParquetWriter(self.parquet_savepath, self.schema)
        # Writer process initialization
        self.shared_data.stop.value = False
        self.shared_data.save_video_path_list = self.manager.list()
        # print("self.shared_data.counter.value",self.shared_data.counter.value)
        self.writer_thread = Process(target=self.write, daemon=True)
        try:
            self.writer_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start writer_thread: {e}")
        time.sleep(0.5)

    def clean_record_data(self):
        """ 
        Clean up the record data.
        """
        self.shared_data.episode_parquet_list = self.manager.list()
        self.obs_time.clear()
        self.action_list.clear()
        self.action_time.clear()
        # clean episode task list
        self.shared_data.episode_task_list = self.manager.list()
        ## clean queue
        self.record_queue = Queue()
        self.logger.info("cleaning data finished")

    def checkdir_and_update_config(self):
        """
        Checks whether the directory `self.save_meta_path` exists.

        If it does not exist, creates the directory along with related data and video paths.
        If it exists but is empty, returns early.
        If it exists and contains required files (info.json, episodes.jsonl, tasks.jsonl),
        updates the configuration using these files. Otherwise, raises an error due to missing files.

        Raises:
            AssertionError: If any of the required files are missing in the existing directory.
        """
        
        # Case 1: Directory does not exist
        if not os.path.exists(self.save_meta_path):
            # Set up default subdirectory paths
            self.save_data_path = os.path.join(self.save_path, 'data', 'chunk-000')
            self.save_video_path = os.path.join(self.save_path, 'videos', 'chunk-000')

            # Create directories
            os.makedirs(self.save_meta_path, exist_ok=True)
            os.makedirs(self.save_data_path, exist_ok=True)
            os.makedirs(self.save_video_path, exist_ok=True)
            self.total_frames = 0
            self.episode_chunk = 0

            self.logger.info(f"{self.save_meta_path} not exists, create it")
            return

        # Case 2: Directory exists but is empty
        elif len(os.listdir(self.save_meta_path)) == 0:
            return

        # Check for required files
        required_files = ['info.json', 'episodes.jsonl', 'tasks.jsonl']
        missing_files = []

        for filename in required_files:
            file_path = os.path.join(self.save_meta_path, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        # Raise error if any required file is missing
        if missing_files:
            self.logger.error(f"{self.save_meta_path} is missing the following required files: {', '.join(missing_files)}")
            assert False, "Missing required files"
            return

        # Load info.json and update dataset info
        info_file_path = os.path.join(self.save_meta_path, 'info.json')
        self.from_file_update_dataset_info(info_file_path)

        # Load tasks.jsonl and update task languages
        task_file_path = os.path.join(self.save_meta_path, 'tasks.jsonl')
        self.from_file_update_task_languages(task_file_path)
    def from_file_update_dataset_info(self,file_path: str) -> None:
        """
        Updates the dataset info using the provided JSON file.
        """
        # Open the specified JSON file and load its contents
        with open(file_path, 'r') as file:
            data = json.loads(file.read())
        
        # Update the dataset info in the config using the loaded JSON data
        self.config["info"] = ConfigDict(data, allow_dotted_keys=True)

        # Print a success message indicating that the meta files have updated the config
        self.logger.info("update self.config info success")
    
    def from_file_update_task_languages(self,file_path: str) -> None:
        """
        Updates the task-language mapping using the provided JSONL file.
        """
        with open(file_path, 'r') as file:
            for line in file:
                data = json.loads(line)
                task_index = data['task_index']
                task_name = data['tasks'] 
                if task_name not in self.shared_data.task_language_dict:
                    self.shared_data.task_language_dict[task_name] = task_index
            # self.logger.info(self.shared_data.task_language_dict)
    def gener_video_write_dict(self) -> Dict[str, Any]:
        """
        Generates video writers for each camera stream.

        Creates OpenCV VideoWriter objects for each camera specified in the configuration.

        Returns:
            dict: A dictionary mapping camera names to their respective VideoWriter objects.
        """
        filename = f"{'episode'}_{self.shared_data.counter.value:06d}.{'mp4'}"
        video_write_dict = {}
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.camera_shape_dict = {}
        for camera_name in self.camera_name_list:
            shape_list = self.config['info']["features"][camera_name]["shape"]
            height, width = shape_list[0],shape_list[1]
            os.makedirs(os.path.join(self.save_video_path, camera_name), exist_ok=True)
            video_path = os.path.join(self.save_video_path, camera_name, filename)
            self.shared_data.save_video_path_list.append(video_path)
            self.camera_shape_dict[camera_name] = tuple(shape_list)
            video_write_dict[camera_name] = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
        return video_write_dict
    
    def init_parquet_content(self):
        """
        Initializes the schema for the Parquet file.

        Defines the structure of the Parquet table including observation, action, timestamps, and metadata.
        """
        self.schema = pa.schema([
        ('observation.state', pa.list_(pa.float32())),  # NumPy array -> list[float]
        ('action', pa.list_(pa.float32())),              # NumPy array -> list[float]
        ('episode_index', pa.int32()),
        ('frame_index', pa.int32()),
        ('index', pa.int32()),
        ('task_index', pa.int32()),
        ('timestamp', pa.float64())
         ])
    def release_writers(self):
        """
        Initializes the schema for the Parquet file.

        Defines the structure of the Parquet table including observation, action, timestamps, and metadata.
        """
        for writer in self.videos_writer.values():
            writer.release()
        self.logger.info("All video writers released.")
    
    def write_parquet_file(self):
        """ Writes the Parquet file containing the collected data.   """
        print('parquet',list(self.shared_data.episode_parquet_list)[0])
        try:
            df = pd.DataFrame(list(self.shared_data.episode_parquet_list))
            # print(df)
            table = pa.Table.from_pandas(df, schema=self.schema)
            # Write to parquet file
            self.parquet_writer.write_table(table)
        finally:
            self.parquet_writer.close()
            self.logger.info(f"Successfully wrote Parquet file to: {self.parquet_savepath}")
            

    def write_meta_files(self):
        """
        Writes metadata files including info.json, episodes.jsonl, and tasks.jsonl.

        These files contain global dataset statistics, per-episode information, and task mappings respectively.
        """
        # Write info.json file
        info_file_path = os.path.join(self.save_meta_path, 'info.json')
        self.config['info']["total_episodes"] = self.shared_data.counter.value + 1
        self.config['info']["total_frames"] = self.total_frames
        self.config['info']["total_videos"] += len(self.camera_name_list)
        self.config['info']["splits"] = {"test": f"0:{self.shared_data.counter.value }"}

        with open(info_file_path, 'w') as f:
            json.dump(self.config['info'].to_dict(), f, indent=2, default=str)

        self.logger.info(f"info.json has been written to: {info_file_path}")

        # Write episodes.jsonl file
        episodes_file_path = os.path.join(self.save_meta_path, 'episodes.jsonl')
        episodes_content = {
            "episode_index": self.config['info']["total_episodes"] - 1,
            "tasks": list(self.shared_data.episode_task_list),
            "length": self.episode_length
        }
        # print(f'episodes_content: {episodes_content}')
        with open(episodes_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(episodes_content, ensure_ascii=False) + '\n')

        self.logger.info(f"episodes.jsonl has been written to: {episodes_file_path}")

        # Write tasks.jsonl file
        tasks_file_path = os.path.join(self.save_meta_path, 'tasks.jsonl')
        # print(self.shared_data.task_language_dict)
        with open(tasks_file_path, 'w', encoding='utf-8') as f:
            for task_language in self.shared_data.task_language_dict.keys():
                tasks_content = {
                    "task_index": self.shared_data.task_language_dict[task_language],
                    "tasks": task_language
                }
                f.write(json.dumps(tasks_content, ensure_ascii=False) + '\n')

        self.logger.info(f"tasks.jsonl has been written to: {tasks_file_path}")
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
    writer.writer_thread.terminate()
    print("Test completed. Check output files:")
    print(f"- Video files path: {os.path.join(save_dir, 'videos')}")
    print(f"- Parquet file path: {os.path.join(save_dir, 'data')}")
    print(f"- Meta file path: {os.path.join(save_dir, 'meta')}")

    assert os.path.exists(os.path.join(save_dir, 'meta', 'info.json')), "info.json not generated"
    assert os.path.exists(os.path.join(save_dir, 'meta', 'episodes.jsonl')), "episodes.jsonl not generated"
    print("✅ All files verified successfully!")
    # sys.exit(0)