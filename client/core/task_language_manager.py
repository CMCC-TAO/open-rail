import json
import logging
import os
import numpy as np
from collections import deque
from typing import Deque, Dict, List, Optional
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
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.task_language_map: Dict[str, List[str]] = self._load_task_language_map(
            getattr(self.config, "file_path", "")
        )
        self.currt_language_instruction: str = self._sync_language_from_config()
        self.task_progress_queue: Deque[float] = deque()
        self.ready_for_advance: bool = True
        self.sub_task_id_tmp: int = int(getattr(self.config, "sub_task_id", 0))
        self.logger.info(f"Task language manager inited. tasks={self.task_language_map}, currt_language_instruction={self.currt_language_instruction}")

    def _resolve_task_file_path(self, file_path: str) -> str:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return file_path if os.path.isabs(file_path) else os.path.join(root_dir, "conf", file_path)

    def _load_task_language_map(self, file_path: str) -> Dict[str, List[str]]:
        target_path = self._resolve_task_file_path(file_path)
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return {"Default": [x for x in data if isinstance(x, str)]}
            if isinstance(data, dict):
                return {
                    k: [x for x in v if isinstance(x, str)]
                    for k, v in data.items()
                    if isinstance(v, list)
                }
        except Exception as e:
            self.logger.warning(
                f"Failed to load language command file: {target_path}, error: {e}"
            )
        return {}

    def _sync_language_from_config(self) -> str:
        """Sync current language text from config.task_id/sub_task_id."""
        task_id = getattr(self.config, "task_id", "")
        sub_task_id = int(getattr(self.config, "sub_task_id", 0))
        task_cmds = self.task_language_map.get(task_id, [])

        if not task_cmds and self.task_language_map:
            task_id = next(iter(self.task_language_map.keys()))
            self.config.task_id = task_id
            task_cmds = self.task_language_map.get(task_id, [])

        if not task_cmds:
            self.config.sub_task_id = 0
            return ""

        sub_task_id = max(0, min(sub_task_id, len(task_cmds) - 1))
        self.config.sub_task_id = sub_task_id
        return task_cmds[sub_task_id]

    def advance_subtask(self) -> None:
        """Advance sub task id cyclically under current task and return language."""
        # Check if ready for advance based on task progress
        if self.ready_for_advance:
            avg_task_progress = self._average_task_progress(win_size=self.config.task_progress_win_size if hasattr(self.config, "task_progress_win_size") else 10)
            # self.logger.debug(f"Avg task progress: {avg_task_progress:.2f}")
            task_progress_threshold = getattr(self.config, "task_progress_threshold", 0.9)
            if avg_task_progress >= task_progress_threshold:
                self.ready_for_advance = False  # Reset advance flag until next threshold is reached
                self.logger.info(f"Task progress threshold reached: {avg_task_progress:.2f} > {task_progress_threshold:.2f}, advance to next subtask.")
                task_id = getattr(self.config, "task_id", "")
                task_cmds = self.task_language_map.get(task_id, [])
                if not task_cmds:
                    return 

                sub_task_id = int(getattr(self.config, "sub_task_id", 0))
                sub_task_id = (sub_task_id + 1) % len(task_cmds)
                self.sub_task_id_tmp = sub_task_id
                self.currt_language_instruction = task_cmds[sub_task_id]
            # else:
            #     self.logger.debug(f"Not ready for advance. Avg task progress: {avg_task_progress:.2f}")
            #     return  # Not ready to advance yet
        # return self.currt_language_instruction

    def reload(self) -> None:
        """Reload task file and re-sync language from current config."""
        self.task_language_map = self._load_task_language_map(getattr(self.config, "file_path", ""))
        self.currt_language_instruction = self._sync_language_from_config()

    def add_task_progress(self, progress: float) -> None:
        """Add a new task progress value to the queue."""
        self.task_progress_queue.append(progress)

    def reset_task_progress(self, language_instruction: str, task_progress_next: np.array) -> None:
        """After advanced to next sub-task, clear task progress queue and wait for advancing again."""
        if self.ready_for_advance == False and language_instruction == self.currt_language_instruction:
            # Compute task progress for the next sub-task based on the provided task_progress_next array
            length = min(len(task_progress_next), getattr(self.config, "task_progress_win_size", 10))
            avg_task_progress_next = np.mean(task_progress_next[:length]) if length > 0 else 0.0
            if avg_task_progress_next < getattr(self.config, "task_progress_threshold", 0.9) / 10:
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
