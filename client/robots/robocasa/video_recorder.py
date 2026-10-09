import os
import threading
import time

import cv2
import numpy as np


class VideoRecorder:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.writer = None
        self.path = None
        self.error = None
        self._finalize_threads = []
        self.last_write_timings = {}

    def start(self, env_name, episode):
        self.stop()
        self.path = None
        self.error = None
        video_dir = str(self.config.get('video_dir', '') or '').strip()
        if not video_dir:
            return
        try:
            import imageio.v2 as imageio

            os.makedirs(video_dir, exist_ok=True)
            task = str(env_name).split('/')[-1]
            self.path = os.path.join(video_dir, f'{task}_episode_{episode:04d}.mp4')
            self.writer = imageio.get_writer(
                self.path,
                fps=int(self.config.get('video_fps', 20)),
                codec='libx264',
            )
        except Exception as exc:
            self.error = str(exc)
            self.writer = None
            self.logger.exception('Failed to start RoboCasa video recording')

    @staticmethod
    def _fit_text(text, width, font, scale, thickness):
        text = str(text)
        if cv2.getTextSize(text, font, scale, thickness)[0][0] <= width:
            return text
        suffix = '...'
        while text and cv2.getTextSize(text + suffix, font, scale, thickness)[0][0] > width:
            text = text[:-1]
        return text + suffix

    def _info_panel(self, reference, metadata):
        panel = np.zeros_like(reference)
        metadata = metadata or {}
        height, width = panel.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.36, min(0.55, width / 520.0))
        thickness = 1
        margin = max(10, width // 20)
        line_height = max(20, height // 11)
        max_text_width = width - 2 * margin
        success = bool(metadata.get('success', False))
        terminated = bool(metadata.get('terminated', False))
        truncated = bool(metadata.get('truncated', False))
        if success:
            state = 'SUCCESS'
            state_color = (80, 210, 120)
        elif terminated:
            state = 'TERMINATED'
            state_color = (235, 100, 100)
        elif truncated:
            state = 'TRUNCATED'
            state_color = (235, 180, 80)
        else:
            state = str(metadata.get('state', 'RUNNING')).upper()
            state_color = (120, 185, 240)

        task = str(metadata.get('task', self.config.get('env_name', ''))).split('/')[-1]
        episode = metadata.get('episode', '-')
        step = metadata.get('step', '-')
        max_steps = metadata.get('max_steps', '-')
        reward = metadata.get('reward')
        sim_time = metadata.get('sim_time')
        lines = [
            (self.config.get('video_title', 'ROBOCASA EVALUATION'), (235, 235, 235)),
            (f'Task: {task}', (190, 195, 205)),
            (f'Episode: {episode}', (190, 195, 205)),
            (f'Step: {step} / {max_steps}', (190, 195, 205)),
            (f'Reward: {float(reward):.3f}' if reward is not None else 'Reward: -', (190, 195, 205)),
            (f'Success: {"YES" if success else "NO"}', (190, 195, 205)),
            (f'State: {state}', state_color),
            (f'Sim time: {float(sim_time):.3f} s' if sim_time is not None else 'Sim time: -', (190, 195, 205)),
        ]
        y = margin + line_height
        for text, color in lines:
            fitted = self._fit_text(text, max_text_width, font, scale, thickness)
            cv2.putText(panel, fitted, (margin, y), font, scale, color, thickness, cv2.LINE_AA)
            y += line_height
            if y >= height - margin:
                break
        return panel

    def write(self, obs, metadata=None):
        self.last_write_timings = {'video_prepare_s': 0.0, 'video_encode_submit_s': 0.0}
        if self.writer is None:
            return
        started = time.perf_counter()
        try:
            images = []
            height = int(self.config.get('camera_height', 256))
            width = int(self.config.get('camera_width', 256))
            for obs_key in self.config.camera.names.values():
                if obs_key not in obs:
                    continue
                image = np.asarray(obs[obs_key], dtype=np.uint8)
                if image.shape[:2] != (height, width):
                    image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
                images.append(image)
            if not images:
                return
            if self.config.get('video_layout', 'grid') == 'single':
                frame = images[0]
            else:
                images = images[:3]
                while len(images) < 3:
                    images.append(np.zeros_like(images[0]))
                images.append(self._info_panel(images[0], metadata))
                frame = np.concatenate(
                    [np.concatenate(images[:2], axis=1), np.concatenate(images[2:4], axis=1)],
                    axis=0,
                )
            self.last_write_timings['video_prepare_s'] = time.perf_counter() - started
            encode_started = time.perf_counter()
            try:
                self.writer.append_data(frame)
            finally:
                self.last_write_timings['video_encode_submit_s'] = time.perf_counter() - encode_started
        except Exception as exc:
            self.error = str(exc)
            self.logger.exception('Failed to write RoboCasa video frame')
            self.stop()

    def _close_writer(self, writer):
        try:
            writer.close()
        except Exception as exc:
            self.error = self.error or str(exc)
            self.logger.exception('Failed to finalize RoboCasa video')

    def stop(self, wait=True):
        writer, self.writer = self.writer, None
        if writer is None:
            return
        if wait:
            self._close_writer(writer)
            return
        thread = threading.Thread(
            target=self._close_writer,
            args=(writer,),
            daemon=True,
            name='robocasa_video_finalize',
        )
        self._finalize_threads.append(thread)
        thread.start()

    def close(self, timeout=2.0):
        self.stop(wait=False)
        for thread in self._finalize_threads:
            thread.join(timeout=timeout)
        self._finalize_threads = [thread for thread in self._finalize_threads if thread.is_alive()]
