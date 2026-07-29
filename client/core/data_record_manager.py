import os
import re
import json
import cv2
import csv
import time
import logging
import threading
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from queue import Empty
from pathlib import Path
from datetime import datetime
from collections import deque
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Manager,Queue
from typing import Any, Dict, List, Optional, Union
from client.utils.util import run_time_decorator
class LeRobotDatasetParser:
    """Parse LeRobot dataset episodes from one task recording directory."""

    def __init__(self, dataset_root: str, logger: Optional[logging.Logger] = None) -> None:
        self.dataset_root = Path(dataset_root)
        self.logger = logger or logging.getLogger(__name__)
        self.meta_dir = self.dataset_root / "meta"
        self.data_dir = self.dataset_root / "data"
        self.info = self._load_info()
        self.fps = int(self.info.get("fps", 30) or 30)
        self.chunks_size = int(self.info.get("chunks_size", 1000) or 1000)
        self.video_keys = self._get_video_keys(self.info)
        self.episode_length_map = self._load_episode_length_map()

    def _load_info(self) -> dict:
        info_path = self.meta_dir / "info.json"
        if not info_path.exists():
            return {}
        try:
            with info_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self.logger.warning("Failed to parse info.json: %s", info_path, exc_info=True)
            return {}

    def _load_episode_length_map(self) -> Dict[int, int]:
        episodes_path = self.meta_dir / "episodes.jsonl"
        mapping: Dict[int, int] = {}
        if not episodes_path.exists():
            return mapping
        try:
            with episodes_path.open("r", encoding="utf-8") as f:
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
    def _get_video_keys(info: dict) -> List[str]:
        features = info.get("features", {}) if isinstance(info, dict) else {}
        keys: List[str] = []
        for key, value in features.items():
            if isinstance(value, dict) and value.get("dtype") == "video":
                keys.append(key)
        return keys

    def _parquet_num_rows(self, parquet_path: Path) -> int:
        try:
            return int(pq.ParquetFile(parquet_path).metadata.num_rows)
        except Exception:
            return 0

    def _video_exists(self, chunk_id: int, episode_index: int, video_key: str) -> bool:
        video_fmt = self.info.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )
        rel = video_fmt.format(
            episode_chunk=chunk_id,
            episode_index=episode_index,
            video_key=video_key,
        )
        return (self.dataset_root / rel).exists()

    def get_chunk_ids(self) -> List[int]:
        if not self.data_dir.exists():
            return []
        ids: List[int] = []
        for p in self.data_dir.iterdir():
            if not p.is_dir():
                continue
            m = re.fullmatch(r"chunk-(\d{3})", p.name)
            if not m:
                continue
            ids.append(int(m.group(1)))
        return sorted(set(ids))

    def parse_episode_records(self, chunk_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.data_dir.exists():
            return []

        pattern = re.compile(r"chunk-(\d{3})/episode_(\d{6})\.parquet$")
        meta_ok = all((self.meta_dir / name).exists() for name in ("info.json", "episodes.jsonl", "tasks.jsonl"))
        records: List[Dict[str, Any]] = []

        for parquet_path in self.data_dir.rglob("episode_*.parquet"):
            rel_data = parquet_path.relative_to(self.data_dir).as_posix()
            m = pattern.search(rel_data)
            if not m:
                continue
            cur_chunk_id = int(m.group(1))
            if chunk_id is not None and cur_chunk_id != int(chunk_id):
                continue

            episode_index = int(m.group(2))
            frames = int(self.episode_length_map.get(episode_index, self._parquet_num_rows(parquet_path)))
            duration_sec = round((frames / self.fps), 1) if self.fps > 0 else 0.0
            videos_ok = all(self._video_exists(cur_chunk_id, episode_index, key) for key in self.video_keys)

            records.append({
                "id": f"chunk-{cur_chunk_id:03d}/episode_{episode_index:06d}",
                "name": f"episode_{episode_index:06d}",
                "chunk": cur_chunk_id,
                "chunk_str": f"{cur_chunk_id:03d}",
                "episode_index": episode_index,
                "frames": frames,
                "duration_sec": duration_sec,
                "parquet_relpath": str(parquet_path.relative_to(self.dataset_root)),
                "complete": bool(meta_ok and videos_ok),
            })

        records.sort(key=lambda x: x["episode_index"], reverse=True)
        return records

    @staticmethod
    def _parse_episode_id(episode_id: str) -> tuple[int, int]:
        m = re.fullmatch(r"chunk-(\d{3})/episode_(\d{6})", str(episode_id or "").strip())
        if not m:
            raise ValueError(f"Invalid episode id: {episode_id}")
        return int(m.group(1)), int(m.group(2))

    def delete_episode(self, episode_id: str) -> Dict[str, Any]:
        chunk_id, episode_index = self._parse_episode_id(episode_id)

        parquet_path = self.data_dir / f"chunk-{chunk_id:03d}" / f"episode_{episode_index:06d}.parquet"
        removed_paths: List[str] = []

        if parquet_path.exists():
            parquet_path.unlink()
            removed_paths.append(str(parquet_path.relative_to(self.dataset_root)))

        video_fmt = self.info.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )
        for video_key in self.video_keys:
            rel = video_fmt.format(
                episode_chunk=chunk_id,
                episode_index=episode_index,
                video_key=video_key,
            )
            video_path = self.dataset_root / rel
            if video_path.exists():
                video_path.unlink()
                removed_paths.append(str(video_path.relative_to(self.dataset_root)))

        episodes_path = self.meta_dir / "episodes.jsonl"
        remaining_episode_rows: List[Dict[str, Any]] = []
        removed_meta_rows = 0
        if episodes_path.exists():
            with episodes_path.open("r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s:
                        continue
                    try:
                        row = json.loads(s)
                    except Exception:
                        continue
                    if int(row.get("episode_index", -1)) == episode_index:
                        removed_meta_rows += 1
                        continue
                    remaining_episode_rows.append(row)

        with episodes_path.open("w", encoding="utf-8") as f:
            for row in remaining_episode_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        remaining_indices = sorted({int(r.get("episode_index", -1)) for r in remaining_episode_rows if int(r.get("episode_index", -1)) >= 0})
        remaining_frames = sum(max(0, int(r.get("length", 0) or 0)) for r in remaining_episode_rows)
        next_episode_index = (max(remaining_indices) + 1) if remaining_indices else 0
        splits_text = "0:-1" if next_episode_index <= 0 else f"0:{next_episode_index - 1}"

        info_path = self.meta_dir / "info.json"
        info = self._load_info()
        info["total_episodes"] = int(next_episode_index)
        info["total_frames"] = int(remaining_frames)
        info["total_videos"] = int(len(remaining_indices) * len(self.video_keys))
        info["total_chunks"] = int(len(self.get_chunk_ids()))
        info["splits"] = {"test": splits_text}
        with info_path.open("w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        self.info = info
        self.episode_length_map = {
            int(r.get("episode_index", -1)): int(r.get("length", 0) or 0)
            for r in remaining_episode_rows
            if int(r.get("episode_index", -1)) >= 0
        }

        deleted = bool(removed_paths or removed_meta_rows > 0)
        return {
            "deleted": deleted,
            "episode_id": f"chunk-{chunk_id:03d}/episode_{episode_index:06d}",
            "removed_file_count": len(removed_paths),
            "removed_meta_count": removed_meta_rows,
            "removed_paths": removed_paths,
        }

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

        # Runtime cache for episode browsing in memory.
        self._dataset_root: Optional[Path] = None
        self._meta_dir: Optional[Path] = None
        self._data_dir: Optional[Path] = None
        self._browse_task_name: str = ""
        self._browse_task_dir: str = ""
        self._browse_cache_loaded: bool = False
        self._browse_info: Dict[str, Any] = {}
        self._browse_fps: int = 30
        self._browse_chunks_size: int = 1000
        self._browse_video_keys: List[str] = []
        self._browse_episode_length_map: Dict[int, int] = {}
        self._browse_episode_records: List[Dict[str, Any]] = []

        self._parse_config(lerobot_config)
        # self.record_executor = ThreadPoolExecutor(max_workers=1) # max_workers must be 1 to ensure sequence of recording

    def _check_meta_path_and_dir(self, save_path: str) -> bool:
        self.meta_dir = os.path.join(save_path, 'meta')
        # self.logger.info(f"_check_meta_path_and_dir: save_dir={self.save_dir!r}, save_path={self.save_path!r}, meta_dir={self.meta_dir!r}")

        if not os.path.exists(self.meta_dir):
            os.makedirs(self.meta_dir, exist_ok=True)
            self.logger.info(f"{self.meta_dir} not exists, create it")
            return False
        return self._check_required_meta_files()

    def _check_required_meta_files(self, required_files: List[str] = ['info.json', 'episodes.jsonl', 'tasks.jsonl']) -> bool:
        # Check for required files
        missing_files = []

        for filename in required_files:
            file_path = os.path.join(self.meta_dir, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        # Raise error if any required file is missing
        if missing_files:
            self.logger.warning(f"{self.meta_dir} is missing the following required files: {', '.join(missing_files)}")
            # assert False, "Missing required meta files."
            return False
        else:
            return True
    def set_task(self, save_path: str) -> None:
        self.save_path = save_path
        # Keep current task path for fast in-memory browsing.
        self._set_browse_task_from_path(save_path)
        meta_required_file_exists = self._check_meta_path_and_dir(save_path=save_path)
        if meta_required_file_exists:
            self._update_config_from_meta_file()
        else:
            self.config["total_episodes"] = 0
            self.config["total_frames"] = 0
            self.config["total_videos"] = 0
            self.config['chunks_size'] = 1000

        # Always refresh browse cache through the shared meta-loading interface.
        self._browse_cache_loaded = False
        self._ensure_browse_data_loaded()
        return self.config["total_frames"], self.config["total_videos"], self.config["total_episodes"], self.config['chunks_size']
    

    def _set_browse_task_from_path(self, save_path: str) -> None:
        """Update recorder browsing target and clear cache if task path changes."""
        task_dir = Path(save_path).resolve()
        task_name = task_dir.name
        task_dir_str = str(task_dir)

        if self._browse_task_dir != task_dir_str:
            self._browse_cache_loaded = False
            self._browse_episode_records = []

        self._browse_task_name = task_name
        self._browse_task_dir = task_dir_str
        self._dataset_root = task_dir
        self._meta_dir = task_dir / "meta"
        self._data_dir = task_dir / "data"

    def _resolve_task_dir(self, selected_task: Optional[str], base_dir: Optional[Union[str, Path]] = None) -> Path:
        """Resolve dataset task directory from selected_task or current recorder state."""
        if selected_task and str(selected_task).strip():
            if base_dir is not None:
                return Path(base_dir).resolve() / str(selected_task).strip()
            if self._dataset_root is not None and self._dataset_root.parent.exists():
                return self._dataset_root.parent / str(selected_task).strip()
        if self._dataset_root is None:
            raise ValueError("Task directory is not initialized. Call set_task() first.")
        return self._dataset_root

    def _reload_browse_state(self) -> None:
        """Reload browse metadata and episode records using a shared meta-loading path."""
        self._browse_info = self._load_browse_info()
        self._browse_fps = int(self._browse_info.get("fps", 30) or 30)
        self._browse_chunks_size = int(self._browse_info.get("chunks_size", 1000) or 1000)
        self._browse_video_keys = self._get_browse_video_keys(self._browse_info)
        self._browse_episode_length_map = self._load_browse_episode_length_map()
        self._browse_episode_records = self._build_episode_records()
        self._browse_cache_loaded = True

    def _ensure_browse_data_loaded(self, selected_task: Optional[str] = None, base_dir: Optional[Union[str, Path]] = None) -> None:
        """Load episode metadata and records when task changes or cache is empty."""
        task_dir = self._resolve_task_dir(selected_task=selected_task, base_dir=base_dir).resolve()
        task_name = task_dir.name

        should_reload = (
            (not self._browse_cache_loaded)
            or (task_name != self._browse_task_name)
            or (str(task_dir) != self._browse_task_dir)
        )
        if not should_reload:
            return

        self._set_browse_task_from_path(str(task_dir))
        self._reload_browse_state()

    def _load_browse_info(self) -> Dict[str, Any]:
        info_path = self._meta_dir / "info.json"
        if not info_path.exists():
            return {}
        try:
            with info_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self.logger.warning("Failed to parse info.json: %s", info_path, exc_info=True)
            return {}

    def _load_browse_episode_length_map(self) -> Dict[int, int]:
        episodes_path = self._meta_dir / "episodes.jsonl"
        mapping: Dict[int, int] = {}
        if not episodes_path.exists():
            return mapping
        try:
            with episodes_path.open("r", encoding="utf-8") as f:
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
    def _get_browse_video_keys(info: Dict[str, Any]) -> List[str]:
        features = info.get("features", {}) if isinstance(info, dict) else {}
        keys: List[str] = []
        for key, value in features.items():
            if isinstance(value, dict) and value.get("dtype") == "video":
                keys.append(key)
        return keys

    @staticmethod
    def _parse_episode_id(episode_id: str) -> tuple[int, int]:
        m = re.fullmatch(r"chunk-(\d{3})/episode_(\d{6})", str(episode_id or "").strip())
        if not m:
            raise ValueError(f"Invalid episode id: {episode_id}")
        return int(m.group(1)), int(m.group(2))

    def _browse_parquet_num_rows(self, parquet_path: Path) -> int:
        try:
            return int(pq.ParquetFile(parquet_path).metadata.num_rows)
        except Exception:
            return 0

    def _browse_video_exists(self, chunk_id: int, episode_index: int, video_key: str) -> bool:
        video_fmt = self._browse_info.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )
        rel = video_fmt.format(
            episode_chunk=chunk_id,
            episode_index=episode_index,
            video_key=video_key,
        )
        return (self._dataset_root / rel).exists()

    def _build_episode_records(self) -> List[Dict[str, Any]]:
        if self._data_dir is None or (not self._data_dir.exists()):
            return []

        pattern = re.compile(r"chunk-(\d{3})/episode_(\d{6})\.parquet$")
        meta_ok = all((self._meta_dir / name).exists() for name in ("info.json", "episodes.jsonl", "tasks.jsonl"))
        records: List[Dict[str, Any]] = []

        for parquet_path in self._data_dir.rglob("episode_*.parquet"):
            rel_data = parquet_path.relative_to(self._data_dir).as_posix()
            m = pattern.search(rel_data)
            if not m:
                continue

            cur_chunk_id = int(m.group(1))
            episode_index = int(m.group(2))
            frames = int(self._browse_episode_length_map.get(episode_index, self._browse_parquet_num_rows(parquet_path)))
            duration_sec = round((frames / self._browse_fps), 1) if self._browse_fps > 0 else 0.0
            videos_ok = all(self._browse_video_exists(cur_chunk_id, episode_index, key) for key in self._browse_video_keys)

            records.append({
                "id": f"chunk-{cur_chunk_id:03d}/episode_{episode_index:06d}",
                "name": f"episode_{episode_index:06d}",
                "chunk": cur_chunk_id,
                "chunk_str": f"{cur_chunk_id:03d}",
                "episode_index": episode_index,
                "frames": frames,
                "duration_sec": duration_sec,
                "parquet_relpath": str(parquet_path.relative_to(self._dataset_root)),
                "complete": bool(meta_ok and videos_ok),
            })

        records.sort(key=lambda x: x["episode_index"], reverse=True)
        return records

    def _build_episode_record(self, chunk_id: int, episode_index: int, frames: int, complete: bool) -> Dict[str, Any]:
        duration_sec = round((max(0, int(frames)) / self._browse_fps), 1) if self._browse_fps > 0 else 0.0
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

    def _upsert_browse_episode_record(self, record: Dict[str, Any]) -> None:
        """Insert or replace one episode record in browse cache."""
        target_id = str(record.get("id", ""))
        replaced = False
        for idx, item in enumerate(self._browse_episode_records):
            if str(item.get("id", "")) == target_id:
                self._browse_episode_records[idx] = record
                replaced = True
                break
        if not replaced:
            self._browse_episode_records.append(record)
        self._browse_episode_records.sort(key=lambda x: int(x.get("episode_index", -1)), reverse=True)

    def _sync_browse_on_record_start(self, episode_chunk: int, episode_index: int) -> None:
        """Update in-memory meta/episode cache immediately when recording starts."""
        self._ensure_browse_data_loaded()

        self._browse_episode_length_map[int(episode_index)] = 0
        pending_record = self._build_episode_record(
            chunk_id=int(episode_chunk),
            episode_index=int(episode_index),
            frames=0,
            complete=False,
        )
        self._upsert_browse_episode_record(pending_record)

        total_episodes = int(self._browse_info.get("total_episodes", 0) or 0)
        self._browse_info["total_episodes"] = max(total_episodes, int(episode_index) + 1)
        self._browse_info["total_chunks"] = max(int(self._browse_info.get("total_chunks", 0) or 0), int(episode_chunk) + 1)

    def _sync_browse_on_record_end(self, episode_chunk: int, episode_index: int, episode_length: int, total_episodes: int, total_frames: int, total_videos: int) -> None:
        """Update in-memory meta/episode cache immediately when recording ends."""
        self._ensure_browse_data_loaded()

        self._browse_episode_length_map[int(episode_index)] = int(max(0, int(episode_length)))
        finished_record = self._build_episode_record(
            chunk_id=int(episode_chunk),
            episode_index=int(episode_index),
            frames=int(max(0, int(episode_length))),
            complete=True,
        )
        self._upsert_browse_episode_record(finished_record)

        self._browse_info["total_episodes"] = int(total_episodes)
        self._browse_info["total_frames"] = int(total_frames)
        self._browse_info["total_videos"] = int(total_videos)
        self._browse_info["total_chunks"] = max(int(self._browse_info.get("total_chunks", 0) or 0), int(episode_chunk) + 1)

    def parse_episode_records(self, chunk_id: Optional[int] = None, selected_task: Optional[str] = None, base_dir: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        """Return cached episode records for current task, or reload when selected_task changes."""
        self._ensure_browse_data_loaded(selected_task=selected_task, base_dir=base_dir)
        if chunk_id is None:
            return list(self._browse_episode_records)
        return [r for r in self._browse_episode_records if int(r.get("chunk", -1)) == int(chunk_id)]

    def delete_episode(self, episode_id: str, selected_task: Optional[str] = None, base_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Delete one episode and refresh in-memory cache."""
        self._ensure_browse_data_loaded(selected_task=selected_task, base_dir=base_dir)
        chunk_id, episode_index = self._parse_episode_id(episode_id)

        parquet_path = self._data_dir / f"chunk-{chunk_id:03d}" / f"episode_{episode_index:06d}.parquet"
        removed_paths: List[str] = []

        if parquet_path.exists():
            parquet_path.unlink()
            removed_paths.append(str(parquet_path.relative_to(self._dataset_root)))

        video_fmt = self._browse_info.get(
            "video_path",
            "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        )
        for video_key in self._browse_video_keys:
            rel = video_fmt.format(
                episode_chunk=chunk_id,
                episode_index=episode_index,
                video_key=video_key,
            )
            video_path = self._dataset_root / rel
            if video_path.exists():
                video_path.unlink()
                removed_paths.append(str(video_path.relative_to(self._dataset_root)))

        episodes_path = self._meta_dir / "episodes.jsonl"
        remaining_episode_rows: List[Dict[str, Any]] = []
        removed_meta_rows = 0
        if episodes_path.exists():
            with episodes_path.open("r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s:
                        continue
                    try:
                        row = json.loads(s)
                    except Exception:
                        continue
                    if int(row.get("episode_index", -1)) == episode_index:
                        removed_meta_rows += 1
                        continue
                    remaining_episode_rows.append(row)

        with episodes_path.open("w", encoding="utf-8") as f:
            for row in remaining_episode_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        remaining_indices = sorted({int(r.get("episode_index", -1)) for r in remaining_episode_rows if int(r.get("episode_index", -1)) >= 0})
        remaining_frames = sum(max(0, int(r.get("length", 0) or 0)) for r in remaining_episode_rows)
        next_episode_index = (max(remaining_indices) + 1) if remaining_indices else 0
        splits_text = "0:-1" if next_episode_index <= 0 else f"0:{next_episode_index - 1}"

        info_path = self._meta_dir / "info.json"
        info = self._load_browse_info()
        info["total_episodes"] = int(next_episode_index)
        info["total_frames"] = int(remaining_frames)
        info["total_videos"] = int(len(remaining_indices) * len(self._browse_video_keys))
        info["total_chunks"] = int(len({int(r.get("chunk", -1)) for r in self._browse_episode_records if int(r.get("chunk", -1)) >= 0 and int(r.get("episode_index", -1)) != episode_index}))
        info["splits"] = {"test": splits_text}
        with info_path.open("w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        # Refresh in-memory cache after file mutation.
        self._browse_cache_loaded = False
        self._ensure_browse_data_loaded(selected_task=selected_task, base_dir=base_dir)

        deleted = bool(removed_paths or removed_meta_rows > 0)
        return {
            "deleted": deleted,
            "episode_id": f"chunk-{chunk_id:03d}/episode_{episode_index:06d}",
            "removed_file_count": len(removed_paths),
            "removed_meta_count": removed_meta_rows,
            "removed_paths": removed_paths,
        }

    def _update_config_from_meta_file(self):
        """
        Checks whether the directory `self.meta_dir` exists.

        If it exists and contains required files (info.json, episodes.jsonl, tasks.jsonl),
        updates the configuration using these files. Otherwise, raises an error due to missing files.

        Raises:
            AssertionError: If any of the required files are missing in the existing directory.
        """
        

        # Load info.json and update dataset info
        info_file_path = os.path.join(self.meta_dir, 'info.json')
        self._update_dataset_info_from_meta_file(info_file_path)

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
        try:
            self.config['chunks_size'] = data['chunks_size']
            self.config['codebase_version'] = data['codebase_version']
            self.config['data_path'] = data['data_path']
            self.config['video_path'] = data['video_path']
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

    def begin_recording(self, episode_chunk: int = 0, episode_index: int = 0, total_frames: int = 0, total_videos: int = 0, save_raw: bool =True):
        self.episode_chunk = episode_chunk
        self.episode_index = episode_index
        self.total_frames = total_frames
        self.total_videos = total_videos
        self.save_raw = save_raw
        self.logger.info(f"episode_chunk={episode_chunk}, episode_index={episode_index}, total_frames={total_frames}")

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
    
    def end_record(self):
        try:
            self.record_executor.shutdown(wait=True) 
            finished_episode_index = self.episode_index
            finished_episode_chunk = self.episode_chunk

            self.episode_index = self.episode_index + 1
            self.total_frames = self.total_frames + self.frame_index
            self.total_videos = self.total_videos + len(self.camera_name_list)
            self._write_meta_files(total_frames=self.total_frames,
                                total_episodes=self.episode_index,
                                episode_length=self.frame_index,
                                total_videos=self.total_videos,
                                episode_task_list=self.episode_task_list)
            # stop recording for current episode: flush video/parquet after all queue data drained
            self.write_loop_done.set()
            self.write_parquet_thread.join()
            self._release_video_writers()
            self._release_parquet_writer()

            # Sync browse cache right after recording ends.
            self._sync_browse_on_record_end(
                episode_chunk=finished_episode_chunk,
                episode_index=finished_episode_index,
                episode_length=self.frame_index,
                total_episodes=self.episode_index,
                total_frames=self.total_frames,
                total_videos=self.total_videos,
            )
        except Exception as e:
            self.logger.exception(f"Finished recording failed: {e}")
        self.logger.info("Finish recording.")
        return self.episode_index, self.total_frames, self.total_videos
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

        try:
            # check action shape 
            if step_action.shape[0] < self.action_shape:
                step_action = np.concatenate([step_action, np.zeros(self.action_shape-step_action.shape[0])], axis=0)
            # check action shape 
            if step_state['obs.state'].shape[0] < self.state_shape:
                # self.logger.warning(f"obs shape {observation['obs.state'].shape[0]} is not correct, config shape is {self.state_shape}, add 0 to obs.state")
                # assert state['obs.state'].shape[0] <= self.state_shape, \
                # f"obs shape {state['obs.state'].shape[0]} is bigger than config shape {self.state_shape}"
                step_state['obs.state'] = np.concatenate([
                    step_state['obs.state'],
                    np.zeros(self.state_shape - step_state['obs.state'].shape[0], dtype=step_state['obs.state'].dtype)
                ], axis=0)
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
                raw_frame = step_state.get(camera_name)
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
            if self.frame_index % 30 == 0:
                self.logger.info(
                    f"write-loop progress: episode={self.episode_index}, "
                    f"frame_index={self.frame_index}, cached_records={len(self.parquet_frame_list)}"
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
        save_video_path = os.path.join(self.save_path, 'videos', f'chunk-{episode_chunk:03d}')
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
            self.save_path,
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
            

    def _write_meta_files(self, total_episodes: int, total_frames: int, episode_length: int, total_videos: int, episode_task_list: list[str]):
        """
        Writes metadata files including info.json, episodes.jsonl, and tasks.jsonl.

        These files contain global dataset statistics, per-episode information, and task mappings respectively.
        """
        try:
            # os.makedirs(self.meta_dir, exist_ok=True)
            # Write info.json file (always overwrite to keep metadata in sync)
            info_file_path = os.path.join(self.meta_dir, 'info.json')
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
            self.logger.exception(f"Exception in write_meta_files: {e}")

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
        record_id = 0
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
                self._clear_share_queue()
                self._enqueue_eval_record_crud(command="LoadRecords", record_id=-1, score=None, note="", task_path=task_path)
                clear = True
                append = True
            self._sync_eval_records_for_browse(timeout_s=0.05, max_empty_retries=5, clear=clear, append=append)
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
                    empty_count = 0  # Reset counter on successful fetch
                    
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

    # def _sync_browse_on_record_start(self, eval_record_id: int, sub_task_id: Optional[int] = None) -> None:
    #     """Sync main-process eval browse cache immediately when recording starts."""
    #     self._pending_record = {
    #         "id": int(eval_record_id),
    #         "sub_task_id": int(sub_task_id)+1 if sub_task_id is not None else None,
    #         "duration": 0.0,
    #         "score": None,
    #         "note": "",
    #     }
    #     self._upsert_eval_browse_record(self._pending_record)

    # def _sync_browse_on_record_end(self, duration: float) -> None:
    #     """Sync main-process eval browse cache immediately when recording ends."""
    #     if self._pending_record is not None:
    #         self._pending_record['duration'] = duration
    #     self._upsert_eval_browse_record(self._pending_record)
    #     self._pending_record = None

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
            self.logger.info(f"Eval directory already exists: {self._eval_dir}")

        return load_data

    def _load_existing_records(self) -> None:
        """Load existing records from eval_log.json; fallback to empty list. Called in writer process."""
        self._eval_records = []
        record_id = 0
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
                    record_id = max(int(r.get('id', -1)) for r in self._eval_records) + 1
        except Exception as e:
            self.logger.exception(f"Load eval_log.json failed: {e}")
            self._eval_records = []
            record_id = 0
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
                "sub_task_id": sub_task_id + 1 if sub_task_id else None,
                "duration": record.get("duration", None),
                "score": record.get("score", None),
                "note": record.get("note", ""),
            }
        # 1. Handle list of dict: iterate and put each record individually
        if isinstance(targets, list):
            for item in targets:
                if isinstance(item, dict):
                    self._eval_records_for_share.put(_convert_to_eval_record_for_browse(record=item))
                elif isinstance(item, int):
                    self._eval_records_for_share.put(item)
            return

        # 2. Handle single dict: put directly
        if isinstance(targets, dict):
            self._eval_records_for_share.put(_convert_to_eval_record_for_browse(record=targets))
            return

        # 3. Handle int (record_id for deletion): put directly
        if isinstance(targets, int):
            self._eval_records_for_share.put(targets)
            return

        self.logger.warning(f"Unsupported target type for _sync_eval_records_for_share: {type(targets)}")


    def _is_need_load(self, save_path: str) -> bool:
        """Return true when eval_dir assigned or changed. Called in main process."""
        need_load = False
        if self._eval_dir_for_browse is None or self._eval_dir_for_browse != os.path.join(save_path, 'eval'):
            need_load = True
            self._eval_dir_for_browse = os.path.join(save_path, 'eval')
        self.logger.info(f"Eval directory: {self._eval_dir_for_browse}, need_load: {need_load}")
        return need_load

    # def _load_existing_browse_records(self) -> None:
    #     """Load evaluation browse records using eval_log.json. Called in main process."""
    #     records: List[Dict[str, Any]] = []
    #     if self._eval_json_file_for_browse and os.path.exists(self._eval_json_file_for_browse):
    #         try:
    #             with open(self._eval_json_file_for_browse, 'r', encoding='utf-8') as f:
    #                 data = json.load(f)
    #             if isinstance(data, list):
    #                 for row in data:
    #                     if not isinstance(row, dict):
    #                         continue
    #                     records.append({
    #                         "id": int(row.get("id", -1)),
    #                         "sub_task_id": row.get("sub_task_id", None) + 1 if row.get("sub_task_id", None) else None,
    #                         "duration": row.get("duration", None),
    #                         "score": row.get("score", None),
    #                         "note": row.get("note", ""),
    #                     })
    #         except Exception:
    #             self.logger.warning("Failed to parse eval_log.json: %s", self._eval_json_file_for_browse, exc_info=True)

    #     records.sort(key=lambda x: int(x.get("id", -1)), reverse=True)
    #     self._eval_records_for_browse = records
    #     self.logger.info(f"Load eval records for browse successfully, eval_json_file = {self._eval_json_file_for_browse}, total records = {len(records)}")


    def begin_recording(self, eval_record_id: int):
        self._record_executor = ThreadPoolExecutor(max_workers=1) # max_workers must be 1 to ensure sequence of recording
        self._create_new_record(eval_record_id=eval_record_id)

    def _create_new_record(self, eval_record_id: int):
        self._obv_count = 0
        # self._eval_record_start_time = None
        self._current_record = {
            'id': eval_record_id,
            'task_id': None,
            'sub_task_id': None,
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

    def end_recording(self):
        record_id, duration = self._finalize_current_record()
        self._flush_to_disk()
        return record_id, duration
    
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
            if self._current_record['sub_task_id'] is None:
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
                self._create_new_record(record_id + 1)
                self._init_current_record(step_extra=step_extra)
        except KeyboardInterrupt:
            self.logger.warning("Child process detected keyboard interrupt, preparing to exit...")
        except Exception as e:
            self.logger.exception(f"Writing frame exited with exception: {e}")
            # self.release_writers()
        # finally:
            # self.logger.info("Writing frame exited.")
            # self.release_writers()
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
        self._sync_eval_records_for_share(targets=self._current_record)
    
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
        self._current_record['start_time'] = self._timestamp(self._eval_record_start_time)
        self._current_record['end_time'] = self._timestamp(self._eval_record_stop_time)
        self._current_record['duration'] = round(self._eval_record_stop_time - self._eval_record_start_time, 1)
        self._sync_eval_records_for_share(targets=self._current_record)
        return self._current_record['id'], self._current_record['duration']
    
    def _timestamp(self, time_stamp) -> str:
        dt = datetime.fromtimestamp(time_stamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    def pause(self) -> None:
        """Pause the timer for the currently running record."""
        pass
        # with self._lock:
        #     running = self._find_running_unlocked()
        #     if running is None or running.get('paused_at') is not None:
        #         return
        #     if running.get('status') != 'running':
        #         return
        #     running['paused_at'] = time.time()

    def resume(self) -> None:
        """Resume the timer for the currently paused record."""
        pass
        # with self._lock:
        #     running = self._find_running_unlocked()
        #     if running is None or running.get('paused_at') is None:
        #         return
        #     paused_at = float(running.pop('paused_at'))
        #     running['paused_s'] = round(float(running.get('paused_s', 0.0)) + (time.time() - paused_at), 1)

    def _enqueue_eval_record_crud(self, command: str, record_id: int, score: Optional[float] = None, note: str = "", task_path: str = "") -> None:
        """Publish one CRUD command to the shared queue for writer-side sync."""
        payload = {
            "command": command,
            "task_path": task_path,
            "record_id": int(record_id),
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
                self.logger.info(f"Load eval records CRUD command: {command}, task_path: {task_path}")
                return

        rec = next((r for r in self._eval_records if int(r.get('id', -1)) == record_id), None)
        if rec is None:
            self.logger.warning(f"Record with id {record_id} not found for CRUD command: {command}")
            return

        if command == "UpdateScore":
            rec['score'] = payload.get('score', None)
            self._sync_eval_records_for_share(targets=rec)
            self._flush_to_disk()
        elif command == "UpdateNote":
            rec['note'] = payload.get('note', "")
            self._sync_eval_records_for_share(targets=rec)
            self._flush_to_disk()
        elif command == "DeleteRecord":
            for i in range(len(self._eval_records) - 1, -1, -1):
                if int(self._eval_records[i].get('id', -1)) == record_id:
                    del self._eval_records[i]
                    self._sync_eval_records_for_share(targets=record_id)
                    self._flush_to_disk()
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
        # rec = next((r for r in self._eval_records_for_browse if r['id'] == record_id), None)
        # if rec is None:
        #     return
        # rec['score'] = score
        self._enqueue_eval_record_crud(command="UpdateScore", record_id=record_id, score=score, note="")
        return


    def set_note(self, record_id: int, note: str) -> None:
        # rec = next((r for r in self._eval_records_for_browse if r['id'] == record_id), None)
        # if rec is None:
        #     return
        # rec['note'] = note
        self._enqueue_eval_record_crud(command="UpdateNote", record_id=record_id, score=None, note=note)
        return


    def delete_record(self, record_id: int) -> None:
        # for i in range(len(self._eval_records_for_browse) - 1, -1, -1):
        #     if self._eval_records_for_browse[i].get('id') == record_id:
        #         del self._eval_records_for_browse[i]
        #         break
        self._enqueue_eval_record_crud(command="DeleteRecord", record_id=record_id, score=None, note="")
        return


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
                    writer.writerow(self._record_to_csv_row(record))

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
            record.get('sub_task_id', 0) + 1,
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
        self.current_task = None
        # print(f"Debug: record_config: {self.config}")
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
        # self.shared_data.start_write_time = self.manager.Value('b', False)
        # self.shared_data.stop = self.manager.Value('b', False)
        # self.shared_data.close = self.manager.Value('b', False)
        # self.shared_data.init_write = self.manager.Value('b', True)
        self.shared_data.total_frames = self.manager.Value('i', 0)
        self.shared_data.total_videos = self.manager.Value('i', 0)
        self.shared_data.episode_chunk = self.manager.Value('i', 0)
        self.shared_data.episode_index = self.manager.Value('i', 0)
        self.shared_data.eval_record_id = self.manager.Value('i', 0)
        self.shared_data.eval_record_duration = self.manager.Value('f', 0.0)
        self.shared_data.running = self.manager.Value('b', False)
        # self.shared_data.episode_parquet_list = self.manager.list()
        # self.shared_data.save_video_path_list = self.manager.list()
        # Task and language information storage
        # self.shared_data.episode_task_list = self.manager.list()
        # self.shared_data.task_language_dict = self.manager.dict()
    
    def _sanitize_task_name(self, task: Optional[str]) -> str:
        task_name = str(task).strip() if task is not None else ""
        if not task_name:
            task_name = "default"
        for ch in ('/', '\\', ' ', ':'):
            task_name = task_name.replace(ch, '_')
        return task_name

    def _build_full_save_path(self, save_dir: str, task: Optional[str]) -> str:
        self.project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        rel_save_dir = str(save_dir or "data/recording").strip().lstrip('/').lstrip('\\')
        date_str = datetime.now().strftime("%Y%m%d")
        task_name = self._sanitize_task_name(task)
        self.current_task = task_name
        return os.path.join(self.project_root_path, rel_save_dir, task_name + '_' + date_str)

    def set_task(self, task: str) -> None:
        """Update save path by task/date before a new recording starts. Called in the writer process."""
        # avoid reload data from file
        # if self.current_task == task:
        #     self.logger.warning(f"{self.current_task} is already set, return.")
        #     return
        # if self.shared_data.running.value:
        #     self.logger.warning("set_task ignored because recording is running")
        #     return

        self.current_task = task
        # if self.current_task == task_name and os.path.exists(os.path.join(self.project_root_path, self.save_dir, candidate_dir)):
        #     self.logger.info(f"set_task with the same task name {task_name} and existing directory, reuse it.")
        #     return
        self.save_dir = self.config.get("save_dir", "data/recording")     # relative path
        self.save_path = self._build_full_save_path(self.save_dir, task)  # full path
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
            self.logger.info(f"{self.save_path} not exists, create it")
        
        if self.config.get('is_record_episode', False):
            total_frames, total_videos, total_episodes, chunks_size = self.lerobot_recorder.set_task(save_path=self.save_path)
            self._sync_shared_data(total_frames=total_frames,
                                total_videos=total_videos,
                                total_episodes=total_episodes,
                                chunks_size=chunks_size)
        else:
            self.logger.info("Recording lerobot episode is disabled, skip recording.")
        
        if self.config.get('is_record_eval_log', False):
            self.eval_recorder.set_task(save_path=self.save_path, episode_id=self.shared_data.episode_index.value)
            # Keep next eval record id consistent across processes.
            self._sync_shared_data(eval_record_id = self.eval_recorder._record_id)
        else:
            self.logger.info("Recording evaluation log is disabled, skip recording.")
    
    def set_task_for_browse(self, task: str) -> None:
        """Update save path by task/date before a new recording starts. Called in the main process."""
        self.current_task = task
        self.save_dir = self.config.get("save_dir", "data/recording")     # relative path
        self.save_path = self._build_full_save_path(self.save_dir, task)  # full path
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
            self.logger.info(f"{self.save_path} not exists, create it")
        
        if self.config.get('is_record_episode', False):
            self.lerobot_recorder.set_task(save_path=self.save_path)
            # self._sync_shared_data(total_frames=total_frames,
            #                     total_videos=total_videos,
            #                     total_episodes=total_episodes,
            #                     chunks_size=chunks_size)
        else:
            self.logger.info("Recording lerobot episode is disabled, skip recording.")
        
        if self.config.get('is_record_eval_log', False):
            self.eval_recorder.set_task_for_browse(save_path=self.save_path)
            # Keep next eval record id consistent across processes.
            self._sync_shared_data(eval_record_id = self.eval_recorder._record_id)
        else:
            self.logger.info("Recording evaluation log is disabled, skip recording.")
    def _sync_shared_data(self, total_frames: int = None, total_videos: int = None, total_episodes: int = None, chunks_size: int = 1000, eval_record_id: int = None, eval_record_duration: float = None) -> None:
        """Sync record lerobot values to shared_data."""
        if total_frames is not None:
            self.shared_data.total_frames.value = total_frames
        if total_videos is not None:
            self.shared_data.total_videos.value = total_videos
        if total_episodes is not None:
            self.shared_data.episode_index.value = total_episodes
            self.shared_data.episode_chunk.value = total_episodes // chunks_size
        if eval_record_id is not None:
            self.shared_data.eval_record_id.value = eval_record_id
        if eval_record_duration is not None:
            self.shared_data.eval_record_duration.value = eval_record_duration
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
                    self.set_task(task = command.get("task_id", "default"))
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
    
    def start_recording(self, task_id: str):
        """
        Starts the recording process by dispatching write task in resident writer process.

        This method should be called before adding any observations or actions to ensure that
        the writer process is running and ready to handle incoming data.
        """
        try:
            session_id = self._bump_recording_session_id()
            self._clear_queues()

            # Keep main-process browse cache in sync immediately.
            # begin_recording() also runs inside writer subprocess, but subprocess memory
            # updates are not visible to the main process cache used by web APIs.
            self.set_task_for_browse(task=task_id)
            self.shared_data.running.value = True
            first_record = self._wait_for_record_data(get_timeout_s=0.05, max_attempts=20)
            if self.config.get('is_record_episode', False):
                self.lerobot_recorder._sync_browse_on_record_start(
                    episode_chunk=self.shared_data.episode_chunk.value,
                    episode_index=self.shared_data.episode_index.value,
                )
            if self.config.get('is_record_eval_log', False):
                if isinstance(first_record, tuple) and len(first_record) == 3:
                    _, _, step_extra = first_record
                    language_status = step_extra.get('language_status', {}) if isinstance(step_extra, dict) else {}
                    sub_task_id = language_status.get('sub_task_id', None)
                    self.eval_recorder._sync_browse_on_record_start(
                        eval_record_id=self.shared_data.eval_record_id.value,
                        sub_task_id=sub_task_id,
                    )
                    # if sub_task_id is not None:
                        # self.eval_recorder._sync_browse_on_runtime_step(
                        #     eval_record_id=self.shared_data.eval_record_id.value,
                        #     sub_task_id=sub_task_id,
                        # )
            command = {
                "command": "start",
                "task_id": task_id,
            }
            self.writer_command_queue.put(command)
            self.logger.info(f"Writer task dispatched successfully. session_id={session_id}")
        except Exception as e:
            self.logger.exception(f"Failed to start writer task: {e}")

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
        - Wait for resident writer task to exit naturally after flushing video/parquet.
        """
        # Capture snapshot before stop, used for main-process browse cache sync.
        prev_episode_index = int(self.shared_data.episode_index.value)
        prev_total_frames = int(self.shared_data.total_frames.value)

        # Invalidate future async tasks from next cycle; current queue will still be drained.
        stop_session_id = self._bump_recording_session_id()
        if self.shared_data.running.value:
            self.shared_data.running.value = False
            self.logger.info("Signaled writer task to stop after draining queue.")

        command = {
            "command": "stop",
        }
        self.writer_command_queue.put(command)

        # Sync browse cache in main process after writer updates shared counters.
        self._sync_browse_on_record_stop_main(
                stop_session_id,
                prev_episode_index,
                prev_total_frames,
                timeout_s=2.0)

    def _sync_browse_on_record_stop_main(
        self,
        stop_session_id: int,
        prev_episode_index: int,
        prev_total_frames: int,
        timeout_s: float = 8.0,
    ) -> None:
        """Best-effort sync of main-process browse cache when stop_recording is called."""
        deadline = time.time() + max(0.1, float(timeout_s))

        while time.time() < deadline:

            cur_episode_index = int(self.shared_data.episode_index.value)
            cur_total_frames = int(self.shared_data.total_frames.value)
            cur_total_videos = int(self.shared_data.total_videos.value)

            if cur_episode_index >= prev_episode_index + 1:
                finished_episode_index = cur_episode_index - 1
                chunks_size = int(self.config.lerobot.get('chunks_size', 1000) or 1000)
                finished_episode_chunk = finished_episode_index // max(1, chunks_size)
                episode_length = max(0, cur_total_frames - int(prev_total_frames))

                try:
                    if self.config.get('is_record_episode', False):
                        self.lerobot_recorder._sync_browse_on_record_end(
                            episode_chunk=finished_episode_chunk,
                            episode_index=finished_episode_index,
                            episode_length=episode_length,
                            total_episodes=cur_episode_index,
                            total_frames=cur_total_frames,
                            total_videos=cur_total_videos,
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to sync browse cache on stop in main process: {e}")
                return

            time.sleep(0.05)

        # Timeout fallback: force main-process browse cache to reload from current task files.
        try:
            self.lerobot_recorder._browse_cache_loaded = False
            self.lerobot_recorder._ensure_browse_data_loaded()
        except Exception as e:
            self.logger.warning(f"Failed to refresh browse cache after stop timeout: {e}")

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
            if self.config.get('is_record_episode', False):
                self.lerobot_recorder.begin_recording(episode_chunk = self.shared_data.episode_chunk.value,
                                                    episode_index = self.shared_data.episode_index.value,
                                                    total_frames = self.shared_data.total_frames.value,
                                                    total_videos = self.shared_data.total_videos.value,
                                                    save_raw=self.config.save_raw)
            if self.config.get('is_record_eval_log', False):
                self.eval_recorder.begin_recording(eval_record_id=self.shared_data.eval_record_id.value)
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
            if self.config.get('is_record_eval_log', False):
                currt_record_id, currt_record_duration = self.eval_recorder.end_recording()
                self._sync_shared_data(eval_record_id=currt_record_id + 1, eval_record_duration=currt_record_duration)

            if self.config.get('is_record_episode', False):
                episode_index, total_frames, total_videos = self.lerobot_recorder.end_record()
                self._sync_shared_data(total_frames=total_frames,
                                    total_videos=total_videos,
                                    total_episodes=episode_index,
                                    chunks_size=self.config.lerobot['chunks_size']) # chunks_size doesn't change

        
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
    import sys
    print(f"Current working directory: {os.getcwd()}")
    sys.path.append('/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer')
    from conf.client_conf import get_client_config

    save_dir = "/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer/data/output/test"
    config = get_client_config()

    # Initialize writer
    writer = DataRecordManager(config.record)

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