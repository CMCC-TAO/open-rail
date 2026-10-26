import os
import re
import json
import cv2
import time
import logging
import threading
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from queue import Empty
from pathlib import Path
from datetime import datetime
from collections import deque
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Manager, get_context
from typing import Any, Dict, List, Optional, Union


class _ImageIOVideoWriter:
    def __init__(self, path: str, fps: float) -> None:
        import imageio.v2 as imageio

        self.writer = imageio.get_writer(
            path,
            fps=fps,
            codec='libx264',
            pixelformat='yuv420p',
            macro_block_size=None,
        )
        self.opened = True

    def isOpened(self) -> bool:
        return self.opened

    def write(self, frame: np.ndarray) -> None:
        self.writer.append_data(frame[..., ::-1])

    def release(self) -> None:
        if self.opened:
            self.writer.close()
            self.opened = False


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
        self._parse_config(lerobot_config)

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
        meta_required_file_exists = self._check_meta_path_and_dir(save_path=save_path)
        if meta_required_file_exists:
            self._update_config_from_meta_file()
        else:
            self.config["total_episodes"] = 0
            self.config["total_frames"] = 0
            self.config["total_videos"] = 0
            self.config['chunks_size'] = 1000
        return self.config["total_frames"], self.config["total_videos"], self.config["total_episodes"], self.config['chunks_size']


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
            for camera_name, video_key in self.camera_video_key_dict.items():
                feature = data['features'].get(video_key, data['features'].get(camera_name))
                if feature is None:
                    continue
                info = feature['info']
                self.config[camera_name]['encode']['codec'] = info['video.codec']
                self.config[camera_name]['encode']['has_audio'] = info['has_audio']
                self.config[camera_name]['encode']['is_depth_map'] = info['video.is_depth_map']
                self.config[camera_name]['shape']['height'] = info['video.height']
                self.config[camera_name]['shape']['width'] = info['video.width']
                self.config[camera_name]['shape']['channel'] = info['video.channels']
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
                task_name = data.get('task', data.get('tasks'))
                if task_name not in self.task_language_dict:
                    self.task_language_dict[task_name] = task_index
        self.logger.info(f"Update task languages from meta task file success, task_language_dict={self.task_language_dict}.")

    def _parse_config(self, config: ConfigDict) -> None:
        self.camera_name_list = []
        self.camera_shape_dict = {}
        self.camera_video_key_dict = {}
        image_feature_keys = config.get('image_feature_keys', {})
        for camera_name in config.keys():
            if str(camera_name).startswith("cam."):
                self.camera_name_list.append(camera_name)
                shape_dict = config[camera_name]["shape"]
                self.camera_shape_dict[camera_name] = (shape_dict["height"], shape_dict["width"], shape_dict["channel"])
                short_name = str(camera_name).removeprefix('cam.')
                self.camera_video_key_dict[camera_name] = image_feature_keys.get(
                    short_name, camera_name
                )
                # print(f"Debug: camera_name: {camera_name}, shape: {shape_list}")

        self.action_shape = config['action_shape']
        self.state_shape = config['state_shape']
        self.instruction_key = config.get('instruction_key', 'task_index')
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
        self.video_writers = self._create_video_writer(
            episode_chunk=episode_chunk,
            episode_index=episode_index
        )
        self.parquet_schema, self.parquet_path = self._prepare_parquet_file(
            episode_chunk=episode_chunk,
            episode_index=episode_index
        )
        self.parquet_frame_list = list()
        self.frame_index = 0
        self.episode_task_list = []
        self.step_task_index = 0

    def end_record(self):
        self._release_video_writers()
        self._write_parquet_file()
        self.episode_index = self.episode_index + 1
        self.total_frames = self.total_frames + self.frame_index
        self.total_videos = self.total_videos + len(self.camera_name_list)
        self._write_meta_files(total_frames=self.total_frames,
                            total_episodes=self.episode_index,
                            episode_length=self.frame_index,
                            total_videos=self.total_videos,
                            episode_task_list=self.episode_task_list)
        self.logger.info("Finish recording.")
        return self.episode_index, self.total_frames, self.total_videos
            # self._clear_queues()
            # print(f'self.shared_data.task_language_dict {self.shared_data.task_language_dict}')

    def add_frame_async(self, step_state: dict, step_action: np.ndarray):
        self._write_frame_fun(step_state, step_action)

    def _write_frame_fun(self, step_state: dict, step_action: np.ndarray):
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
            step_language = step_state['language_instruction']

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
                'timestamp': self.frame_index / float(self.config['fps']),
            }
            parquet_frame[self.instruction_key] = step_task_index
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

        Creates video writers for each camera specified in the configuration.

        Returns:
            dict: A dictionary mapping camera names to their respective VideoWriter objects.
        """
        # Video writing setup
        # print(f"DEBUG: Mark 1")
        save_video_path = os.path.join(self.save_path, 'videos', f'chunk-{episode_chunk:03d}')
        filename = f"{'episode'}_{episode_index:06d}.{'mp4'}"
        video_write_dict = {}
        self.video_codec_dict = {}
        # self.camera_shape_dict = {}
        fps = float(self.config.get('fps', 30))

        # print(f"DEBUG: Mark 2")
        for camera_name in self.camera_name_list:
            shape_list = self.camera_shape_dict[camera_name]
            height, width = int(shape_list[0]), int(shape_list[1])
            video_key = self.camera_video_key_dict[camera_name]
            os.makedirs(os.path.join(save_video_path, video_key), exist_ok=True)
            video_path = os.path.join(save_video_path, video_key, filename)
            # self.shared_data.save_video_path_list.append(video_path)

            writer = None
            configured_codec = str(
                self.config[camera_name]['encode'].get('codec', 'h264')
            ).lower()
            if configured_codec in ('h264', 'avc1'):
                try:
                    writer = _ImageIOVideoWriter(video_path, fps)
                    self.video_codec_dict[camera_name] = 'h264'
                except Exception:
                    self.logger.warning(
                        f"Software H.264 writer unavailable for {camera_name}, falling back to OpenCV",
                        exc_info=True,
                    )

            codec_candidates = {
                'mpeg4': ('mp4v', 'XVID', 'MJPG'),
                'mp4v': ('mp4v', 'XVID', 'MJPG'),
                'xvid': ('XVID', 'mp4v', 'MJPG'),
                'mjpeg': ('MJPG', 'mp4v', 'XVID'),
                'mjpg': ('MJPG', 'mp4v', 'XVID'),
            }.get(configured_codec, ('mp4v', 'XVID', 'MJPG'))
            for codec in codec_candidates if writer is None else ():
                # print(f"Debug: Trying to save video with codec: {codec}")
                fourcc = cv2.VideoWriter_fourcc(*codec)
                candidate = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
                if candidate is not None and candidate.isOpened():
                    writer = candidate
                    self.video_codec_dict[camera_name] = {
                        'mp4v': 'mpeg4',
                        'XVID': 'mpeg4',
                        'MJPG': 'mjpeg',
                    }[codec]
                    break
                if candidate is not None:
                    candidate.release()
            if writer is None:
                raise RuntimeError(f"Failed to open VideoWriter for {camera_name}: {video_path}")

            video_write_dict[camera_name] = writer
        self.logger.info(f"create video writer: {save_video_path}")
        return video_write_dict

    def _prepare_parquet_file(self, episode_chunk: int = 0, episode_index: int = 0):
        """
        Initializes the schema for the Parquet file.

        Defines the structure of the Parquet table including observation, action, timestamps, and metadata.
        """
        value_type = {
            'float32': pa.float32(),
            'float64': pa.float64(),
        }[str(self.config.get('state_action_dtype', 'float32'))]
        strict_shapes = bool(self.config.get('strict_shapes', False))
        state_type = (
            pa.list_(value_type, self.state_shape) if strict_shapes else pa.list_(value_type)
        )
        action_type = (
            pa.list_(value_type, self.action_shape) if strict_shapes else pa.list_(value_type)
        )
        fields = [
            ('observation.state', state_type),
            ('action', action_type),
            ('episode_index', pa.int64()),
            ('frame_index', pa.int64()),
            ('index', pa.int64()),
            ('task_index', pa.int64()),
            ('timestamp', pa.float32()),
        ]
        if self.instruction_key != 'task_index':
            fields.append((self.instruction_key, pa.int64()))
        parquet_schema = pa.schema(fields)

        parquet_file_path = os.path.join(
            self.save_path,
            self.config['data_path'].format(episode_chunk=episode_chunk, episode_index=episode_index)
        )
        os.makedirs(os.path.dirname(parquet_file_path), exist_ok=True)
        self.logger.info(f"prepare parquet output: {parquet_file_path}")
        return parquet_schema, parquet_file_path

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

    def _write_parquet_file(self) -> None:
        if not self.parquet_frame_list:
            raise RuntimeError(f'No frames recorded for episode {self.episode_index}')
        table = pa.Table.from_pylist(self.parquet_frame_list, schema=self.parquet_schema)
        temporary_path = f'{self.parquet_path}.tmp'
        pq.write_table(table, temporary_path)
        os.replace(temporary_path, self.parquet_path)
        self.logger.info(
            'Wrote %d records to parquet file: %s',
            len(self.parquet_frame_list),
            self.parquet_path,
        )
        self.parquet_frame_list.clear()


    def _image_feature_metadata(self, camera_name: str) -> dict:
        camera = self.config[camera_name]
        shape = camera['shape']
        encode = camera['encode']
        video_info = {
            'video.codec': getattr(self, 'video_codec_dict', {}).get(
                camera_name, encode['codec']
            ),
            'video.fps': float(self.config['fps']),
            'video.is_depth_map': encode['is_depth_map'],
            'video.pix_fmt': 'yuv420p',
            'has_audio': encode['has_audio'],
        }
        return {
            'dtype': 'video',
            'shape': [shape['height'], shape['width'], shape['channel']],
            'names': ['height', 'width', 'channel'],
            'info': {
                **video_info,
                'video.height': shape['height'],
                'video.width': shape['width'],
                'video.channels': shape['channel'],
                'has_audio': encode['has_audio'],
            },
            'video_info': video_info,
        }

    @staticmethod
    def _array_stats(values: np.ndarray) -> dict:
        values = np.asarray(values, dtype=np.float64)
        if values.ndim == 1:
            values = values[:, None]
        return {
            'mean': values.mean(axis=0).tolist(),
            'std': values.std(axis=0).tolist(),
            'min': values.min(axis=0).tolist(),
            'max': values.max(axis=0).tolist(),
            'q01': np.quantile(values, 0.01, axis=0).tolist(),
            'q99': np.quantile(values, 0.99, axis=0).tolist(),
        }

    def _parquet_stats(self, paths: List[Path]) -> dict:
        columns = ('observation.state', 'action', 'timestamp')
        values = {column: [] for column in columns}
        for path in paths:
            table = pq.read_table(path, columns=list(columns))
            if table.num_rows == 0:
                continue
            for column in columns:
                values[column].extend(table[column].to_pylist())
        return {
            column: self._array_stats(column_values)
            for column, column_values in values.items()
            if column_values
        }

    def _write_stats_files(self, episode_index: int) -> None:
        episode_path = Path(self.save_path) / self.config['data_path'].format(
            episode_chunk=episode_index // int(self.config['chunks_size']),
            episode_index=episode_index,
        )
        episode_stats = self._parquet_stats([episode_path])
        episodes_stats_path = Path(self.meta_dir) / 'episodes_stats.jsonl'
        with episodes_stats_path.open('a', encoding='utf-8') as file:
            file.write(json.dumps({
                'episode_index': episode_index,
                'stats': episode_stats,
            }, ensure_ascii=False) + '\n')

    def _write_meta_files(self, total_episodes: int, total_frames: int,
                          episode_length: int, total_videos: int,
                          episode_task_list: list[str]):
        try:
            self.config['total_episodes'] = total_episodes
            self.config['total_frames'] = total_frames
            self.config['total_videos'] = total_videos
            self.config['splits'] = {'train': f'0:{total_episodes}'}
            state_action_dtype = str(self.config.get('state_action_dtype', 'float32'))
            features = {
                'observation.state': {
                    'dtype': state_action_dtype,
                    'shape': [self.config['state_shape']],
                },
                'action': {
                    'dtype': state_action_dtype,
                    'shape': [self.config['action_shape']],
                },
                'timestamp': {'dtype': 'float32', 'names': None, 'shape': [1]},
                'frame_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                'episode_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                'index': {'dtype': 'int64', 'names': None, 'shape': [1]},
                'task_index': {'dtype': 'int64', 'names': None, 'shape': [1]},
            }
            if self.instruction_key != 'task_index':
                features[self.instruction_key] = {
                    'dtype': 'int64', 'names': None, 'shape': [1]
                }
            for camera_name in self.camera_name_list:
                features[self.camera_video_key_dict[camera_name]] = (
                    self._image_feature_metadata(camera_name)
                )

            chunks_size = int(self.config['chunks_size'])
            info = {
                'codebase_version': self.config['codebase_version'],
                'robot_type': self.config['robot_type'],
                'total_episodes': total_episodes,
                'total_frames': total_frames,
                'total_tasks': len(self.task_language_dict),
                'total_videos': total_videos,
                'total_chunks': (total_episodes + chunks_size - 1) // chunks_size,
                'chunks_size': chunks_size,
                'fps': float(self.config['fps']),
                'splits': {'train': f'0:{total_episodes}'},
                'data_path': self.config['data_path'],
                'video_path': self.config['video_path'],
                'features': features,
            }
            with open(os.path.join(self.meta_dir, 'info.json'), 'w', encoding='utf-8') as file:
                json.dump(info, file, indent=2, ensure_ascii=False)

            episode_index = total_episodes - 1
            with open(os.path.join(self.meta_dir, 'episodes.jsonl'), 'a', encoding='utf-8') as file:
                file.write(json.dumps({
                    'episode_index': episode_index,
                    'tasks': episode_task_list,
                    'length': episode_length,
                }, ensure_ascii=False) + '\n')

            with open(os.path.join(self.meta_dir, 'tasks.jsonl'), 'w', encoding='utf-8') as file:
                for task_language, task_index in self.task_language_dict.items():
                    file.write(json.dumps({
                        'task_index': task_index,
                        'task': task_language,
                    }, ensure_ascii=False) + '\n')
            self._write_stats_files(episode_index)
        except Exception:
            self.logger.exception("Failed to write LeRobot metadata")


def _record_episode_worker(record_config, save_path, save_raw,
                           record_queue, shared_data) -> None:
    logger = logging.getLogger(__name__)
    record_config = ConfigDict(record_config, allow_dotted_keys=True)
    recorder = LeRobotDatasetRecorder(record_config)
    try:
        recorder.set_task(save_path)
        recorder.begin_recording(
            episode_chunk=shared_data.episode_chunk.value,
            episode_index=shared_data.episode_index.value,
            total_frames=shared_data.total_frames.value,
            total_videos=shared_data.total_videos.value,
            save_raw=save_raw,
        )
        while True:
            try:
                step_state, step_action = record_queue.get(timeout=0.1)
            except Empty:
                if not shared_data.running.value:
                    break
                continue
            recorder.add_frame_async(step_state=step_state, step_action=step_action)

        episode_index, total_frames, total_videos = recorder.end_record()
        chunks_size = int(record_config['chunks_size'])
        shared_data.total_frames.value = total_frames
        shared_data.total_videos.value = total_videos
        shared_data.episode_index.value = episode_index
        shared_data.episode_chunk.value = episode_index // chunks_size
    except Exception:
        recorder._release_video_writers()
        logger.exception('Recording worker exited with exception')
        raise


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
        # self.task_language_dict = {}
        # self._parse_config_info(self.config["lerobot"])

        # Shared Queue
        self._process_context = get_context('spawn')
        self.record_queue = self._process_context.Queue()

        # Action recording queues
        self.action_lock = threading.Lock()
        self.action_frame_queue = deque(maxlen=10)

        self.record_obs_executor = ThreadPoolExecutor(max_workers=2)
        self.record_action_executor = ThreadPoolExecutor(max_workers=4)

        # Writer process initialization
        self.writer_process = None
        self._active_episode_index = None
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
        date_str = str(self.config.get('dataset_date') or datetime.now().strftime("%Y%m%d"))
        task_name = self._sanitize_task_name(task)
        self.current_task = task_name
        return os.path.join(self.project_root_path, rel_save_dir, task_name + '_' + date_str)

    def set_task(self, task: str) -> None:
        """Update save path by task/date before a new recording starts."""
        # avoid reload data from file
        if self.current_task == task:
            self.logger.warning(f"{self.current_task} is already set, return.")
            return
        if self.shared_data.running.value:
            self.logger.warning("set_task ignored because recording is running")
            return

        self.current_task = task
        # if self.current_task == task_name and os.path.exists(os.path.join(self.project_root_path, self.save_dir, candidate_dir)):
        #     self.logger.info(f"set_task with the same task name {task_name} and existing directory, reuse it.")
        #     return
        self.save_dir = self.config.get("save_dir", "data/recording")     # relative path
        self.save_path = self._build_full_save_path(self.save_dir, task)  # full path
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
            self.logger.info(f"{self.save_path} not exists, create it")
        total_frames, total_videos, total_episodes, chunks_size = self.lerobot_recorder.set_task(save_path=self.save_path)
        self._sync_shared_data(total_frames=total_frames,
                            total_videos=total_videos,
                            total_episodes=total_episodes,
                            chunks_size=chunks_size)

    def _sync_shared_data(self, total_frames: int = 0, total_videos: int = 0, total_episodes: int = 0, chunks_size: int = 1000) -> None:
        """Sync record lerobot values to shared_data."""
        self.shared_data.total_frames.value = total_frames
        self.shared_data.total_videos.value = total_videos
        self.shared_data.episode_index.value = total_episodes
        self.shared_data.episode_chunk.value = total_episodes // chunks_size
        self.logger.info(f"total_frames={self.shared_data.total_frames.value}, total_videos={self.shared_data.total_videos.value}, total_episodes={self.shared_data.episode_index.value}")

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
        session_id = self._get_recording_session_id()
        self.record_obs_executor.submit(self._add_observation_fun, observation, language_instruction, timestamp, session_id)

    def add_action_async(self, action: np.ndarray, timestamp: int | float) -> None:
        """
        Asynchronously writes action data into the dataset.

        Args:
            action (np.ndarray): A dictionary containing action data from the environment.
        """
        session_id = self._get_recording_session_id()
        self.record_action_executor.submit(self._add_action_fun, action, timestamp, session_id)

    def add_step(self, observation: Dict[str, np.ndarray], action: np.ndarray,
                 language_instruction: str) -> None:
        """Record an already aligned observation-action pair."""
        if not self.shared_data.running.value:
            return
        action = np.asarray(action).reshape(-1)
        if self.config.lerobot.get('strict_shapes', False):
            state = np.asarray(observation['obs.state']).reshape(-1)
            expected_state = int(self.config.lerobot.state_shape)
            expected_action = int(self.config.lerobot.action_shape)
            if state.size != expected_state or action.size != expected_action:
                raise ValueError(
                    'Recording shape mismatch: '
                    f'state={state.size}/{expected_state}, '
                    f'action={action.size}/{expected_action}'
                )
        step_state = dict(observation)
        step_state['language_instruction'] = language_instruction
        self.record_queue.put((step_state, action.copy()))

    def start_recording(self):
        """
        Starts the recording process by launching the writer process.

        This method should be called before adding any observations or actions to ensure that
        the writer process is running and ready to handle incoming data.
        """
        try:
            session_id = self._bump_recording_session_id()
            self.shared_data.running.value = True
            self._clear_queues()
            self._active_episode_index = int(self.shared_data.episode_index.value)
            self.writer_process = self._process_context.Process(
                target=_record_episode_worker,
                args=(
                    self.config.lerobot.to_dict(),
                    self.save_path,
                    bool(self.config.save_raw),
                    self.record_queue,
                    self.shared_data,
                ),
                daemon=True,
            )
            self.writer_process.start()
            self.logger.info(f"Writer process started successfully. session_id={session_id}")
        except Exception as e:
            self.shared_data.running.value = False
            self._active_episode_index = None
            self.logger.exception(f"Failed to start writer_process: {e}")
            raise

    @staticmethod
    def _read_last_jsonl_record(path: Path) -> dict:
        with path.open('rb') as file:
            position = file.seek(0, os.SEEK_END)
            reversed_line = bytearray()
            started = False
            while position > 0:
                position -= 1
                file.seek(position)
                byte = file.read(1)
                if not started and byte in b'\r\n\t ':
                    continue
                started = True
                if byte in b'\r\n':
                    break
                reversed_line.extend(byte)
        if not reversed_line:
            raise RuntimeError(f'No records found in {path}')
        return json.loads(bytes(reversed(reversed_line)).decode('utf-8'))

    @staticmethod
    def _validate_parquet_container(path: Path) -> None:
        if not path.is_file() or path.stat().st_size < 8:
            raise RuntimeError(f'Incomplete parquet file: {path}')
        with path.open('rb') as file:
            header = file.read(4)
            file.seek(-4, os.SEEK_END)
            footer = file.read(4)
        if header != b'PAR1' or footer != b'PAR1':
            raise RuntimeError(f'Invalid parquet container: {path}')

    def _sync_recording_from_disk(self) -> int:
        committed_index = int(self._active_episode_index)
        chunks_size = int(self.config.lerobot['chunks_size'])
        episode_chunk = committed_index // chunks_size
        committed_path = Path(self.save_path) / self.config.lerobot.data_path.format(
            episode_chunk=episode_chunk,
            episode_index=committed_index,
        )
        self._validate_parquet_container(committed_path)

        committed_row = self._read_last_jsonl_record(
            Path(self.save_path) / 'meta/episodes.jsonl'
        )
        committed_frames = int(committed_row.get('length', -1))
        if (
            int(committed_row.get('episode_index', -1)) != committed_index
            or committed_frames <= 0
        ):
            raise RuntimeError(
                f'Recorded episode {committed_index} has no valid commit metadata'
            )

        video_keys = list(self.lerobot_recorder.camera_video_key_dict.values())
        for video_key in video_keys:
            video_path = Path(self.save_path) / self.config.lerobot.video_path.format(
                episode_chunk=episode_chunk,
                episode_index=committed_index,
                video_key=video_key,
            )
            if not video_path.is_file() or video_path.stat().st_size <= 0:
                raise RuntimeError(f'Incomplete recorded video: {video_path}')

        info = json.loads(
            (Path(self.save_path) / 'meta/info.json').read_text(encoding='utf-8')
        )
        total_episodes = int(info.get('total_episodes', -1))
        total_frames = int(info.get('total_frames', -1))
        total_videos = int(info.get('total_videos', -1))
        if (
            total_episodes != committed_index + 1
            or total_frames < committed_frames
            or total_videos != total_episodes * len(video_keys)
        ):
            raise RuntimeError(
                f'Recorded episode {committed_index} has inconsistent dataset metadata'
            )
        self._sync_shared_data(
            total_frames=total_frames,
            total_videos=total_videos,
            total_episodes=total_episodes,
            chunks_size=chunks_size,
        )
        return committed_index

    def stop_recording(self):
        """
        Stops recording and waits for all queued data to be written before exiting.

        Behavior:
        - Set ``running=False`` to stop accepting new records.
        - Let writer process continue draining ``record_queue``.
        - Wait for writer process to exit naturally after flushing video/parquet.
        """
        if self.shared_data.running.value:
            self.shared_data.running.value = False
            self.logger.info("Signaled writer process to stop after draining queue.")

        # Invalidate future async tasks from next cycle; current queue will still be drained.
        self._bump_recording_session_id()

        process = self.writer_process
        if process is not None and process.is_alive():
            self.logger.info("Waiting writer process to flush queued data...")
            process.join()
        elif process is None:
            self.logger.debug("stop_recording called but writer process is not initialized.")

        self.writer_process = None
        self._clear_queues()
        if process is None:
            return None
        exitcode = process.exitcode
        try:
            committed_index = self._sync_recording_from_disk()
        except Exception as error:
            if exitcode != 0:
                raise RuntimeError(
                    f'Recording process exited with code {exitcode} '
                    'and the episode was not completely committed'
                ) from error
            raise
        if exitcode != 0:
            self.logger.warning(
                'Recording process exited with code %s after episode %s was completely '
                'committed; continuing evaluation',
                exitcode,
                committed_index,
            )
        self._active_episode_index = None
        return committed_index
    def _add_observation_fun(self, observation: Dict[str, np.ndarray], language_instruction: str, timestamp: int | float, session_id: int) -> None:
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

        observation['language_instruction'] = language_instruction
        # check state shape

        self.record_queue.put((observation, action))

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

    def close(self):
        """Release all dataset writer resources safely and idempotently."""
        self.logger.info("Closing DataRecordManager...")

        try:
            self.stop_recording()
        except Exception:
            self.logger.debug("stop_recording failed during close", exc_info=True)

        self.logger.info("Closing DataRecordManager, recording stopped.")
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
