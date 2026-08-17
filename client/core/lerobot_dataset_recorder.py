import os
import re
import json
import cv2
import time
import logging
import threading
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from queue import Empty
from pathlib import Path
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue
from typing import Any, Dict, List, Optional, Union, Tuple
from client.utils.util import run_time_decorator

class LeRobotDatasetRecorder:
    """
    A class to manage writing robotic observation and action data to disk in a structured format.

    This class handles the synchronization, storage, and serialization of high-frequency robot sensor data,
    including images, states, actions, and associated metadata. It supports multiprocessing for efficient I/O
    operations and writes data into Parquet files along with corresponding video recordings.
    """

    def __init__(self, lerobot_config: ConfigDict, task: Optional[str] = None) -> None:
        """
        Initializes the DataRecordManager instance with the given configuration.

        Sets up directories, loads or initializes metadata, prepares video writers, and starts
        the writer process for asynchronous disk writing.

        Args:
            lerobot_config (dict): LeRobot configuration dictionary in record conf.
                                For more information, see ./conf/save_conf.py
        """
        # Define logger
        self.logger = logging.getLogger(__name__)
        self.config = lerobot_config
        # print(f"Debug: record_config: {self.config}")
        self.task_language_dict = {}

        # Runtime cache for writer-side episode metadata.
        self._save_path: Optional[str] = None
        self._meta_dir: Optional[str] = None
        self._data_dir: Optional[str] = None
        self._dataset_fps: int = 30
        self._episode_length_map: Dict[int, int] = {}
        self._writer_episode_records: List[Dict[str, Any]] = []

        # Queue-based browse sync between main process and writer process.
        self._episode_records_for_browse: List[Dict[str, Any]] = []
        self._episode_records_for_share: Queue = Queue()
        self._task_dir_for_browse: Optional[str] = None
        self._episode_record_crud_queue: Queue = Queue()
        self._episode_record_crud_thread: Optional[threading.Thread] = None
        self._episode_record_crud_stop_event = threading.Event()

        self._parse_config(lerobot_config)
        # self.record_executor = ThreadPoolExecutor(max_workers=1) # max_workers must be 1 to ensure sequence of recording

    def _check_meta_path_and_dir(self, save_path: str) -> bool:
        """
        Check and create the metadata directory if it doesn't exist, then verify required meta files.

        This method performs the following operations:
        1. Constructs the metadata directory path by joining save_path with 'meta'
        2. Creates the directory if it doesn't exist
        3. Logs the directory creation if performed
        4. Checks for required metadata files if directory already exists

        Args:
            save_path (str): The base path where metadata directory should be located

        Returns:
            bool: False if directory was created, otherwise returns result of _check_required_meta_files() which indicates whether all required meta files exist.

        Notes:
            Handles special characters in paths including \t, \r, \n
            Uses exist_ok=True to prevent race conditions
        """
        if not os.path.exists(self._meta_dir):
            os.makedirs(self._meta_dir, exist_ok=True)
            self.logger.info(f"{self._meta_dir} not exists, create it")
            return False
        return self._check_required_meta_files()

    def _check_required_meta_files(self, required_files: List[str] = ['info.json', 'episodes.jsonl', 'tasks.jsonl']) -> bool:
        """
        Check if the required meta files exist in the meta directory. Called in writer process.

        Args:
            required_files (List[str]): A list of required filenames to check for. 
                                        Defaults to ['info.json', 'episodes.jsonl', 'tasks.jsonl'].

        Returns:
            bool: True if all required files exist, False otherwise.

        Note:
            If any files are missing, a warning message is logged listing the missing files.
        """
        # Check for required files
        missing_files = []

        for filename in required_files:
            file_path = os.path.join(self._meta_dir, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        # Raise error if any required file is missing
        if missing_files:
            self.logger.warning(f"{self._meta_dir} is missing the following required files: {', '.join(missing_files)}")
            # assert False, "Missing required meta files."
            return False
        else:
            self.logger.info(f"{self._meta_dir} has the following required files: {', '.join(required_files)}")
            return True

    def set_task(self, save_path: str) -> Tuple[int, int, int, int, int]:
        """
        Set up a new task with the specified save path and initialize configuration. Called in writer process.

        This method performs the following operations:
        1. Sets the save path for the task
        2. Initializes task-specific paths
        3. Checks for existing metadata files
        4. Updates configuration either from metadata or with default values
        5. Refreshes writer-side cache for queue-based synchronization

        Args:
            save_path (str): The directory path where task data will be saved.
                            The path may contain special characters:
                            - \\t: Tab character
                            - \\r: Carriage return
                            - \\n: Newline character

        Returns:
            Tuple[int, int, int, int]: A tuple containing:
                - total_frames (int): Total number of frames in the task
                - total_videos (int): Total number of videos in the task
                - total_episodes (int): Total number of episodes in the task
                - chunks_size (int): Size of chunks for data processing (default 1000)
                - episode_index (int): Index for recording next episode (default 0)

        Side Effects:
            - Modifies self._save_path
            - Updates self.config with task parameters
            - Reloads browse state for synchronization
        """
        if self._set_task_path(save_path=save_path):
            meta_required_file_exists = self._check_meta_path_and_dir(save_path=save_path)
            if meta_required_file_exists:
                self._update_config_from_meta_file()
            else:
                self._update_config_from_init()

            # Refresh writer-side cache for subsequent queue-based sync.
            self._reload_browse_state()
            self._sync_episode_records_for_share(self._writer_episode_records)
        # total_frames, total_videos, total_episodes, chunks_size = self.config["total_frames"], self.config["total_videos"], self.config["total_episodes"], self.config['chunks_size']
        # self.logger.info(f"total_frames: {total_frames}, total_videos: {total_videos}, total_episodes: {total_episodes}, chunks_size: {chunks_size}")
        return self.config["total_frames"], self.config["total_videos"], self.config["total_episodes"], self.config['chunks_size'], self.config['episode_index']

    def _set_task_path(self, save_path: str) -> bool:
        """
        Set the paths for saving task-related data and metadata.
        
        Args:
            save_path (str): The base directory path where all task-related 
                folders will be created.
                
        Returns:
            bool: True if save_path is new and False if save_path is same with the existing one.:
        Note:
            This method initializes two subdirectories path string under the save_path:
            1. 'data' directory for storing task data
            2. 'meta' directory for storing metadata
            
            The paths are stored as instance variables for later use.
        """
        new_path = False
        if self._save_path is None or self._save_path != save_path:
            new_path = True
            self._save_path = save_path
            self._data_dir = os.path.join(save_path, 'data')
            self._meta_dir = os.path.join(save_path, 'meta')
        return new_path

    def _reload_browse_state(self) -> None:
        """Reload writer-side dataset metadata and episode records."""
        self._dataset_fps = int(self.config.get("fps", 30) or 30)
        self._episode_length_map = self._load_episode_length_map()
        self._writer_episode_records = self._build_episode_records()

    def _load_dataset_info(self) -> Dict[str, Any]:
        """
        Load dataset information from a JSON file named info.json.
        
        This method attempts to read and parse a JSON file containing metadata about the dataset. If the file doesn't exist or cannot be parsed, it returns an empty dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the dataset information if successfully loaded, otherwise an empty dictionary.
        
        Note:
            Any exceptions during file parsing are caught and logged as warnings, with an empty dictionary returned in such cases.
        """
        info_path = os.path.join(self._meta_dir, "info.json")
        if not os.path.exists(info_path):
            return {}
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self.logger.warning(f"Failed to parse info.json: {info_path}", exc_info=True)
            return {}

    def _load_episode_length_map(self) -> Dict[int, int]:
        episodes_path = os.path.join(self._meta_dir, "episodes.jsonl")
        mapping: Dict[int, int] = {}
        if not os.path.exists(episodes_path):
            return mapping
        try:
            with open(episodes_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s:
                        continue
                    data = json.loads(s)
                    ep_idx = int(data.get("episode_index", -1))
                    ep_len = int(data.get("length", -1))
                    if ep_idx >= 0 and ep_len >= 0:
                        mapping[ep_idx] = ep_len
        except Exception:
            self.logger.warning("Failed to parse episodes.jsonl: %s", episodes_path, exc_info=True)
        return mapping

    @staticmethod
    def _parse_episode_id(episode_id: str) -> tuple[int, int]:
        m = re.fullmatch(r"chunk-(\d{3})/episode_(\d{6})", str(episode_id or "").strip())
        if not m:
            raise ValueError(f"Invalid episode id: {episode_id}")
        return int(m.group(1)), int(m.group(2))

    def _parquet_num_rows(self, parquet_path: Path) -> int:
        try:
            return int(pq.ParquetFile(parquet_path).metadata.num_rows)
        except Exception:
            return 0

    def _video_exists(self, chunk_id: int, episode_index: int, video_key: str) -> bool:
        video_fmt = self.config.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )
        rel = video_fmt.format(
            episode_chunk=chunk_id,
            episode_index=episode_index,
            video_key=video_key,
        )
        return os.path.exists(os.path.join(self._save_path, rel))

    def _build_episode_records(self) -> List[Dict[str, Any]]:
        if self._data_dir is None or (not os.path.exists(self._data_dir)):
            return []

        pattern = re.compile(r"chunk-(\d{3})/episode_(\d{6})\.parquet$")
        meta_ok = all(os.path.exists(os.path.join(self._meta_dir, name)) for name in ("info.json", "episodes.jsonl", "tasks.jsonl"))
        records: List[Dict[str, Any]] = []

        for parquet_path in Path(self._data_dir).rglob("episode_*.parquet"):
            rel_data = parquet_path.relative_to(self._data_dir).as_posix()
            m = pattern.search(rel_data)
            if not m:
                continue

            cur_chunk_id = int(m.group(1))
            episode_index = int(m.group(2))
            frames = int(self._episode_length_map.get(episode_index, self._parquet_num_rows(parquet_path)))
            # duration_sec = round((frames / self._dataset_fps), 1) if self._dataset_fps > 0 else 0.0
            videos_ok = all(self._video_exists(cur_chunk_id, episode_index, key) for key in self.camera_name_list)

            records.append(
                self._build_episode_record(
                    chunk_id=cur_chunk_id,
                    episode_index=episode_index,
                    frames=frames,
                    complete=bool(meta_ok and videos_ok)
                    )
                )
            # records.append({
            #     "id": f"chunk-{cur_chunk_id:03d}/episode_{episode_index:06d}",
            #     "name": f"episode_{episode_index:06d}",
            #     "chunk": cur_chunk_id,
            #     "chunk_str": f"{cur_chunk_id:03d}",
            #     "episode_index": episode_index,
            #     "frames": frames,
            #     "duration_sec": duration_sec,
            #     "parquet_relpath": str(parquet_path.relative_to(self._save_path)),
            #     "complete": bool(meta_ok and videos_ok),
            # })

        records.sort(key=lambda x: x["episode_index"], reverse=True)
        return records

    def _build_episode_record(self, chunk_id: int, episode_index: int, frames: int, complete: bool) -> Dict[str, Any]:
        duration_sec = round((max(0, int(frames)) / self._dataset_fps), 1) if self._dataset_fps > 0 else 0.0
        parquet_relpath = self.config['data_path'].format(episode_chunk=chunk_id, episode_index=episode_index)
        return {
            "id": f"chunk-{chunk_id:03d}/episode_{episode_index:06d}",
            "name": f"episode_{episode_index:06d}",
            "chunk": int(chunk_id),
            "chunk_str": f"{int(chunk_id):03d}",
            "episode_index": int(episode_index),
            "frames": int(max(0, int(frames))),
            "duration_sec": duration_sec,
            "parquet_relpath": str(parquet_relpath),
            "complete": bool(complete),
        }

    def _upsert_writer_episode_record(self, record: Dict[str, Any]) -> None:
        """
        Insert or replace one episode record in browse cache.
        
        This method checks if an episode with the same ID already exists in the cache.
        If found, it replaces the existing record with the new one. If not found,
        it appends the new record to the cache. Finally, it sorts all records by episode index in descending order.
        
        Args:
            record (Dict[str, Any]): The episode record to be inserted or replaced. Must contain an 'id' field and optionally an 'episode_index' field for sorting.
        
        Returns:
            None
        """
        target_id = str(record.get("id", ""))
        replaced = False
        for idx, item in enumerate(self._writer_episode_records):
            if str(item.get("id", "")) == target_id:
                self._writer_episode_records[idx] = record
                replaced = True
                break
        if not replaced:
            self._writer_episode_records.append(record)
        self._writer_episode_records.sort(key=lambda x: int(x.get("episode_index", -1)), reverse=True)

    def _clear_episode_share_queue(self):
        """
        Clear stale shared browse records before loading a new task. Called in main process.
        
        This method empties the queue of episode records that are shared between processes.
        It handles both normal queue clearing and edge cases where the queue might be in an inconsistent state.
        
        Special characters handled:
        - \t (tab)
        - \r (carriage return)
        - \n (newline)
        
        Raises:
            Exception: If queue clearing fails, attempts alternative clearing method
        """
        try:
            while not self._episode_records_for_share.empty():
                try:
                    self._episode_records_for_share.get_nowait()
                except Empty:
                    break
        except Exception:
            try:
                while True:
                    self._episode_records_for_share.get_nowait()
            except Exception:
                self.logger.info("Episode browse share queue cleared.")

    def _sync_episode_records_for_browse(
        self,
        timeout_s: float = 0.1,
        max_empty_retries: int = 5,
        clear: bool = False,
        append: bool = False,
    ) -> None:
        """Synchronize episode records for browsing purposes.
        
        This method continuously retrieves episode records from a shared queue and updates the browse records accordingly. It handles both dictionary records for insertion update and string records for deletion.
        
        Args:
            timeout_s (float, optional): Timeout in seconds for queue operations. Defaults to 0.1.
            max_empty_retries (int, optional): Maximum number of consecutive empty queue retrievals before breaking. Defaults to 5.
            clear (bool, optional): Whether to clear existing browse records before synchronization. Defaults to False.
            append (bool, optional): Whether to append records instead of upserting. If True, appends dictionary records. If False, upserts records. Defaults to False.
        
        Returns:
            None
        
        Note:
            Records are sorted by episode_index in descending order after synchronization. The method breaks after max_empty_retries consecutive empty queue retrievals or if an exception occurs during processing.
        """
        if clear:
            self._episode_records_for_browse.clear()

        empty_count = 0
        while True:
            try:
                payload = self._episode_records_for_share.get(timeout=timeout_s)
                empty_count = max_empty_retries-2

                if isinstance(payload, dict):
                    if append:
                        self._episode_records_for_browse.append(payload)
                    else:
                        self._upsert_episode_browse_record(payload)
                elif isinstance(payload, str): # episode_id
                    self._delete_episode_browse_record(payload)
            except Empty:
                empty_count += 1
                if empty_count >= max_empty_retries:
                    break
            except Exception as e:
                self.logger.exception(f"Failed to sync episode records for browse: {e}")
                break

        self._episode_records_for_browse.sort(key=lambda x: int(x.get("episode_index", -1)), reverse=True)

    def _upsert_episode_browse_record(self, record: Dict[str, Any]) -> None:
        """
        Upsert (insert or update) an episode browse record in the internal list.
        
        This method checks if a record with the same ID already exists in the list.
        If found, it replaces the existing record with the new one.
        If not found, it appends the new record to the list.
        
        Args:
            record (Dict[str, Any]): The episode record to be inserted or updated. Must contain an 'id' field for comparison.
        
        Returns:
            None
        """
        target_id = str(record.get("id", ""))
        replaced = False
        for idx, item in enumerate(self._episode_records_for_browse):
            if str(item.get("id", "")) == target_id:
                self._episode_records_for_browse[idx] = record
                replaced = True
                break
        if not replaced:
            self._episode_records_for_browse.append(record)

    def _delete_episode_browse_record(self, record_id: str) -> None:
        """Delete one episode record from browse cache by record id."""
        for i in range(len(self._episode_records_for_browse) - 1, -1, -1):
            if str(self._episode_records_for_browse[i].get("id", "")) == str(record_id):
                del self._episode_records_for_browse[i]
                return

    def _sync_episode_records_for_share(self, targets: Union[List[Dict[str, Any]], Dict[str, Any], str]) -> None:
        """Publish episode browse records to shared queue for main-process sync."""
        if targets is None:
            return

        if isinstance(targets, list):
            for item in targets:
                if isinstance(item, dict):
                    self._episode_records_for_share.put(item)
                elif isinstance(item, str):
                    self._episode_records_for_share.put(item)
            return

        if isinstance(targets, dict):
            self._episode_records_for_share.put(targets)
            return

        if isinstance(targets, str):
            self._episode_records_for_share.put(targets)
            return

        self.logger.warning(f"Unsupported target type for episode browse sync: {type(targets)}")

    def _is_need_load(self, save_path: str) -> bool:
        """
        Check if the task directory needs to be loaded based on the current and new save paths. Called in main process.

        This method compares the current task directory for browsing with the provided save path. If they differ or if no directory is currently set, it marks that loading is needed and updates the current task directory. The result is logged before returning.

        Args:
            save_path (str): The path to the directory that needs to be checked for loading.

        Returns:
            bool: True if the task directory needs to be loaded, False otherwise.

        Note:
            This method handles special characters in paths including \t, \r, or \n.
        """
        need_load = False
        if self._task_dir_for_browse is None or self._task_dir_for_browse != save_path:
            need_load = True
            self._task_dir_for_browse = save_path
        self.logger.info(f"Episode directory: {self._task_dir_for_browse}, need_load: {need_load}")
        return need_load

    def _enqueue_episode_record_crud(self, command: str, param: str) -> None:
        """
        Enqueue an episode record CRUD (Create, Read, Update, Delete) command to the processing queue.

        This method packages the command and task path into a payload and attempts to add it to the episode record CRUD queue. If the operation fails, an exception is logged.

        Args:
            command (str): The CRUD command to be executed (e.g., 'create', 'read', 'update', 'delete').
                            The command may contain special characters like:
                            - '\\t' (tab)
                            - '\\r' (carriage return)
                            - '\\n' (newline)
            param (str): The parameter associated with the command.
                            If command == LoadRecords, param should be save_path.
                            If command == DeleteRecord, param should be episode_id.
        Returns:
            None

        Raises:
            Exception: If there's an error while adding the payload to the queue. The exception is caught and logged rather than being re-raised.
        """
        payload = {
            "command": command,
            "param": param,
        }
        try:
            self._episode_record_crud_queue.put(payload)
        except Exception as e:
            self.logger.exception(f"Failed to enqueue episode record CRUD command: {e}")

    def _apply_episode_record_crud_command(self, payload: Dict[str, Any]) -> None:
        command = str(payload.get("command", "")).strip()
        if command == "LoadRecords":
            save_path = str(payload.get("param", "")).strip()
            if not save_path:
                self.logger.warning("LoadRecords missing save_path for episode browse sync.")
                return

            # if self._set_task_path(save_path):
            #     self._reload_browse_state()
            #     self._sync_episode_records_for_share(self._writer_episode_records)
            self.set_task(save_path=save_path)
            return
        elif command == "DeleteRecord":
            episode_id = str(payload.get("param", "")).strip()
            if not episode_id:
                self.logger.warning("DeleteRecord missing episode_id.")
                return
            self._delete_episode_backend(episode_id=episode_id)
            return
        self.logger.warning(f"Unknown episode record CRUD command: {payload}")
        return

    def _episode_record_crud_listener(self) -> None:
        """Continuously consume browse commands in writer process."""
        while not self._episode_record_crud_stop_event.is_set():
            try:
                payload = self._episode_record_crud_queue.get(timeout=0.2)
            except Empty:
                continue
            except Exception as e:
                self.logger.exception(f"Episode record CRUD listener queue read failed: {e}")
                continue

            if not isinstance(payload, dict):
                self.logger.warning(f"Invalid episode record CRUD payload, expected dict: {payload}")
                continue

            try:
                self._apply_episode_record_crud_command(payload)
            except Exception as e:
                self.logger.exception(f"Episode record CRUD command apply failed: {e}")

    def start_episode_record_crud_listener(self) -> None:
        """Start writer-side browse listener thread."""
        if self._episode_record_crud_thread is not None and self._episode_record_crud_thread.is_alive():
            return

        self._episode_record_crud_stop_event.clear()
        self._episode_record_crud_thread = threading.Thread(
            target=self._episode_record_crud_listener,
            daemon=True,
            name="episode_record_crud_listener",
        )
        self._episode_record_crud_thread.start()

    def stop_episode_record_crud_listener(self) -> None:
        """Stop writer-side browse listener thread and drain pending commands."""
        self._episode_record_crud_stop_event.set()
        if self._episode_record_crud_thread is not None and self._episode_record_crud_thread.is_alive():
            self._episode_record_crud_thread.join(timeout=1.0)
        self._episode_record_crud_thread = None

        while True:
            try:
                payload = self._episode_record_crud_queue.get_nowait()
            except Empty:
                break
            except Exception:
                break

            if not isinstance(payload, dict):
                continue
            try:
                self._apply_episode_record_crud_command(payload)
            except Exception as e:
                self.logger.exception(f"Episode record CRUD drain apply failed: {e}")

    def _sync_browse_on_record_start(self, episode_chunk: int, episode_index: int) -> None:
        """Update writer-side browse cache on recording start and publish to share queue."""
        self._episode_length_map[int(episode_index)] = 0
        pending_record = self._build_episode_record(
            chunk_id=int(episode_chunk),
            episode_index=int(episode_index),
            frames=0,
            complete=False,
        )
        self._upsert_writer_episode_record(pending_record)
        self._sync_episode_records_for_share(pending_record)

    def _sync_browse_on_record_end(self, episode_chunk: int, episode_index: int, episode_length: int) -> None:
        """Update writer-side browse cache on recording end and publish to share queue."""
        self._episode_length_map[int(episode_index)] = int(max(0, int(episode_length)))
        finished_record = self._build_episode_record(
            chunk_id=episode_chunk,
            episode_index=episode_index,
            frames=episode_length,
            complete=True,
        )
        self._upsert_writer_episode_record(finished_record)
        self._sync_episode_records_for_share(finished_record)

    def parse_episode_records(self, chunk_id: Optional[int] = None, selected_task: Optional[str] = None, base_dir: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        """Return browse episode records synced from writer process."""
        try:
            save_path = base_dir / selected_task
            clear = False
            append = False
            if self._is_need_load(save_path=save_path):
                # self._clear_episode_share_queue()
                self._enqueue_episode_record_crud(command="LoadRecords", param=save_path)
                clear = True
                append = True
            self._sync_episode_records_for_browse(timeout_s=0.2, max_empty_retries=5, clear=clear, append=append)
        except Exception as e:
            self.logger.exception(f"Failed to parse episode records: {e}")

        if chunk_id is None:
            return list(self._episode_records_for_browse)
        return [r for r in self._episode_records_for_browse if int(r.get("chunk", -1)) == int(chunk_id)]

    def delete_episode(self, episode_id: str) -> Dict[str, Any]:
        """Delete one episode and update browse cache in main process."""
        self._enqueue_episode_record_crud(command="DeleteRecord", param=episode_id)

        return {
            "deleted": True,
            "episode_id": episode_id,
        }
    def _delete_episode_backend(self, episode_id: str):
        """Delete one episode's data/meta and sync browse cache to main process."""
        try:
            chunk_id, episode_index = self._parse_episode_id(episode_id)
        except Exception as e:
            self.logger.warning(f"Invalid episode_id for delete: {episode_id}, error={e}")
            return

        if not self._save_path or not self._meta_dir:
            self.logger.warning("Delete episode skipped: task path is not initialized.")
            return

        deleted_video_count = 0
        deleted_from_parquet_rows = 0
        deleted_any_data = False

        # 1) Delete parquet file.
        data_path_tpl = self.config.get("data_path", "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet")
        parquet_rel = str(data_path_tpl).format(episode_chunk=chunk_id, episode_index=episode_index)
        parquet_path = Path(self._save_path) / parquet_rel
        if parquet_path.exists():
            deleted_from_parquet_rows = self._parquet_num_rows(parquet_path)
            try:
                parquet_path.unlink()
                deleted_any_data = True
                self.logger.info(f"Deleted parquet file: {parquet_path}")
            except Exception as e:
                self.logger.exception(f"Failed to delete parquet file: {parquet_path}, error={e}")

        # 2) Delete video files for this episode.
        # info = self._load_dataset_info()

        video_path_tpl = self.config.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )

        for video_key in self.camera_name_list:
            rel_video = str(video_path_tpl).format(
                episode_chunk=chunk_id,
                episode_index=episode_index,
                video_key=video_key,
            )
            abs_video = Path(self._save_path) / rel_video
            if not abs_video.exists():
                continue
            try:
                abs_video.unlink()
                deleted_video_count += 1
                deleted_any_data = True
                self.logger.info(f"Deleted video file: {abs_video}")
            except Exception as e:
                self.logger.exception(f"Failed to delete video file: {abs_video}, error={e}")

        # 3) Update episodes.jsonl (remove target episode) and collect removed length.
        episodes_path = Path(self._meta_dir) / "episodes.jsonl"
        kept_lines: List[str] = []
        kept_count = 0
        removed_count = 0
        removed_length = 0

        if episodes_path.exists():
            try:
                with open(episodes_path, "r", encoding="utf-8") as f:
                    for raw_line in f:
                        line = raw_line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                        except Exception:
                            # Keep malformed lines unchanged to avoid data loss.
                            kept_lines.append(line)
                            continue

                        row_episode = int(row.get("episode_index", -1))
                        if row_episode == int(episode_index):
                            removed_count += 1
                            try:
                                removed_length += int(row.get("length", 0) or 0)
                            except Exception:
                                pass
                            continue

                        kept_lines.append(json.dumps(row, ensure_ascii=False))
                        kept_count += 1

                with open(episodes_path, "w", encoding="utf-8") as f:
                    for line in kept_lines:
                        f.write(line + "\n")
                self.logger.info(
                    f"Updated episodes.jsonl after delete: episode_id={episode_id}, removed_count={removed_count}, kept_count={kept_count}"
                )
            except Exception as e:
                self.logger.exception(f"Failed to update episodes.jsonl: {episodes_path}, error={e}")

        # 4) Update info.json and runtime config counters.
        frames_to_sub = int(removed_length if removed_length > 0 else deleted_from_parquet_rows)
        total_frames_new = max(0, self.config["total_frames"] - max(0, frames_to_sub))
        if removed_count > 0:
            total_episodes_new = max(0, kept_count)
        else:
            total_episodes_new = max(0, self.config["total_episodes"] - (1 if deleted_any_data else 0))
        total_videos_new = max(0, self.config["total_videos"] - max(0, deleted_video_count))
        self._write_info_file(total_episodes=total_episodes_new, total_frames=total_frames_new, total_videos=total_videos_new, episode_index=self.config["episode_index"])

        # 5) Update writer-side cache and publish delete event for main-process browse cache.
        self._episode_length_map.pop(int(episode_index), None)
        for i in range(len(self._writer_episode_records) - 1, -1, -1):
            if str(self._writer_episode_records[i].get("id", "")) == str(episode_id):
                del self._writer_episode_records[i]

        self._sync_episode_records_for_share(str(episode_id))
        self.logger.info(
            f"Delete episode backend done: episode_id={episode_id}, videos_deleted={deleted_video_count}, frames_removed={removed_length or deleted_from_parquet_rows}"
        )

    def _update_config_from_init(self):
        self.config["episode_index"] = 0
        self.config["total_episodes"] = 0
        self.config["total_frames"] = 0
        self.config["total_videos"] = 0
        self.config['chunks_size'] = 1000
    
    def _update_config_from_meta_file(self):
        """
        Update configuration by reading metadata files from the meta directory.
        
        This method performs the following operations:
        1. Loads and processes 'info.json' to update dataset information
        2. Loads and processes 'tasks.jsonl' to update task languages
        
        The method handles file paths with proper joining and processes files that may contain special characters including \t (tab), \r (carriage return), or \n (newline).
        
        Returns:
            None: Updates internal state but doesn't return any value
        """
        # Load info.json and update dataset info
        info_file_path = os.path.join(self._meta_dir, 'info.json')
        self._update_dataset_info_from_meta_file(info_file_path)

        # Load tasks.jsonl and update task languages
        task_file_path = os.path.join(self._meta_dir, 'tasks.jsonl')
        self._update_task_languages_from_meta_file(task_file_path)

    def _update_dataset_info_from_meta_file(self, file_path: str):
        """
        Update dataset configuration information from a metadata JSON file.

        This method reads a JSON file containing dataset metadata and updates
        the configuration dictionary with the loaded values. The metadata includes
        information about chunk sizes, video properties, camera configurations,
        and various dataset statistics.

        Args:
            file_path (str): Path to the JSON metadata file to be read.

        Notes:
            - The method handles special characters in the file path including \t (tab), \r (carriage return), and \n (newline).
            - Updates configuration for multiple camera views (head, hand_left, hand_right) including encoding parameters and shape information.
            - Errors during the update process are caught and logged.
        """
        # Open the specified JSON file and load its contents
        with open(file_path, 'r') as file:
            data = json.loads(file.read())
        
        # Update the dataset info in the config using the loaded JSON data
        try:
            self.config['chunks_size'] = data['chunks_size']
            self.config['codebase_version'] = data['codebase_version']
            self.config['data_path'] = data['data_path']
            self.config['video_path'] = data['video_path']
            self.config['episode_index'] = data['episode_index']
            self.config['total_videos'] = data['total_videos']
            self.config['total_frames'] = data['total_frames']
            self.config['total_tasks'] = data['total_tasks']
            self.config['total_episodes'] = data['total_episodes']
            self.config['total_chunks'] = data['total_chunks']
            self.config['fps'] = int(data['fps'])
            self.config['robot_type'] = data['robot_type']
            self.config['splits'] = data['splits']
            self.config['state_shape'] = data['features']['observation.state']['shape'][0]
            self.config['action_shape'] = data['features']['action']['shape'][0]
            self.config['cam.head']['encode']['codec'] = data['features']['cam.head']['info']['video.codec']
            self.config['cam.head']['encode']['has_audio'] = data['features']['cam.head']['info']['has_audio']
            self.config['cam.head']['encode']['is_depth_map'] = data['features']['cam.head']['info']['video.is_depth_map']
            self.config['cam.head']['shape']['height'] = data['features']['cam.head']['info']['video.height']
            self.config['cam.head']['shape']['width'] = data['features']['cam.head']['info']['video.width']
            self.config['cam.head']['shape']['channel'] = data['features']['cam.head']['info']['video.channels']
            self.config['cam.hand_left']['encode']['codec'] = data['features']['cam.head']['info']['video.codec']
            self.config['cam.hand_left']['encode']['has_audio'] = data['features']['cam.head']['info']['has_audio']
            self.config['cam.hand_left']['encode']['is_depth_map'] = data['features']['cam.head']['info']['video.is_depth_map']
            self.config['cam.hand_left']['shape']['height'] = data['features']['cam.head']['info']['video.height']
            self.config['cam.hand_left']['shape']['width'] = data['features']['cam.head']['info']['video.width']
            self.config['cam.hand_left']['shape']['channel'] = data['features']['cam.head']['info']['video.channels']
            self.config['cam.hand_right']['encode']['codec'] = data['features']['cam.head']['info']['video.codec']
            self.config['cam.hand_right']['encode']['has_audio'] = data['features']['cam.head']['info']['has_audio']
            self.config['cam.hand_right']['encode']['is_depth_map'] = data['features']['cam.head']['info']['video.is_depth_map']
            self.config['cam.hand_right']['shape']['height'] = data['features']['cam.head']['info']['video.height']
            self.config['cam.hand_right']['shape']['width'] = data['features']['cam.head']['info']['video.width']
            self.config['cam.hand_right']['shape']['channel'] = data['features']['cam.head']['info']['video.channels']
        except Exception as e:
            self.logger.error(f"Catch exception: {e}")
        # self._normalize_record_features_cam()
        # print(f"Debug: after update config.info={self.config.info}")

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
    
    def _parse_config(self, config: ConfigDict) -> None:
        self.camera_name_list = []
        self.camera_shape_dict = {}
        for camera_name in config.keys():
            if str(camera_name).startswith("cam."):
                self.camera_name_list.append(camera_name)
                shape_dict = config[camera_name]["shape"]
                self.camera_shape_dict[camera_name] = (shape_dict["height"], shape_dict["width"], shape_dict["channel"])
                # print(f"Debug: camera_name: {camera_name}, shape: {shape_list}")

        self.action_shape = config['action_shape']
        self.state_shape = config['state_shape']
        # {'action': (22,), 'cam.hand_left': (480, 848, 3), 'cam.hand_right': (480, 848, 3), 'cam.head': (720, 1280, 3), 'episode_index': (1,), 'frame_index': (1,), 'index': (1,), 'observation.state': (20,), 'task_index': (1,), 'timestamp': (1,)}
        # print(f"Debug: camera_shape_dict={self.camera_shape_dict}")

    def update_camera_shape_dict(self, shape_dict: Dict[str, Union[tuple[int, int, int], list[int]]]) -> None:
        """Update camera shape settings for current recording session and metadata.

        Args:
            shape_dict: Mapping from camera name (e.g. ``cam.head``) to HWC shape.
        """
        if not isinstance(shape_dict, dict) or not shape_dict:
            self.logger.warning("update_camera_shape_dict called with empty shape_dict, skip update.")
            return

        updated = {}
        for camera_name, shape_value in shape_dict.items():
            if not str(camera_name).startswith("cam."):
                continue

            if shape_value is None or len(shape_value) < 2:
                self.logger.warning(f"Invalid shape for {camera_name}: {shape_value}, skip update.")
                continue

            height = int(shape_value[0])
            width = int(shape_value[1])
            channel = int(shape_value[2]) if len(shape_value) >= 3 else 3
            if height <= 0 or width <= 0 or channel <= 0:
                self.logger.warning(f"Invalid shape value for {camera_name}: {shape_value}, skip update.")
                continue

            normalized_shape = (height, width, channel)
            self.camera_shape_dict[camera_name] = normalized_shape
            if camera_name not in self.camera_name_list:
                self.camera_name_list.append(camera_name)

            camera_info = self.config.get(camera_name, ConfigDict(allow_dotted_keys=False))
            # print(f"Debug: camera={camera_name}, feature={camera_feature}")
            camera_info["shape"]["height"] = height
            camera_info["shape"]["width"] = width
            camera_info["shape"]["channel"] = channel

            self.config[camera_name] = camera_info
            updated[camera_name] = normalized_shape

        if updated:
            self.logger.info(f"Updated camera_shape_dict with runtime observation shapes: {updated}")
        else:
            self.logger.warning("No valid camera shape found in shape_dict, keep original config.")

    def begin_recording(self, episode_chunk: int = 0, episode_index: int = 0, total_frames: int = 0, total_videos: int = 0, total_episodes: int = 0, save_raw: bool =True):
        self.episode_chunk = episode_chunk
        self.episode_index = episode_index
        self.total_frames = total_frames
        self.total_videos = total_videos
        self.total_episodes = total_episodes
        self.save_raw = save_raw
        self.logger.info(f"episode_chunk={episode_chunk}, episode_index={episode_index}, total_frames={total_frames}, total_videos={total_videos}, total_episodes={total_episodes}")

        # # Sync browse cache immediately so parse_episode_records can see the running episode.
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
        self.frame_index = 0
        self.episode_task_list = []
        self.step_task_index = 0
        # Use a thread to write parquet file
        self.record_executor = ThreadPoolExecutor(max_workers=1) # max_workers must be 1 to ensure sequence of recording
        self.write_loop_done = threading.Event()
        self.write_parquet_thread = threading.Thread(target=self._write_parquet_fun, args=(self.write_loop_done,), daemon=True)
        try:
            self.write_parquet_thread.start()
        except Exception as e:
            self.logger.exception(f"Write parquet thread can't start: {e}")
            return
    
    def end_recording(self):
        try:
            self.record_executor.shutdown(wait=True) 
            finished_episode_index = self.episode_index
            finished_episode_chunk = self.episode_chunk

            self.episode_index = self.episode_index + 1
            self.total_episodes = self.total_episodes + 1
            self.total_frames = self.total_frames + self.frame_index
            self.total_videos = self.total_videos + len(self.camera_name_list)
            # Sync browse cache right after recording ends.
            self._sync_browse_on_record_end(
                episode_chunk=finished_episode_chunk,
                episode_index=finished_episode_index,
                episode_length=self.frame_index,
            )
            self._write_meta_files(total_episodes=self.total_episodes,
                                total_frames=self.total_frames,
                                total_videos=self.total_videos,
                                episode_length=self.frame_index,
                                episode_task_list=self.episode_task_list,
                                episode_index=self.episode_index)
            # stop recording for current episode: flush video/parquet after all queue data drained
            self.write_loop_done.set()
            self.write_parquet_thread.join()
            self._release_video_writers()
            self._release_parquet_writer()

        except Exception as e:
            self.logger.exception(f"Finished recording failed: {e}")
        self.logger.info("Finish recording.")
        return self.episode_index, self.total_frames, self.total_videos, self.total_episodes
            # self._clear_queues()
            # print(f'self.shared_data.task_language_dict {self.shared_data.task_language_dict}')

    def add_frame_async(self, step_state: dict, step_action: np.ndarray, step_extra: dict):
        self.record_executor.submit(self._write_frame_fun, step_state, step_action, step_extra)

    # @run_time_decorator
    # First frame takas 20ms and the others tasks 5ms
    def _write_frame_fun(self, step_state: dict, step_action: np.ndarray, step_extra: dict):
        """
        Main function for the write data frame responsible for writing data to disk.

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

        start_time = time.perf_counter()
        try:
            # check action shape 
            if step_action.shape[0] < self.action_shape:
                step_action = np.concatenate([step_action, np.zeros(self.action_shape-step_action.shape[0])], axis=0)
            # check action shape 
            obs_state = step_state['obs']['state']
            if obs_state.shape[0] < self.state_shape:
                # self.logger.warning(f"obs shape {observation['obs.state'].shape[0]} is not correct, config shape is {self.state_shape}, add 0 to obs.state")
                # assert state['obs.state'].shape[0] <= self.state_shape, \
                # f"obs shape {state['obs.state'].shape[0]} is bigger than config shape {self.state_shape}"
                obs_state = np.concatenate([obs_state, np.zeros(self.state_shape - obs_state.shape[0], dtype=obs_state.dtype)], axis=0)
            step_language = step_extra.get('language_status', {}).get('language', '')
            
            # Track new language instructions per episode
            if step_language not in self.episode_task_list:
                self.episode_task_list.append(step_language)
            
            # Assign task index based on unique language instruction
            if step_language not in self.task_language_dict.keys():
                step_task_index = len(self.task_language_dict.keys())
                self.task_language_dict[step_language] = step_task_index
            else:
                step_task_index = self.task_language_dict[step_language]
            
            # Write image frames to video files
            for camera_name in self.camera_name_list:
                expected_shape = self.camera_shape_dict[camera_name]
                raw_frame = step_state['obs'].get(camera_name)
                # self.logger.info(f"step_state: {step_state.keys()}")
                # TODO: use three threads in the future
                frame = self._prepare_video_frame(raw_frame, self.save_raw, expected_shape)
                # self.logger.info(f"expected_shape: {expected_shape}")
                if frame is None:
                    self.logger.warning(f"{camera_name} frame invalid, skip this frame")
                    continue

                writer = self.video_writers.get(camera_name, None)
                if writer is None or (not writer.isOpened()):
                    self.logger.error(f"Video writer is not opened for {camera_name}, skip write")
                    continue

                writer.write(frame)
                if self.frame_index % 30 == 0:
                    self.logger.debug(f"{camera_name} writes a frame with expected_shape {frame.shape}.")
            # Construct record dictionary for Parquet file
            parquet_frame = {
                'observation.state': step_state['obs.state'].tolist(),
                'action': step_action.tolist(),
                'episode_index': self.episode_index,
                'frame_index': self.frame_index,
                'index': self.total_frames+self.frame_index,
                'task_index': step_task_index,  # Placeholder for task index, can be updated based on actual task mapping
                'timestamp': 1/30 * self.frame_index,  # Fixed frame rate assumption
            }
            with self.parquet_lock:
                self.parquet_frame_list.append(parquet_frame)
            
            # Update counters
            frame_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            if self.frame_index % 30 == 0 or frame_elapsed_ms > 30.0:
                self.logger.info(
                    f"_write_frame_fun: episode={self.episode_index}, frame_index={self.frame_index}, "
                    f"frame_time={frame_elapsed_ms:.1f}ms, cached_records={len(self.parquet_frame_list)}, "
                    f"camera_names={self.camera_name_list}"
                )
            if frame_elapsed_ms > 30.0:
                self.logger.warning(
                    f"_write_frame_fun slow frame: episode={self.episode_index}, frame_index={self.frame_index}, "
                    f"frame_time={frame_elapsed_ms:.1f}ms"
                )
            self.frame_index += 1
        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
            # self.release_writers()
        
        except Exception as e:
            self.logger.exception(f"Writing frame exited with exception: {e}")
            # self.release_writers()
        # finally:
            # self.logger.info("Writing frame exited.")
            # self.release_writers()
    def _prepare_video_frame(self, frame: Any, save_raw: bool=True, expected_shape: tuple[int, int, int]=(480, 640, 3)) -> Optional[np.ndarray]:
        """Normalize input frame to contiguous uint8 HWC(BGR-compatible) for VideoWriter."""
        # print(f"frame ndim={frame.ndim}, dtype={frame.dtype}, shape={frame.shape}, expected_shape={expected_shape}")
        if not isinstance(frame, np.ndarray):
            self.logger.warning(f"Frame is not np.ndarray, skip process and return None.")
            return None

        if frame.ndim != 3:
            self.logger.warning(f"Frame ndim is not equal 3, skip process and return None.")
            return None

        # Convert RGB frames to BGR for OpenCV VideoWriter compatibility
        # if frame.shape[2] == 3:
        #     frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        exp_h, exp_w = expected_shape[0], expected_shape[1]
        if not save_raw and (frame.shape[0] != exp_h or frame.shape[1] != exp_w):
            frame = cv2.resize(frame, (exp_w, exp_h), interpolation=cv2.INTER_LINEAR)
        
        return np.ascontiguousarray(frame)

    def _create_video_writer(self, episode_chunk: int = 0, episode_index: int = 0) -> Dict[str, Any]:
        """
        Generates video writers for each camera stream.

        Creates OpenCV VideoWriter objects for each camera specified in the configuration.

        Returns:
            dict: A dictionary mapping camera names to their respective VideoWriter objects.
        """
        # Video writing setup
        # print(f"DEBUG: Mark 1")
        save_video_path = os.path.join(self._save_path, 'videos', f'chunk-{episode_chunk:03d}')
        filename = f"{'episode'}_{episode_index:06d}.{'mp4'}"
        video_write_dict = {}
        # self.camera_shape_dict = {}
        fps = float(self.config.get('fps', 30))

        # print(f"DEBUG: Mark 2")
        for camera_name in self.camera_name_list:
            shape_list = self.camera_shape_dict[camera_name]
            height, width = int(shape_list[0]), int(shape_list[1])
            os.makedirs(os.path.join(save_video_path, camera_name), exist_ok=True)
            video_path = os.path.join(save_video_path, camera_name, filename)
            # self.shared_data.save_video_path_list.append(video_path)

            writer = None
            for codec in ('mp4v', 'avc1', 'XVID', 'MJPG'):
                # print(f"Debug: Trying to save video with codec: {codec}")
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
        self.logger.info(f"create video writer: {save_video_path}")
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
            self._save_path,
            self.config['data_path'].format(episode_chunk=episode_chunk, episode_index=episode_index)
        )
        os.makedirs(os.path.dirname(parquet_file_path), exist_ok=True)
        parquet_writer = pq.ParquetWriter(parquet_file_path, parquet_schema)
        # return parquet_schema, parquet_file_path, parquet_writer
        self.logger.info(f"create parquet writer: {parquet_file_path}")
        return parquet_schema, parquet_writer

    def _release_video_writers(self):
        """Release all opened video writers safely."""
        video_writers = getattr(self, 'video_writers', None)
        if not video_writers:
            return
        for writer in video_writers.values():
            try:
                writer.release()
            except Exception:
                self.logger.debug("Video writer release() failed", exc_info=True)
        self.video_writers = {}
        self.logger.info("All video writers released.")
    
    def _release_parquet_writer(self):
        """Release opened parquet writer safely."""
        parquet_writer = getattr(self, 'parquet_writer', None)
        if parquet_writer:
            parquet_writer.close()
            self.parquet_writer = None
            self.logger.info(f"Successfully wrote Parquet file.")

    def _write_parquet_fun(self, write_loop_done: threading.Event):
        """Writes parquet batches until writer loop is done and in-memory buffer is empty."""
        while True:
            # Write a batch of records to Parquet file every 1 second
            time.sleep(1.0)
            with self.parquet_lock:
                if self.parquet_frame_list:
                    df = pd.DataFrame(self.parquet_frame_list)
                    table = pa.Table.from_pandas(df, schema=self.parquet_schema)
                    self.parquet_writer.write_table(table)
                    self.logger.info(f"Wrote {len(self.parquet_frame_list)} records to Parquet file.")
                    self.parquet_frame_list.clear()
                if write_loop_done.is_set() and (not self.parquet_frame_list):
                    break

        # Final flush before closing
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
        self.logger.info("Successfully wrote Parquet file.")
            

    def _write_meta_files(self, total_episodes: int, total_frames: int, total_videos: int, episode_length: int, episode_task_list: list[str], episode_index: int):
        """
        Writes metadata files including info.json, episodes.jsonl, and tasks.jsonl.

        These files contain global dataset statistics, per-episode information, and task mappings respectively.
        """
        try:
            # Write info.json file (always overwrite to keep metadata in sync)
            self._write_info_file(total_episodes=total_episodes, total_frames=total_frames, total_videos=total_videos, episode_index=episode_index)

            # Write episodes.jsonl file
            episodes_file_path = os.path.join(self._meta_dir, 'episodes.jsonl')
            episodes_content = {
                "episode_index": episode_index - 1,
                "tasks": episode_task_list,
                "length": episode_length
            }
            with open(episodes_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(episodes_content, ensure_ascii=False) + '\n')

            self.logger.info(f"episodes.jsonl has been written to: {episodes_file_path}")

            # Write tasks.jsonl file
            tasks_file_path = os.path.join(self._meta_dir, 'tasks.jsonl')
            with open(tasks_file_path, 'w', encoding='utf-8') as f:
                for task_language in self.task_language_dict.keys():
                    tasks_content = {
                        "task_index": self.task_language_dict[task_language],
                        "tasks": task_language
                    }
                    f.write(json.dumps(tasks_content, ensure_ascii=False) + '\n')
            self.logger.info(f"tasks.jsonl has been written to: {tasks_file_path}")

        except Exception as e:
            self.logger.exception(f"Exception in write_meta_files: {e}")

    def _write_info_file(self, total_episodes: int, total_frames: int, total_videos: int, episode_index: int):
        try:
            # Write info.json file (always overwrite to keep metadata in sync)
            info_file_path = os.path.join(self._meta_dir, 'info.json')
            self.config["episode_index"] = episode_index
            self.config["total_episodes"] = total_episodes
            self.config["total_frames"] = total_frames
            self.config["total_videos"] = total_videos
            self.config["splits"] = {"test": f"0:{total_episodes-1}"}
            # Define complete metadata dictionary structure
            meta_info_dict = {
                'chunks_size': self.config['chunks_size'],
                'codebase_version': self.config['codebase_version'],
                'data_path': self.config['data_path'],
                'features': {
                    'action': {'dtype': 'float32', 'shape': [self.config['action_shape']]},
                    'cam.hand_left': {
                        'dtype': 'video',
                        'info': {
                            'has_audio': self.config['cam.hand_left']['encode']['has_audio'],
                            'video.channels': self.config['cam.hand_left']['shape']['channel'],
                            'video.codec': self.config['cam.hand_left']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.height': self.config['cam.hand_left']['shape']['height'],
                            'video.is_depth_map': self.config['cam.hand_left']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p',
                            'video.width': self.config['cam.hand_left']['shape']['width'],
                        },
                        'names': ['height', 'width', 'channel'],
                        'shape': [
                            self.config['cam.hand_left']['shape']['height'],
                            self.config['cam.hand_left']['shape']['width'],
                            self.config['cam.hand_left']['shape']['channel']
                            ],
                        'video_info': {
                            'has_audio': self.config['cam.hand_left']['encode']['has_audio'],
                            'video.codec': self.config['cam.hand_left']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.is_depth_map': self.config['cam.hand_left']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p'
                        }
                    },
                    'cam.hand_right': {
                        'dtype': 'video',
                        'info': {
                            'has_audio': self.config['cam.hand_right']['encode']['has_audio'],
                            'video.channels': self.config['cam.hand_right']['shape']['channel'],
                            'video.codec': self.config['cam.hand_right']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.height': self.config['cam.hand_right']['shape']['height'],
                            'video.is_depth_map': self.config['cam.hand_right']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p',
                            'video.width': self.config['cam.hand_right']['shape']['width'],
                        },
                        'names': ['height', 'width', 'channel'],
                        'shape': [
                            self.config['cam.hand_right']['shape']['height'],
                            self.config['cam.hand_right']['shape']['width'],
                            self.config['cam.hand_right']['shape']['channel']
                            ],
                        'video_info': {
                            'has_audio': self.config['cam.hand_right']['encode']['has_audio'],
                            'video.codec': self.config['cam.hand_right']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.is_depth_map': self.config['cam.hand_right']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p'
                        }
                    },
                    'cam.head': {
                        'dtype': 'video',
                        'info': {
                            'has_audio': self.config['cam.head']['encode']['has_audio'],
                            'video.channels': self.config['cam.head']['shape']['channel'],
                            'video.codec': self.config['cam.head']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.height': self.config['cam.head']['shape']['height'],
                            'video.is_depth_map': self.config['cam.head']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p',
                            'video.width': self.config['cam.head']['shape']['width'],
                        },
                        'names': ['height', 'width', 'channel'],
                        'shape': [
                            self.config['cam.head']['shape']['height'],
                            self.config['cam.head']['shape']['width'],
                            self.config['cam.head']['shape']['channel']
                            ],
                        'video_info': {
                            'has_audio': self.config['cam.head']['encode']['has_audio'],
                            'video.codec': self.config['cam.head']['encode']['codec'],
                            'video.fps': float(self.config['fps']),
                            'video.is_depth_map': self.config['cam.head']['encode']['is_depth_map'],
                            'video.pix_fmt': 'yuv420p'
                        }
                    },
                    'episode_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                    'frame_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                    'index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                    'observation.state': {'dtype': 'float32', 'shape': [self.config['state_shape']]},
                    'task_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                    'timestamp': {'dtype': 'float32', 'names': None, 'shape': [1]}
                },
                'fps': float(self.config['fps']),
                'robot_type': self.config['robot_type'],
                'splits': {'train': f'0:{total_episodes-1}'},
                'episode_index': episode_index,
                'total_chunks': 1,
                'total_episodes': total_episodes,
                'total_frames': total_frames,
                'total_tasks': len(self.task_language_dict.keys()), # TODO: assign total tasks
                'total_videos': total_videos,
                'video_path': self.config['video_path']
            }
            # print(f"Debug: info_file: {meta_info_dict}")
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(meta_info_dict, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"info.json has been written to: {info_file_path}")
        except Exception as e:
            self.logger.exception(f"Exception in write_info_file: {e}")

if __name__ == "__main__":
    pass