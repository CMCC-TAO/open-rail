import time
import cv2
import random
import logging
import numpy as np
from pprint import pprint
import threading

from launch import Action
from ..base_robot import RobotBase
from client.utils.util import run_time_decorator, parse_action_layout

import os
import glob
import pandas as pd
import torch

# 限制 OpenCV/FFmpeg 线程，避免多线程解码冲突（pthread_frame async_lock）
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "threads;1")
cv2.setNumThreads(1)

class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the mock robot body using LeRobot dataset for simulation.
        
        Args:
            config (dict): Configuration dictionary containing mock robot settings
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.cfg, self.ori_cfg = config['robots']['mock'], config
        if not hasattr(self.cfg, 'action_layout'):
            self.logger.error("Parameter action_layout is required, please check the configuration.")
        self.action_layout = dict(self.cfg.get('action_layout', {}))
        self.action_dim, _, _ = parse_action_layout(self.action_layout)
        self.current_state = np.zeros(self.action_dim)
        self.dataset = None
        self.episode_files = []
        self.current_episode_idx = 0
        self.currt_index = 0
        self.period = 1.0 / 30.0
        self.video_caps = {}
        self._io_lock = threading.Lock()

        try:
            root = self.cfg['root']
            parquet_glob = os.path.join(root, 'data', 'chunk-*', 'episode_*.parquet')
            parquet_files = sorted(glob.glob(parquet_glob))
            if not parquet_files:
                raise FileNotFoundError(f'未找到离线数据: {parquet_glob}')

            for parquet_path in parquet_files:
                chunk_dir = os.path.basename(os.path.dirname(parquet_path))
                chunk_id = int(chunk_dir.split('-')[-1])
                ep_name = os.path.splitext(os.path.basename(parquet_path))[0]
                episode_id = int(ep_name.split('_')[-1])
                self.episode_files.append((chunk_id, episode_id, parquet_path))

            self._load_episode(0)

            meta_info_path = os.path.join(root, 'meta', 'info.json')
            if os.path.exists(meta_info_path):
                try:
                    import json
                    with open(meta_info_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    fps = info.get('fps', 30)
                    self.period = 1.0 / max(float(fps), 1e-6)
                except Exception:
                    pass

            self.logger.info(f"Loaded local episodes: {len(self.episode_files)}")
            self.logger.info(f"Current episode frames: {len(self.dataset)}")
            self.logger.info(f"Playback fps: {1.0 / self.period:.2f}")
        except Exception as e:
            self.logger.error(f"Failed to load local dataset: {e}")
            print(f"Failed to load local dataset: {e}")
            self.dataset = None

    def _release_video_caps(self):
        for cap in self.video_caps.values():
            try:
                cap.release()
            except Exception:
                pass
        self.video_caps = {}

    def _load_episode(self, episode_list_idx: int):
        self._release_video_caps()
        self.current_episode_idx = episode_list_idx
        chunk_id, episode_id, parquet_path = self.episode_files[self.current_episode_idx]
        self.dataset = pd.read_parquet(parquet_path)
        self.currt_index = 0

        for _, video_key in self.cfg['camera']['names'].items():
            video_path = os.path.join(
                self.cfg['root'],
                'videos',
                f'chunk-{chunk_id:03d}',
                video_key,
                f'episode_{episode_id:06d}.mp4'
            )
            if not os.path.exists(video_path):
                raise FileNotFoundError(f'视频文件不存在: {video_path}')
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f'视频打开失败: {video_path}')
            self.video_caps[video_key] = cap

    def _next_episode(self):
        if not self.episode_files:
            return
        next_idx = (self.current_episode_idx + 1) % len(self.episode_files)
        self._load_episode(next_idx)

    def execute_action(self, action):
        """Execute the given action on the mock robot.
        
        Args:
            action (dict): Dictionary containing action commands for robot joints and gripper
        """
        return

    def reset_robot(self, target_pose=None, mode='zero'):
        """Reset the robot to its default position.
        """
        if target_pose is None:
            if mode == 'zero':
                target_pose = np.zeros(self.action_dim)
        self.current_state = target_pose if target_pose is not None else self.current_state

    def retrieve_observation(self):
        """Retrieve observation data from local lerobot-format files."""
        if self.dataset is None or len(self.dataset) == 0:
            return None

        start_time = time.time()

        with self._io_lock:
            if self.currt_index >= len(self.dataset):
                self.logger.info(f'End of episode {self.current_episode_idx}, frames: {len(self.dataset)}')
                self._next_episode()
                if self.dataset is None or len(self.dataset) == 0:
                    return None

            row = self.dataset.iloc[self.currt_index]
            cam_names = self.cfg['camera']['names']

            result = {
                'ref_timestamp': time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            }

            # 顺序读取3路视频帧；若当前episode读到结尾，切换下一段后重读一次
            for _ in range(2):
                all_ok = True
                for key, video_key in cam_names.items():
                    cap = self.video_caps.get(video_key)
                    if cap is None:
                        raise RuntimeError(f'视频流未初始化: {video_key}')

                    ok, frame_bgr = cap.read()
                    if not ok or frame_bgr is None:
                        all_ok = False
                        break

                    # 避免在 mock 侧使用 cv2.cvtColor，减少与其他模块的 OpenCV/FFmpeg 竞争
                    frame_rgb = frame_bgr[:, :, ::-1].copy()
                    cam_key = f'cam.{key if key != "depth_head" else "depth.head"}'
                    result[cam_key] = frame_rgb

                if all_ok:
                    break

                self.logger.warning('视频读取到末尾，切换下一段 episode 重试')
                self._next_episode()
                if self.dataset is None or len(self.dataset) == 0:
                    return None
                row = self.dataset.iloc[self.currt_index]
                result = {'ref_timestamp': time.clock_gettime_ns(time.CLOCK_MONOTONIC)}
            else:
                return None

            obs_state = np.asarray(row["observation.state"], dtype=np.float32)
            if obs_state.shape[0] != self.action_dim:
                obs_state = obs_state[:self.action_dim] if obs_state.shape[0] > self.action_dim else np.pad(obs_state, (0, self.action_dim - obs_state.shape[0]))
            result['obs.state'] = obs_state
            self.current_state = obs_state

            action = np.asarray(row["action"], dtype=np.float32)
            if action.shape[0] != self.action_dim:
                action = action[:self.action_dim] if action.shape[0] > self.action_dim else np.pad(action, (0, self.action_dim - action.shape[0]))
            result['action'] = action

            self.currt_index += 1

        end_time = time.time()
        if end_time - start_time < self.period:
            time.sleep(self.period - (end_time - start_time))
        return result

    def close(self):
        """Close the mock robot and clean up resources.
        
        This method performs cleanup for the mock robot simulation.
        """
        self._release_video_caps()
        self.logger.info('Close mock robot...')

if __name__ == '__main__':
    # from conf.robots_conf import get_robots_config
    from conf.client_conf import get_client_config
    # config = get_robots_config()
    config = get_client_config()
    robot = RobotBody(config)
    try:
        while True:
            result = robot.retrieve_observation()
            print(f"retrieve_observation: {result.keys()}")
            if result is None:
                break
            for key, value in result.items():
                if 'cam.' not in key:
                    print(f"{key}: {value}")
                    continue
                if 'depth.' in key:
                    img_depth_norm = cv2.normalize(value, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    img_show = cv2.applyColorMap(img_depth_norm, cv2.COLORMAP_JET)
                else:
                    img_show = cv2.cvtColor(value, cv2.COLOR_RGB2BGR)
                cv2.imshow(key, img_show)
                cv2.waitKey(1)
    except KeyboardInterrupt:
        robot.close()