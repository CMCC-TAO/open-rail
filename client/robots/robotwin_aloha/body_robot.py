import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from client.robots.base_robot import ObservationMode, RobotBase, RobotStepResult
from client.robots.robocasa_pandas.video_recorder import VideoRecorder


class RobotBody(RobotBase):
    DATASET_ROBOT_TYPE = "robotwin_aloha"
    DATASET_CAMERA_KEYS = {
        "head": "observation.images.head",
        "hand_left": "observation.images.hand_left",
        "hand_right": "observation.images.hand_right",
    }
    DATASET_INSTRUCTION_KEY = "annotation.human.task_description"

    def to_dataset_action(self, action):
        return self._normalize_action(action).astype(np.float64)

    def __init__(
        self,
        config,
        task_env,
        instruction,
        episode_index=0,
        seed=None,
        sim_executor=None,
    ):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.cfg = config
        self.observation_mode = ObservationMode.STEP_RESULT
        self._lock = threading.RLock()
        self._owns_sim_executor = sim_executor is None
        self._sim_executor = sim_executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="robotwin_aloha_sim"
        )
        self.task_env = None
        self._last_obs = None
        self._initial_observation_pending = False
        self._episode_index = -1
        self._episode_steps = 0
        self._episode_done = False
        self._episode_result = None
        self._instruction = ""
        self._chunk_rendering = False
        self._chunk_boundary = True
        self.video_recorder = VideoRecorder(config, self.logger)
        self.reset(task_env, instruction, episode_index=episode_index, seed=seed)

    @staticmethod
    def _state(obs):
        try:
            state = obs["joint_action"]["vector"]
        except KeyError as exc:
            raise KeyError("RoboTwin observation is missing joint_action.vector") from exc
        return np.asarray(state, dtype=np.float64).reshape(-1)

    def _to_vla_observation(
        self,
        obs,
        observation_step,
        observation_source,
        applied_action_step=None,
    ):
        result = {
            "ref_timestamp": time.clock_gettime_ns(time.CLOCK_MONOTONIC),
            "obs.state": self.current_state.copy(),
            "_observation_mode": self.observation_mode.value,
            "_observation_step": int(observation_step),
            "_observation_source": observation_source,
        }
        if applied_action_step is not None:
            result["_applied_action_step"] = int(applied_action_step)
        result['_joint_trajectory'] = self.get_joint_trajectory()
        cameras = obs.get("observation", {})
        for target_name, source_name in self.config.camera.names.items():
            try:
                image = cameras[source_name]["rgb"]
            except KeyError as exc:
                raise KeyError(f"RoboTwin observation is missing {source_name}.rgb") from exc
            image = np.asarray(image)
            if image.ndim != 3 or image.shape[-1] != 3:
                raise ValueError(f"RoboTwin camera {source_name} must be HxWx3, got {image.shape}")
            result[f"cam.{target_name}"] = image[..., ::-1].copy()
        return result

    def get_joint_trajectory(self, action_fitted=None, action_raw=None):
        labels = [f'qpos_{i}' for i in range(self.current_state.size)]
        for name, segment in self.config.action_layout.items():
            start, end = int(segment['start']), int(segment['end'])
            for i in range(start, min(end, len(labels))):
                labels[i] = name if end - start == 1 else f'{name}_{i - start}'
        result = {'labels': labels, 'state': self.current_state.tolist()}
        if self.config.get('action_type', 'qpos') == 'qpos':
            for key, action in (('action_fitted', action_fitted), ('action_raw', action_raw)):
                if action is not None:
                    result[key] = self._normalize_action(action).tolist()
        return result

    def _normalize_action(self, action):
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.size != self.action_dim:
            raise ValueError(
                f"robotwin_aloha action must contain {self.action_dim} values, got {action.size}"
            )
        if not np.all(np.isfinite(action)):
            raise ValueError("robotwin_aloha action must contain only finite values")
        return action

    def _video_observation(self, obs):
        cameras = obs.get("observation", {})
        frames = {}
        for source_name in self.config.camera.names.values():
            image = cameras.get(source_name, {}).get("rgb")
            if image is not None:
                frames[source_name] = np.asarray(image, dtype=np.uint8)
        return frames

    def _video_task(self):
        return str(
            self.config.get(
                "task_name",
                type(self.task_env).__name__ if self.task_env is not None else "robotwin",
            )
        )

    def _write_video(self, obs, *, success=False, terminated=False, truncated=False, state=None):
        self.video_recorder.write(
            self._video_observation(obs),
            {
                "task": self._video_task(),
                "episode": self._episode_index + 1,
                "step": self._episode_steps,
                "max_steps": int(self.task_env.step_lim),
                "success": success,
                "terminated": terminated,
                "truncated": truncated,
                "state": state,
            },
        )

    def configure_chunk_rendering(self, enabled):
        self._chunk_rendering = bool(enabled)

    def set_action_chunk_boundary(self, boundary):
        self._chunk_boundary = bool(boundary)

    def _take_action(self, action):
        env = self.task_env
        saved = {}
        if self._chunk_rendering:
            for name, replacement in (
                ("_update_render", lambda: None),
                ("get_obs", lambda: self._last_obs),
                ("render_freq", 0),
            ):
                if hasattr(env, name):
                    saved[name] = getattr(env, name)
                    setattr(env, name, replacement)
        try:
            env.take_action(action, action_type=str(self.config.get("action_type", "qpos")))
            if self._chunk_rendering:
                self.current_state = np.concatenate((
                    env.robot.get_left_arm_jointState(), env.robot.get_right_arm_jointState(),
                )).astype(np.float64, copy=False)
        finally:
            for name, value in saved.items():
                setattr(env, name, value)

    def control_robot(self, action):
        with self._lock:
            if self.task_env is None:
                raise RuntimeError("RoboTwin task environment is not initialized")
            if self._episode_done:
                return RobotStepResult(
                    success=bool(self._episode_result and self._episode_result["success"]),
                    terminated=True,
                    observation_step=self._episode_steps,
                    applied_action_step=max(0, self._episode_steps - 1),
                    observation_source=ObservationMode.STEP_RESULT.value,
                    info=dict(self._episode_result or {}),
                )

            action = self._normalize_action(action)
            applied_action_step = self._episode_steps
            self._sim_executor.submit(self._take_action, action).result()
            self._episode_steps = int(self.task_env.take_action_cnt)
            success = bool(self.task_env.eval_success)
            truncated = self._episode_steps >= int(self.task_env.step_lim)
            self._episode_done = success or truncated
            obs = None
            if not self._chunk_rendering or self._chunk_boundary or self._episode_done:
                obs = self._sim_executor.submit(self.task_env.get_obs).result()
                self._last_obs = obs
                self.current_state = self._state(obs)
                self._write_video(
                    obs,
                    success=success,
                    terminated=success,
                    truncated=truncated and not success,
                )
            if self._episode_done:
                self._episode_result = {
                    "episode": self._episode_index,
                    "seed": self._seed,
                    "success": success,
                    "steps": self._episode_steps,
                    "terminated": success,
                    "truncated": truncated and not success,
                    "instruction": self._instruction,
                    "video_path": self.video_recorder.path,
                    "video_error": self.video_recorder.error,
                }
                self.logger.info(
                    "RoboTwin episode %d finished: success=%s, steps=%d",
                    self._episode_index,
                    success,
                    self._episode_steps,
                )
                self.video_recorder.stop(wait=False)
            return RobotStepResult(
                observation=self._to_vla_observation(
                    obs,
                    observation_step=self._episode_steps,
                    applied_action_step=applied_action_step,
                    observation_source=ObservationMode.STEP_RESULT.value,
                ) if obs is not None else None,
                success=success,
                terminated=success,
                truncated=truncated and not success,
                observation_step=self._episode_steps,
                applied_action_step=applied_action_step,
                observation_source=ObservationMode.STEP_RESULT.value,
                info={"instruction": self._instruction},
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
                observation_source="reset",
            )

    def reset(self, task_env, instruction, episode_index, seed=None):
        with self._lock:
            self.video_recorder.stop()
            if task_env is None:
                raise ValueError("task_env is required")
            self.task_env = task_env
            self._instruction = str(instruction).strip()
            if not self._instruction:
                raise ValueError("RoboTwin instruction must not be empty")
            self._episode_index = int(episode_index)
            self._seed = None if seed is None else int(seed)
            self._episode_steps = int(task_env.take_action_cnt)
            if self._episode_steps != 0:
                raise ValueError("RoboTwin episode must start before the first action")
            if task_env.step_lim is None:
                raise ValueError("RoboTwin task step_lim is not initialized")
            obs = self._sim_executor.submit(task_env.get_obs).result()
            state = self._state(obs)
            if state.size != self.action_dim:
                raise ValueError(
                    f"RoboTwin state/action dimensions differ: {state.size} != "
                    f"{self.action_dim}; check the embodiment and action layout"
                )
            self.current_state = state
            self._last_obs = obs
            self._initial_observation_pending = True
            self._episode_done = False
            self._episode_result = None
            self.video_recorder.start(self._video_task(), self._episode_index)
            self._write_video(obs, state="RESET")
            return self._to_vla_observation(obs, 0, "reset")

    def get_task_description(self):
        return self._instruction

    def get_episode_result(self):
        with self._lock:
            return None if self._episode_result is None else dict(self._episode_result)

    def get_episode_steps(self):
        with self._lock:
            return self._episode_steps

    def stop_video(self):
        with self._lock:
            self.video_recorder.stop()
            return {
                "video_path": self.video_recorder.path,
                "video_error": self.video_recorder.error,
            }

    def detach_env(self):
        with self._lock:
            self.video_recorder.stop()
            env, self.task_env = self.task_env, None
        if env is not None:
            self._sim_executor.submit(env.close_env).result()

    def close(self):
        self.video_recorder.close()
        self.detach_env()
        if self._owns_sim_executor:
            self._sim_executor.shutdown(wait=True)
