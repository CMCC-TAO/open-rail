import json
import logging
import os
from typing import Dict, List, Optional
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

    def advance_subtask(self) -> str:
        """Advance sub task id cyclically under current task and return language."""
        task_id = getattr(self.config, "task_id", "")
        task_cmds = self.task_language_map.get(task_id, [])
        if not task_cmds:
            return self.currt_language_instruction

        sub_task_id = int(getattr(self.config, "sub_task_id", 0))
        sub_task_id = (sub_task_id + 1) % len(task_cmds)
        self.config.sub_task_id = sub_task_id
        self.currt_language_instruction = task_cmds[sub_task_id]
        return self.currt_language_instruction

    def reload(self) -> None:
        """Reload task file and re-sync language from current config."""
        self.task_language_map = self._load_task_language_map(getattr(self.config, "file_path", ""))
        self.currt_language_instruction = self._sync_language_from_config()
    
    def get_current_language(self) -> str:
        """Get current language instruction."""
        return self.currt_language_instruction
