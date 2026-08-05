import os
import json
import csv
import time
import logging
import threading
from queue import Empty
from datetime import datetime
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue
from typing import Any, Dict, List, Optional, Union
from client.utils.util import run_time_decorator

class EvaluationResultRecorder:
    """Evaluation result recorder.

    Inspired by LeRobotDatasetWriter's architecture (thread isolation and batch flush),
    but simplified for eval log's small data volume:
    uses threads instead of processes, JSON+CSV instead of Parquet+Video.

    Data flow:
        server.py / vla_client  (main thread)
            │
            ├── start(task, subtask, instruction)   → creates record, starts stats thread
            ├── finalize(status, score)             → closes running record, flushes to disk
            ├── pause() / resume()                  → freezes/resumes timer
            ├── set_score(id, score) / set_note(id, note)
            │
            └── Stats Thread (daemon, 200ms interval)
                    └── reads vla_client.realtime_data_manager → updates running record

    Storage:
        {save_dir}/{task_name}_{date}/eval/eval_log.json + eval_log.csv
    """

    CSV_HEADERS = [
        'ID', 'TaskId', 'SubTaskId', 'Instruction', 'StartTime', 'EndTime', 'Duration(s)', 'Score', 'Note',
        'EpisodeID', 'Mode', 'WaitTime(ms)', 'ControlPeriod(ms)', 'ControlSpeed', 'InterChunkMode', 'IntraChunkMode', 'ModelType', 'ModelPath',
        'ObvCount', 'AvgObvFPS', 'InferCount', 'ImgProcTime(ms)', 'AvgInferTime(ms)', 'AvgInterTrajTime(ms)', 'AvgIntraTrajTime(ms)', 'AvgCommTime(ms)',
    ]

    def __init__(self, evaluation_config: ConfigDict) -> None:
        self.logger = logging.getLogger(__name__)
        self.config = evaluation_config
        self._episode_id = -1
        self._eval_dir = None
        self._eval_records: List[Dict[str, Any]] = []
        self._eval_json_file = None
        self._eval_csv_file = None

        # Runtime cache for evaluation result browsing in main process.
        self._eval_records_for_browse: List[Dict[str, Any]] = []
        self._eval_records_for_share: Queue = Queue()
        self._eval_dir_for_browse = None

        # Queue-based CRUD sync between main process and writer process.
        self._eval_record_crud_queue = Queue()
        self._eval_record_crud_thread: Optional[threading.Thread] = None
        self._eval_record_crud_stop_event = threading.Event()

    def set_task(self, save_path: str, episode_id: int = -1) -> int:
        """Set task information and prepare for data recording. Called in writer process"""
        self.logger.info(f"save_path: {save_path}, episode_id: {episode_id}")
        self._episode_id = episode_id
        record_id = None
        if self._check_eval_dir(save_path=save_path):
            record_id = self._load_existing_records()
        return record_id

    # def set_task_for_browse(self, save_path: str) -> None:
    #     """Set task information and prepare for data browse. Called in main process"""
    #     self.logger.info(f"save_path: {save_path}")
    #     try:
    #         if self._check_eval_dir_for_browse(save_path = save_path):
    #             self._load_existing_browse_records()
    #     except Exception as e:
    #         self.logger.exception(f"Failed to load eval records for browse: {e}")
    def parse_eval_records(self, selected_task: Optional[str] = None, base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return evaluation records in reverse order (newest first)."""
        try:
            task_path = base_dir / selected_task
            # self.logger.info(f"Parse eval records: {task_path}")
            clear = False
            append = False
            if self._is_need_load(save_path = task_path):
                # self._clear_share_queue()
                self._enqueue_eval_record_crud(command="LoadRecords", record_id=-1, score=None, note="", task_path=task_path)
                clear = True
                append = True
            self._sync_eval_records_for_browse(timeout_s=0.1, max_empty_retries=10, clear=clear, append=append)
        except Exception as e:
            self.logger.exception(f"Failed to load eval records: {e}")
        return self._eval_records_for_browse

    def _clear_share_queue(self):
        try:
            while not self._eval_records_for_share.empty():
                try:
                    self._eval_records_for_share.get_nowait()
                except Empty:
                    break
        except Exception:
            # Fallback: keep calling get_nowait until it fails
            try:
                while True:
                    self._eval_records_for_share.get_nowait()
            except Exception:
                self.logger.info("Clear _eval_records_for_share and ready to share the new loaded records.")

    def _sync_eval_records_for_browse(self, timeout_s: float = 0.1, max_empty_retries: int = 5, clear: bool = False, append: bool = False):
            """Continuously consume records from _eval_records_for_share and append to _eval_records_for_browse."""
            # 1. Clear stale data before syncing
            if clear:
                self._eval_records_for_browse.clear()

            # 2. Block and wait for data from the shared queue
            empty_count = 0
            while True:
                try:
                    # Block for 0.2s waiting for data from the writer process
                    record = self._eval_records_for_share.get(timeout=timeout_s)
                    empty_count = max_empty_retries - 2  # Reset counter on successful fetch
                    
                    if isinstance(record, dict):
                        if append:
                            self._eval_records_for_browse.append(record)
                            self.logger.info(f"Append new eval record.")
                        else:
                            self._upsert_eval_browse_record(record=record)
                    elif isinstance(record, int):
                        self._delete_eval_browse_record(record_id=record)
                except Empty:
                    # 3. If queue is empty, increment counter. If repeatedly empty, assume sync is done.
                    empty_count += 1
                    if empty_count >= max_empty_retries:
                        self.logger.exception(f"Reach max empty retries when sync eval records for browse.")
                        break
                except Exception as e:
                    self.logger.exception(f"Failed to sync eval records for browse: {e}")
                    break

            # 4. Sort records by id descending (consistent with _upsert_eval_browse_record)
            self._eval_records_for_browse.sort(key=lambda x: int(x.get("id", -1)), reverse=True)

    def _upsert_eval_browse_record(self, record: Dict[str, Any]) -> None:
        """update or append one eval record in browse cache."""
        target_id = int(record.get("id", -1))
        replaced = False
        for idx, item in enumerate(self._eval_records_for_browse):
            if int(item.get("id", -1)) == target_id:
                self._eval_records_for_browse[idx] = record
                replaced = True
                self.logger.info(f"Update eval record successfully, id={target_id}")
                break
        if not replaced:
            self._eval_records_for_browse.append(record)
            self.logger.info(f"Update eval record failed, append it.")
        # self._eval_records_for_browse.sort(key=lambda x: int(x.get("id", -1)), reverse=True)

    def _delete_eval_browse_record(self, record_id: id) -> None:
        is_deleted = False
        for i in range(len(self._eval_records_for_browse) - 1, -1, -1):
            if self._eval_records_for_browse[i].get('id') == record_id:
                del self._eval_records_for_browse[i]
                self.logger.info(f"Delete eval record successfully, id={record_id}")
                is_deleted = True
                break
        if not is_deleted:
            self.logger.info(f"Delete eval record failed, id={record_id}")

    def _check_eval_dir(self, save_path: str) -> bool:
        """Check and ensure eval directory exists. Return true when eval_dir assigned or changed. Called in writer process."""
        load_data = False
        if self._eval_dir is None or self._eval_dir != os.path.join(save_path, 'eval'):
            load_data = True
            self._eval_dir = os.path.join(save_path, 'eval')
            # Ensure eval directory exists.
            if not os.path.exists(self._eval_dir):
                os.makedirs(self._eval_dir, exist_ok=True)
                self.logger.info(f"Eval directory doesn't exist and create it: {self._eval_dir}")
            self._eval_json_file = os.path.join(self._eval_dir, 'eval_log.json')
            self._eval_csv_file = os.path.join(self._eval_dir, 'eval_log.csv')
        else:
            self.logger.info(f"Eval directory already exists: {self._eval_dir}, load_data: {load_data}")

        return load_data

    def _load_existing_records(self) -> None:
        """Load existing records from eval_log.json; fallback to empty list. Called in writer process."""
        self._eval_records = []
        record_id = None
        if not self._eval_json_file or (not os.path.exists(self._eval_json_file)):
            self.logger.info(f"Load eval records from json file terminated, eval_json_file doesn't exist. Total eval records = {len(self._eval_records)}")
            return record_id

        try:
            with open(self._eval_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                self._eval_records = [r for r in data if isinstance(r, dict)]
                self._sync_eval_records_for_share(targets=self._eval_records)
                if self._eval_records:
                    record_id = max(int(r.get('id', -1)) for r in self._eval_records)
        except Exception as e:
            self.logger.exception(f"Load eval_log.json failed: {e}")
            self._eval_records = []
            record_id = None
        self.logger.info(f"Load eval records from json file successfully, total records = {len(self._eval_records)}, max record_id = {record_id}")
        return record_id

    def _sync_eval_records_for_share(self, targets: Union[List[Dict[str, Any]], Dict[str, Any], int]) -> None:
        """Publish eval records or record_id to the shared queue for main-process browse sync."""
        if targets is None:
            return
        def _convert_to_eval_record_for_browse(record: Dict[str, Any]) -> Dict[str, Any]:
            sub_task_id = record.get("sub_task_id", None)
            # self.logger.debug(f"sub_task_id={sub_task_id}")
            return {
                "id": int(record.get("id", -1)),
                "sub_task_id": sub_task_id + 1 if sub_task_id is not None else None,
                "duration": record.get("duration", None),
                "score": record.get("score", None),
                "note": record.get("note", ""),
            }
        # 1. Handle list of dict: iterate and put each record individually
        if isinstance(targets, list):
            for item in targets:
                if isinstance(item, dict):
                    self._eval_records_for_share.put(_convert_to_eval_record_for_browse(record=item))
                    self.logger.info(f"Sync one record for share: {item.get('id')}")
                elif isinstance(item, int):
                    self._eval_records_for_share.put(item)
            return

        # 2. Handle single dict: put directly
        if isinstance(targets, dict):
            self._eval_records_for_share.put(_convert_to_eval_record_for_browse(record=targets))
            self.logger.info(f"Sync one record for share: {targets.get('id')}")
            return

        # 3. Handle int (record_id for deletion): put directly
        if isinstance(targets, int):
            self._eval_records_for_share.put(targets)
            return

        self.logger.warning(f"Unsupported target type: {type(targets)}, only support dict and int.")

    def _is_need_load(self, save_path: str) -> bool:
        """Return true when eval_dir assigned or changed. Called in main process."""
        need_load = False
        if self._eval_dir_for_browse is None or self._eval_dir_for_browse != os.path.join(save_path, 'eval'):
            need_load = True
            self._eval_dir_for_browse = os.path.join(save_path, 'eval')
        self.logger.info(f"Eval directory: {self._eval_dir_for_browse}, need_load: {need_load}")
        return need_load

    def begin_recording(self, eval_record_id: int, sub_task_id: int):
        self._record_executor = ThreadPoolExecutor(max_workers=1) # max_workers must be 1 to ensure sequence of recording
        self._create_new_record(eval_record_id=eval_record_id, sub_task_id=sub_task_id)

    def end_recording(self):
        if self._eval_record_pause_time is not None and self._eval_record_resume_time is None:
            self._eval_record_stop_time = time.time() # required for special case 
            self.resume_recording()
        record_id = self._finalize_current_record()
        self._flush_to_disk()
        return record_id
    
    def pause_recording(self):
        self._eval_record_pause_time = time.time()
        self._eval_record_resume_time = None

    def resume_recording(self):
        self._eval_record_resume_time = time.time()
        self._eval_record_pause_duration += self._eval_record_resume_time - self._eval_record_pause_time
    
    def add_frame_async(self, step_extra: dict):
        self._record_executor.submit(self._write_frame_fun, step_extra)

    # @run_time_decorator
    # First frame takas 20ms and the others tasks 5ms
    def _write_frame_fun(self, step_extra: dict):
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

        try:
            self._eval_record_stop_time = time.time()
            # record info for first frame of a sub-task
            if self._current_record['task_id'] is None:
                # assign value explicitly
                self._init_current_record(step_extra=step_extra)
            # record info for the other frames of a sub-task
            elif self._current_record['sub_task_id'] == step_extra.get('language_status', {}).get('sub_task_id', None):
                self._updata_current_record(step_extra=step_extra)
            # New sub-task, save the current record and start a new record
            else:
                # save the current record
                record_id, _ = self._finalize_current_record()
                self._flush_to_disk()
                # start a new record
                self._create_new_record(eval_record_id=record_id + 1, sub_task_id=step_extra.get('language_status', {}).get('sub_task_id', None))
                self._init_current_record(step_extra=step_extra)
        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
        except Exception as e:
            self.logger.exception(f"Writing frame exited with exception: {e}")
            # self.release_writers()
        # finally:
            # self.logger.info("Writing frame exited.")
            # self.release_writers()
    def _create_new_record(self, eval_record_id: int, sub_task_id: int):
        self._obv_count = 0
        self._eval_record_start_time = None
        self._eval_record_stop_time = None
        self._eval_record_pause_time = None
        self._eval_record_resume_time = None
        self._eval_record_pause_duration = 0.0
        self._current_record = {
            'id': eval_record_id,
            'task_id': None,
            'sub_task_id': sub_task_id,
            'instruction': None,
            'start_time': None,
            'end_time': None,
            'duration': None,
            # 'paused_s': 0.0,
            # 'paused_at': None,
            # 'status': 'running',
            'score': None,
            'note': '',
            'episode_id': self._episode_id,
            'mode': None,
            'wait_time': None,
            'control_period': None,
            'control_speed': None,
            'inter_chunk_mode': None,
            'intra_chunk_mode': None,
            'model_type': None,
            'model_path': None,
            # 'task_name': None,
            'obv_count': None,
            'obv_fps': [],
            'infer_count': [],
            'img_proc_time': [],
            'avg_infer_time': [],
            'avg_intra_traj_time': [],
            'avg_inter_traj_time': [],
            'avg_comm_time': [],
        }
        self._eval_records.append(self._current_record)
        self._sync_eval_records_for_share(targets=self._current_record)

    def _init_current_record(self, step_extra: dict):
        self._eval_record_start_time = time.time()
        # self._obv_count += 1
        runtime_config = step_extra.get('runtime_config', {})
        self._current_record['mode'] = runtime_config.get('mode', None)
        self._current_record['wait_time'] = runtime_config.get('wait_time', None)
        self._current_record['control_period'] = runtime_config.get('control_period', None)
        self._current_record['control_speed'] = runtime_config.get('control_speed', None)
        self._current_record['inter_chunk_mode'] = runtime_config.get('inter_chunk_mode', None)
        self._current_record['intra_chunk_mode'] = runtime_config.get('intra_chunk_mode', None)
        server_status = step_extra.get('server_status', {})
        self._current_record['model_type'] = server_status.get('model_type', None)
        self._current_record['model_path'] = server_status.get('model_path', None)
        # self._current_record['task_name'] = step_runtime.get('task_name', None)
        language_status = step_extra.get('language_status', {})
        self._current_record['task_id'] = language_status.get('task_id', None)
        self._current_record['sub_task_id'] = language_status.get('sub_task_id', None)
        self._current_record['instruction'] = language_status.get('language', None)
        # self._current_record['episode_id'] = step_runtime.get('episode_id', None)
        self._updata_current_record(step_extra=step_extra)
    
    def _updata_current_record(self, step_extra: dict):
        self._obv_count += 1
        runtime_status = step_extra.get('runtime_status', {})
        if not self._current_record['infer_count'] or self._current_record['infer_count'][-1] != runtime_status.get('infer_count', None):
            self._current_record['obv_fps'].append(runtime_status.get('obv_fps', None))
            self._current_record['infer_count'].append(runtime_status.get('infer_count', None))
            self._current_record['img_proc_time'].append(runtime_status.get('img_proc_time', None))
            self._current_record['avg_infer_time'].append(runtime_status.get('avg_infer_time', None))
            self._current_record['avg_intra_traj_time'].append(runtime_status.get('avg_intra_traj_time', None))
            self._current_record['avg_inter_traj_time'].append(runtime_status.get('avg_inter_traj_time', None))
            self._current_record['avg_comm_time'].append(runtime_status.get('avg_comm_time', None))

    def _finalize_current_record(self) -> tuple[int, float]:
        self._current_record['obv_count'] = self._obv_count
        self._current_record['start_time'] = self._timestamp(self._eval_record_start_time) if self._eval_record_start_time is not None else None
        self._current_record['end_time'] = self._timestamp(self._eval_record_stop_time) if self._eval_record_stop_time is not None else None
        self._current_record['duration'] = round(self._eval_record_stop_time - self._eval_record_start_time - self._eval_record_pause_duration, 1) if self._eval_record_start_time is not None and self._eval_record_stop_time is not None else 0.0
        self._sync_eval_records_for_share(targets=self._current_record)
        return self._current_record['id']
    
    def _timestamp(self, time_stamp) -> str:
        dt = datetime.fromtimestamp(time_stamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    def _enqueue_eval_record_crud(self, command: str, record_id: int, score: Optional[float] = None, note: str = "", task_path: str = "") -> None:
        """Publish one CRUD command to the shared queue for writer-side sync."""
        payload = {
            "command": command,
            "task_path": task_path,
            "record_id": record_id,
            "score": score,
            "note": note,
        }
        try:
            self._eval_record_crud_queue.put(payload)
        except Exception as e:
            self.logger.exception(f"Failed to enqueue eval record CRUD command: {e}")

    def _apply_eval_record_crud_command(self, payload: Dict[str, Any]) -> None:
        """Apply one CRUD command to update _eval_records and flush to disk."""
        command = str(payload.get("command", "")).strip()
        record_id = int(payload.get("record_id", -1))
        if command == "LoadRecords":
            task_path = str(payload.get("task_path", "")).strip()
            if self._check_eval_dir(save_path=task_path):
                self._load_existing_records()
                self._eval_dir = None # load data when start recording for first time
                self.logger.info(f"CRUD command: {command} executed successfully, task_path: {task_path}")
                return
        rec = next((r for r in self._eval_records if int(r.get('id', -1)) == record_id), None)
        if rec is None:
            self.logger.warning(f"Record with id {record_id} not found for CRUD command: {command}")
            return

        if command == "UpdateScore":
            score = payload.get('score', None)
            rec['score'] = score
            self._sync_eval_records_for_share(targets=rec)
            self._flush_to_disk()
            self.logger.info(f"CRUD command: {command} executed successfully, record_id: {record_id}, score: {score}")
        elif command == "UpdateNote":
            note = payload.get('note', "")
            rec['note'] = note
            self._sync_eval_records_for_share(targets=rec)
            self._flush_to_disk()
            self.logger.info(f"CRUD command: {command} executed successfully, record_id: {record_id}, note: {note}")
        elif command == "DeleteRecord":
            for i in range(len(self._eval_records) - 1, -1, -1):
                if int(self._eval_records[i].get('id', -1)) == record_id:
                    del self._eval_records[i]
                    self._sync_eval_records_for_share(targets=record_id)
                    self._flush_to_disk()
                    self.logger.info(f"CRUD command: {command} executed successfully, record_id: {record_id}")
                    return
        else:
            self.logger.warning(f"Unknown eval record CRUD command: {payload}")

    def _eval_record_crud_listener(self) -> None:
        """Continuously consume CRUD commands and sync _eval_records in writer process."""
        while not self._eval_record_crud_stop_event.is_set():
            try:
                payload = self._eval_record_crud_queue.get(timeout=0.2)
            except Empty:
                continue
            except Exception as e:
                self.logger.exception(f"Eval record CRUD listener queue read failed: {e}")
                continue

            if not isinstance(payload, dict):
                self.logger.warning(f"Invalid eval record CRUD payload, expected dict: {payload}")
                continue

            try:
                self._apply_eval_record_crud_command(payload)
            except Exception as e:
                self.logger.exception(f"Eval record CRUD command apply failed: {e}")

    def start_eval_record_crud_listener(self) -> None:
        """Start writer-side CRUD listener thread. Called in writer process."""
        if self._eval_record_crud_thread is not None and self._eval_record_crud_thread.is_alive():
            return

        self._eval_record_crud_stop_event.clear()
        self._eval_record_crud_thread = threading.Thread(
            target=self._eval_record_crud_listener,
            daemon=True,
            name="eval_record_crud_listener",
        )
        self._eval_record_crud_thread.start()

    def stop_eval_record_crud_listener(self) -> None:
        """Stop writer-side CRUD listener thread and drain remaining commands. Called in writer process."""
        self._eval_record_crud_stop_event.set()
        if self._eval_record_crud_thread is not None and self._eval_record_crud_thread.is_alive():
            self._eval_record_crud_thread.join(timeout=1.0)
        self._eval_record_crud_thread = None

        while True:
            try:
                payload = self._eval_record_crud_queue.get_nowait()
            except Empty:
                break
            except Exception:
                break

            if not isinstance(payload, dict):
                continue
            try:
                self._apply_eval_record_crud_command(payload)
            except Exception as e:
                self.logger.exception(f"Eval record CRUD drain apply failed: {e}")

    def set_score(self, record_id: int, score: Optional[float]) -> None:
        self._enqueue_eval_record_crud(command="UpdateScore", record_id=record_id, score=score, note="")
        return


    def set_note(self, record_id: int, note: str) -> None:
        self._enqueue_eval_record_crud(command="UpdateNote", record_id=record_id, score=None, note=note)
        return


    def delete_record(self, record_id: int) -> Dict[str, Any]:
        """Delete one episode and update browse cache in main process."""
        self._enqueue_eval_record_crud(command="DeleteRecord", record_id=record_id)

        return {
            "deleted": True,
            "record_id": record_id,
        }


    def _flush_to_disk(self) -> None:
        """Write records to JSON + CSV files."""
        try:
            # serializable = [self._serialize_record(r) for r in records_copy]
            # save to json
            with open(self._eval_json_file, 'w', encoding='utf-8') as f:
                json.dump(self._eval_records, f, ensure_ascii=False, indent=2)

            # if fmt in ('csv', 'both'):
            #     csv_path = f"{self._save_path}.csv"
            with open(self._eval_csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(self.CSV_HEADERS)
                for record in self._eval_records:
                    csv_row = self._record_to_csv_row(record)
                    # self.logger.info(f"csv row: {csv_row}")
                    writer.writerow(csv_row)

            # self.logger.debug(f"EvalLogRecorder: flushed {len(records_copy)} records to {self._save_path}")
        except Exception as e:
            self.logger.exception(f"EvaluationResultRecorder: flush failed: {e}")

    def _record_to_csv_row(self, record: Dict[str, Any]) -> list:
        # s = self._serialize_record(r)
        def _average(data_list: List[float], decimal_places:int = 3) -> float:
            """
            Calculate the average value of the numbers in the list.
            
            Args:
                data_list: A list containing integers or floats.

            Returns:
                float or int: The calculated average value.
                None: Returns None if the list is empty.
            """
            # 1. Check if the list is empty
            if not data_list:
                # print("Warning: List is empty, cannot calculate average") # Uncomment to print log if needed
                return 0.0

            # 2. Calculate the sum and length
            total = sum(data_list)
            count = len(data_list)

            # 3. Return the average
            return round(total / count, decimal_places)

        return [
            record.get('id', ''),
            record.get('task_id', ''),
            record.get('sub_task_id', 0) + 1 if record.get('sub_task_id', 0) is not None else 1,
            record.get('instruction', ''),
            record.get('start_time', ''),
            record.get('end_time', ''),
            record.get('duration', ''),
            record.get('score', None),
            record.get('note', ''),
            record.get('episode_id', -1),
            record.get('mode', ''),
            record.get('wait_time', 0),
            record.get('control_period', 0),
            record.get('control_speed', 1.0),
            record.get('inter_chunk_mode', ''),
            record.get('intra_chunk_mode', ''),
            record.get('model_type', ''),
            record.get('model_path', ''),
            record.get('obv_count', -1),
            _average(record.get('obv_fps', []), 3),
            len(record.get('infer_count', [])),
            _average(record.get('img_proc_time', []), 3),
            round(_average(record.get('avg_infer_time', []), 6) * 1000, 3),
            round(_average(record.get('avg_intra_traj_time', []), 6) * 1000, 3),
            round(_average(record.get('avg_inter_traj_time', []), 6) * 1000, 3),
            round(_average(record.get('avg_comm_time', []), 6) * 1000, 3),
        ]

    def close(self) -> None:
        """Close recorder: finalize running records, flush, stop threads."""
        if self._closed:
            return
        self._closed = True

        self._flush_to_disk()

if __name__ == "__main__":
    pass