import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from client.robots.base_robot import ObservationMode, RobotBase, RobotStepResult
from client.robots.robocasa.video_recorder import VideoRecorder


class RobotBody(RobotBase):
    ACTION_KEYS = (
        'end_effector_position',
        'end_effector_rotation',
        'gripper_close',
        'base_motion',
        'control_mode',
    )

    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.cfg = config
        self._lock = threading.RLock()
        self._sim_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='robocasa_sim')
        try:
            self.env = self._sim_executor.submit(self._create_env).result()
        except Exception:
            self._sim_executor.shutdown(wait=True)
            raise
        self._last_obs = None
        self._initial_observation_pending = False
        self._episode_index = -1
        self._episode_steps = 0
        self._episode_success = False
        self._episode_done = False
        self._episode_result = None
        self._last_action = np.zeros(self.action_dim, dtype=np.float32)
        self.observation_mode = ObservationMode.STEP_RESULT
        self.video_recorder = VideoRecorder(config, self.logger)
        self.reset()

    def _create_env(self):
        try:
            import gymnasium as gym
            import robocasa  # noqa: F401
        except ImportError as exc:
            raise RuntimeError('RoboCasa backend requires gymnasium and robocasa') from exc

        env_name = str(self.config.get('env_name', '')).strip()
        if not env_name:
            raise ValueError('robocasa.env_name is required')
        env_id = env_name if env_name.startswith('robocasa/') else f'robocasa/{env_name}'
        try:
            return gym.make(
                env_id,
                split=self.config.get('split', 'target'),
                camera_widths=int(self.config.get('camera_width', 256)),
                camera_heights=int(self.config.get('camera_height', 256)),
                enable_render=bool(self.config.get('enable_render', True)),
            )
        except ImportError as exc:
            if 'EGL device display' in str(exc):
                raise RuntimeError(
                    'MuJoCo EGL initialization failed; use a GPU node with EGL support '
                    'or pass --mujoco_gl osmesa when OSMesa is installed'
                ) from exc
            raise

    def _update_state(self, obs):
        values = []
        for key in self.config.get('state_keys', []):
            if key not in obs:
                raise KeyError(f'RoboCasa observation is missing {key!r}')
            values.append(np.asarray(obs[key], dtype=np.float32).reshape(-1))
        if not values:
            raise ValueError('robocasa.state_keys must not be empty')
        self.current_state = np.concatenate(values)

    def _sim_time(self):
        for source in (self.env, getattr(self.env, 'unwrapped', None)):
            sim = getattr(source, 'sim', None)
            data = getattr(sim, 'data', None)
            if data is not None and hasattr(data, 'time'):
                return float(data.time)
        return None

    def _to_vla_observation(
        self,
        obs,
        observation_step=None,
        applied_action_step=None,
        observation_source=None,
        sim_time=None,
    ):
        result = {
            'ref_timestamp': time.clock_gettime_ns(time.CLOCK_MONOTONIC),
            '_observation_mode': self.observation_mode.value,
        }
        if observation_step is not None:
            result['_observation_step'] = int(observation_step)
        if applied_action_step is not None:
            result['_applied_action_step'] = int(applied_action_step)
        if observation_source is not None:
            result['_observation_source'] = observation_source
        if sim_time is not None:
            result['_sim_time'] = float(sim_time)
        for camera_name, obs_key in self.config.camera.names.items():
            if obs_key not in obs:
                raise KeyError(f'RoboCasa observation is missing camera {obs_key!r}')
            result[f'cam.{camera_name}'] = np.asarray(obs[obs_key])[..., ::-1].copy()
        result['obs.state'] = self.current_state.copy()
        return result

    def _flat_to_action_dict(self, action):
        action = np.asarray(action, dtype=np.float32).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(f'RoboCasa action must contain {self.action_dim} values, got {action.size}')
        if not np.all(np.isfinite(action)):
            raise ValueError('RoboCasa action must contain only finite values')
        result = {}
        for key in self.ACTION_KEYS:
            layout = self.action_layout[key]
            value = action[layout['start']:layout['end']]
            result[f'action.{key}'] = np.clip(value, -1.0, 1.0)
        return result

    def _to_flat_action(self, action):
        if not isinstance(action, dict):
            return np.asarray(action, dtype=np.float32).reshape(-1)
        result = self._last_action.copy()
        for key in self.ACTION_KEYS:
            value = action.get(key, action.get(f'action.{key}'))
            if value is None:
                continue
            layout = self.action_layout[key]
            value = np.asarray(value, dtype=np.float32).reshape(-1)
            expected = layout['end'] - layout['start']
            if value.size != expected:
                raise ValueError(f'{key} must contain {expected} values')
            result[layout['start']:layout['end']] = value
        return result

    def control_robot(self, action):
        with self._lock:
            if self._episode_done:
                return RobotStepResult(
                    success=self._episode_success,
                    terminated=True,
                    observation_step=self._episode_steps,
                    applied_action_step=max(0, self._episode_steps - 1),
                    sim_time=self._sim_time(),
                    observation_source=ObservationMode.STEP_RESULT.value,
                    info=dict(self._episode_result or {}),
                )
            flat_action = self._to_flat_action(action)
            action_dict = self._flat_to_action_dict(flat_action)
            applied_action_step = self._episode_steps
            obs, reward, terminated, truncated, info = self._sim_executor.submit(
                self.env.step, action_dict
            ).result()
            self._last_obs = obs
            self._update_state(obs)
            self._episode_steps += 1
            observation_step = self._episode_steps
            sim_time = self._sim_time()
            self._last_action = flat_action.copy()
            success = bool(info.get('success', False) or reward > 0)
            self._episode_success |= success
            max_steps = int(self.config.get('max_episode_steps', 1000))
            truncated = bool(truncated or self._episode_steps >= max_steps)
            self._episode_done = bool(self._episode_success or terminated or truncated)
            self.video_recorder.write(obs, {
                'task': self.config.env_name,
                'episode': self._episode_index + 1,
                'step': self._episode_steps,
                'max_steps': max_steps,
                'reward': reward,
                'success': self._episode_success,
                'terminated': bool(terminated),
                'truncated': truncated,
                'sim_time': sim_time,
            })
            if self._episode_done:
                self._episode_result = {
                    'episode': self._episode_index,
                    'success': self._episode_success,
                    'steps': self._episode_steps,
                    'terminated': bool(terminated),
                    'truncated': truncated,
                    'video_path': self.video_recorder.path,
                    'video_error': self.video_recorder.error,
                }
                self.logger.info(
                    'RoboCasa episode %d finished: success=%s, steps=%d',
                    self._episode_index,
                    self._episode_success,
                    self._episode_steps,
                )
                self.video_recorder.stop(wait=False)
            return RobotStepResult(
                observation=self._to_vla_observation(
                    obs,
                    observation_step=observation_step,
                    applied_action_step=applied_action_step,
                    observation_source=ObservationMode.STEP_RESULT.value,
                    sim_time=sim_time,
                ),
                success=self._episode_success,
                terminated=bool(terminated),
                truncated=truncated,
                observation_step=observation_step,
                applied_action_step=applied_action_step,
                sim_time=sim_time,
                observation_source=ObservationMode.STEP_RESULT.value,
                info=dict(info),
            )

    def execute_action(self, data):
        return self.control_robot(data)

    def retrieve_observation(self):
        with self._lock:
            if not self._initial_observation_pending or self._last_obs is None:
                return None
            self._initial_observation_pending = False
            return self._to_vla_observation(
                self._last_obs,
                observation_step=0,
                observation_source='reset',
                sim_time=self._sim_time(),
            )

    def reset(self, seed=None):
        with self._lock:
            self.video_recorder.stop()
            if seed is None:
                base_seed = self.config.get('seed')
                seed = None if base_seed is None else int(base_seed) + self._episode_index + 1
            obs, _ = self._sim_executor.submit(self.env.reset, seed=seed).result()
            self._episode_index += 1
            self._episode_steps = 0
            self._episode_success = False
            self._episode_done = False
            self._episode_result = None
            self._last_action.fill(0.0)
            self._last_obs = obs
            self._initial_observation_pending = True
            self._update_state(obs)
            self.video_recorder.start(self.config.env_name, self._episode_index)
            self.video_recorder.write(obs, {
                'task': self.config.env_name,
                'episode': self._episode_index + 1,
                'step': 0,
                'max_steps': int(self.config.get('max_episode_steps', 1000)),
                'reward': 0.0,
                'success': False,
                'state': 'RESET',
                'sim_time': self._sim_time(),
            })
            self.logger.info('RoboCasa episode %d reset complete', self._episode_index)
            return self._to_vla_observation(
                obs,
                observation_step=0,
                observation_source='reset',
                sim_time=self._sim_time(),
            )

    def reset_robot(self, target_pose=None, mode='default'):
        del target_pose, mode
        return self.reset()

    def get_task_description(self):
        with self._lock:
            if self._last_obs is None:
                return ''
            return str(self._last_obs.get('annotation.human.task_description', ''))

    def get_episode_result(self):
        with self._lock:
            return None if self._episode_result is None else dict(self._episode_result)

    def close(self):
        with self._lock:
            self.video_recorder.close()
            env, self.env = self.env, None
        if env is not None:
            self._sim_executor.submit(env.close).result()
        self._sim_executor.shutdown(wait=True)
