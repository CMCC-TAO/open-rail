import json
import logging
import os
import numpy as np
from collections import deque
from typing import Deque, Dict, List, Optional, Any
from ml_collections import ConfigDict


class TaskLanguageManager:
    """Manage language tasks and current language text from language config."""

    def __init__(self, config: ConfigDict):
        """
        Args:
            language_config: config object compatible with attribute access,
                expected fields: file_path, task_id, sub_task_id.
            logger: optional logger; uses module logger when not provided.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._check_config()

        self.task_language_map: Dict[str, List[str]] = self._load_task_language_map(self.config.file_path)
        self.currt_language_instruction: str = self._get_current_language_instruction()
        self.task_progress_queue: Deque[float] = deque()
        self.ready_for_advance: bool = True
        self.sub_task_id_tmp: int = int(self.config.sub_task_id)
        self.logger.info(f"Task language manager inited. tasks={self.task_language_map}, currt_language_instruction={self.currt_language_instruction}")

    def _check_config(self):
        """
        Validates the configuration and ensures all required fields exist.
        
        If any of the following fields are missing from `self.config`, they will be 
        initialized with their respective default values, and a warning will be logged:
        
        - task_id (str): Defaults to "default_task".
        - sub_task_id (int): Defaults to 0.
        - auto_mode (bool): Defaults to False.
        - file_path (str): Defaults to "language_cmd.json".
        - task_progress_threshold (float): Defaults to 0.9.
        - task_progress_win_size (int): Defaults to 10.
        """
        # Ensure task_id exists; set to empty string if missing
        if not hasattr(self.config, "task_id"):
            setattr(self.config, "task_id", "default_task")
            self.logger.warning("Missing 'task_id' in config, set default to 'default_task'.")
            
        # Ensure sub_task_id exists; set to 0 if missing
        if not hasattr(self.config, "sub_task_id"):
            setattr(self.config, "sub_task_id", 0)
            self.logger.warning("Missing 'sub_task_id' in config, set default to 0.")
        
        # Ensure auto_mode exists; set to False if missing
        if not hasattr(self.config, "auto_mode"):
            setattr(self.config, "auto_mode", False)
            self.logger.warning("Missing 'auto_mode' in config, set default to False.")

        # Ensure file_path exists; set to empty string if missing
        if not hasattr(self.config, "file_path"):
            setattr(self.config, "file_path", "language_cmd.json")
            self.logger.warning("Missing 'file_path' in config, set default to 'language_cmd.json'.")

        # Ensure task_progress_threshold exists; set to 0.9 if missing
        if not hasattr(self.config, "task_progress_threshold"):
            setattr(self.config, "task_progress_threshold", 0.9)
            self.logger.warning("Missing 'task_progress_threshold' in config, set default to 0.9.")

        # Ensure task_progress_win_size exists; set to 10 if missing
        if not hasattr(self.config, "task_progress_win_size"):
            setattr(self.config, "task_progress_win_size", 10)
            self.logger.warning("Missing 'task_progress_win_size' in config, set default to 10.")

    def reset(self) -> None:
        self.sub_task_id_tmp = 0
        self.config.sub_task_id = 0
        self.task_progress_queue.clear()
        self.ready_for_advance=True
        self.currt_language_instruction: str = self._get_current_language_instruction()
    def _resolve_task_file_path(self, file_path: str) -> str:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return file_path if os.path.isabs(file_path) else os.path.join(root_dir, "conf", file_path)
    
    def _load_task_language_map(self, file_path: str) -> Dict[str, List[str]]:
            target_path = self._resolve_task_file_path(file_path)
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                self.logger.exception(f"Failed to load language command file: {target_path}, error: {e}")
                return {}

            def normalize_to_str_list(value: Any) -> Optional[List[str]]:
                """Normalize the input value to a list containing only strings; return None if conversion fails."""
                # 1. If it's already a list, filter out non-string elements

                if isinstance(value, list):
                    filtered = [x for x in value if isinstance(x, str)]
                    return filtered if filtered else None
                
                # 2. Handle the case of a single string by wrapping it in a single-element list
                if isinstance(value, str):
                    return [value]
                
                # 3. For other types (e.g., int, float, None), return None as they are incompatible
                return None

            if isinstance(data, list):
                result = normalize_to_str_list(data)
                self.logger.warning(f"Return default task for list data.")
                return {"default_task": result} if result else {}

            if isinstance(data, dict):
                return {
                    k: normalized_v
                    for k, v in data.items()
                    if (normalized_v := normalize_to_str_list(v)) is not None
                }

            self.logger.warning(f"Failed to load task language map and return empty dict.")
            return {}

    def _get_current_language_instruction(self) -> str:
        """Sync current language text from config.task_id/sub_task_id."""
        # Check if task_language_map is empty first
        if not self.task_language_map:
            self.logger.warning("Task language map is empty, returning empty string.")
            self.config.sub_task_id = 0
            return ""

        task_id = self.config.task_id
        sub_task_id = int(self.config.sub_task_id)
        task_cmds = self.task_language_map.get(task_id, [])

        # If no commands found for the current task_id but task_language_map is not empty,
        # use the first available task_id
        if not task_cmds:
            fallback_task_id = next(iter(self.task_language_map.keys()))
            self.logger.warning(f"No commands found for task_id '{task_id}', falling back to '{fallback_task_id}'.")
            self.config.task_id = fallback_task_id
            task_cmds = self.task_language_map.get(fallback_task_id, [])

        # Ensure sub_task_id is within valid range
        sub_task_id = max(0, min(sub_task_id, len(task_cmds) - 1))
        self.config.sub_task_id = sub_task_id
        self.logger.debug(f"Synchronized language instruction for task_id='{self.config.task_id}', sub_task_id={self.config.sub_task_id}.")
        return task_cmds[sub_task_id]

    def advance_subtask(self) -> None:
        """Advance sub task id cyclically under current task and return language."""
        # Check if ready for advance based on task progress
        if self.ready_for_advance:
            avg_task_progress = self._average_task_progress(win_size=self.config.task_progress_win_size)
            # self.logger.debug(f"Avg task progress: {avg_task_progress:.2f}")
            if avg_task_progress >= self.config.task_progress_threshold:
                self.ready_for_advance = False  # Reset advance flag until next threshold is reached
                self.logger.info(f"Task progress threshold reached: {avg_task_progress:.2f} > {self.config.task_progress_threshold:.2f}, advance to next subtask.")

                self.config.sub_task_id += 1
                self.currt_language_instruction = self._get_current_language_instruction()
                self.sub_task_id_tmp = self.config.sub_task_id
        # return self.currt_language_instruction

    def reload(self) -> None:
        """Reload task file and re-sync language from current config."""
        self.task_language_map = self._load_task_language_map(self.config.file_path)
        self.currt_language_instruction = self._get_current_language_instruction()

    def add_task_progress(self, progress: float) -> None:
        """Add a new task progress value to the queue."""
        self.task_progress_queue.append(progress)

    def reset_task_progress(self, language_instruction: str, task_progress_next: np.array) -> None:
        """After advanced to next sub-task, clear task progress queue and wait for advancing again."""
        if self.ready_for_advance == False and language_instruction == self.currt_language_instruction:
            # Compute task progress for the next sub-task based on the provided task_progress_next array
            length = min(len(task_progress_next), self.config.task_progress_win_size)
            avg_task_progress_next = np.mean(task_progress_next[:length]) if length > 0 else 0.0
            if avg_task_progress_next < self.config.task_progress_threshold / 10.0:
                # Only reset if the next sub-task progress is very low, indicating a new sub-task has started
                self.logger.info(f"Resetting task progress for next subtask. Initial avg progress: {avg_task_progress_next:.2f}")
                self.config.sub_task_id = self.sub_task_id_tmp  # Sign the sub_task_id to the new one
                self.task_progress_queue.clear()
                self.ready_for_advance = True

    def _average_task_progress(self, win_size: int) -> float:
        """Return average of the latest win_size task progress values, or 0.0 if not enough data."""
        # print(f"Debug: window size for average task progress: {win_size}")
        if len(self.task_progress_queue) < win_size:
            return 0.0
        latest_values = list(self.task_progress_queue)[-win_size:]
        return sum(latest_values) / win_size
    
    def get_current_language(self) -> str:
        """Get current language instruction."""
        return self.currt_language_instruction
