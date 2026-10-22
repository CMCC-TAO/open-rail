"""Shared simulation adapter contract, trajectories, and episode state."""

import time
from dataclasses import dataclass

import numpy as np

from client.robots.base_robot import RobotBase


class SimulationRobot(RobotBase):
    joint_action_semantics = None

    def describe_io(self):
        from client.simulation.io_adapter import fields_from_layout

        schema = {
            'state': fields_from_layout(getattr(self, 'state_layout', {})),
            'action': fields_from_layout(self.config.action_layout),
        }
        overrides = self.config.get('io_schema', {})
        schema.update(overrides.to_dict() if hasattr(overrides, 'to_dict') else overrides)
        return schema

    def control_robot(self, action):
        raise NotImplementedError('Simulation adapters must return RobotStepResult from control_robot')

    def joint_state(self):
        """Return joint labels and measured positions, independently of policy state."""
        raise NotImplementedError

    def joint_action(self, action):
        """Return joint targets or explicitly identified estimates; None if unavailable."""
        return None

    def get_joint_trajectory(self, action_fitted=None, action_raw=None):
        labels, state = self.joint_state()
        labels = list(labels)
        result = {'labels': labels}
        if not labels:
            return result
        result['state'] = self._joint_values(state, len(labels))
        for source, action in (('action_fitted', action_fitted), ('action_raw', action_raw)):
            if action is not None:
                values = self.joint_action(action)
                if values is not None:
                    if self.joint_action_semantics not in ('joint_targets', 'estimated_joint_angles'):
                        raise ValueError('Joint action semantics must be declared as targets or estimates')
                    result[source] = self._joint_values(values, len(labels))
                    result['action_semantics'] = self.joint_action_semantics
        return result

    def execute_action(self, data):
        return self.control_robot(data)

    def get_episode_result(self):
        with self._lock:
            return self._episode.snapshot()

    def get_episode_steps(self):
        with self._lock:
            return self._episode.steps

    @staticmethod
    def _joint_values(values, size):
        values = np.asarray(values, dtype=np.float64).reshape(-1)
        if values.size != size or not np.isfinite(values).all():
            raise ValueError(f'Joint trajectory must contain {size} finite values')
        return values.tolist()


@dataclass
class DampedJointProjection:
    """Visualization-only differential IK snapshot; no simulator or controller writes."""

    qpos: np.ndarray
    jacobian: np.ndarray
    rotation: np.ndarray
    position_error: np.ndarray
    orientation: np.ndarray
    goal_orientation: np.ndarray
    joint_limits: np.ndarray
    damping: float = 0.05

    def __post_init__(self):
        for name in (
            'qpos', 'jacobian', 'rotation', 'position_error',
            'orientation', 'goal_orientation', 'joint_limits',
        ):
            setattr(self, name, np.array(getattr(self, name), dtype=np.float64, copy=True))
        self.projector = np.linalg.solve(
            self.jacobian @ self.jacobian.T + self.damping ** 2 * np.eye(6), self.jacobian,
        ).T

    def estimate(self, delta, *, desired=False):
        from scipy.spatial.transform import Rotation

        position_error = self.rotation @ delta[:3]
        if desired:
            position_error += self.position_error
        start_orientation = self.goal_orientation if desired else self.orientation
        world_rotation = self.rotation @ Rotation.from_rotvec(delta[3:]).as_matrix() @ self.rotation.T
        orientation_error = Rotation.from_matrix(
            world_rotation @ start_orientation @ self.orientation.T,
        ).as_rotvec()
        estimate = self.qpos + self.projector @ np.concatenate([position_error, orientation_error])
        return np.clip(estimate, self.joint_limits[:, 0], self.joint_limits[:, 1])


@dataclass
class EpisodeState:
    index: int = -1
    steps: int = 0
    success: bool = False
    terminated: bool = False
    truncated: bool = False
    result: dict | None = None

    @property
    def done(self):
        return self.success or self.terminated or self.truncated

    def reset(self, index):
        self.index = int(index)
        self.steps = 0
        self.success = self.terminated = self.truncated = False
        self.result = None

    def finish(self, recorder, **metadata):
        self.result = {
            **metadata,
            'episode': self.index,
            'success': self.success,
            'steps': self.steps,
            'terminated': self.terminated,
            'truncated': self.truncated,
            'video_path': recorder.path,
            'video_error': recorder.error,
        }
        recorder.stop(wait=False)

    def snapshot(self):
        return None if self.result is None else dict(self.result)


def build_observation(
    state, cameras, *, mode, observation_step=None, applied_action_step=None,
    observation_source=None, sim_time=None, joint_trajectory=None,
):
    result = {
        'ref_timestamp': time.clock_gettime_ns(time.CLOCK_MONOTONIC),
        'obs.state': np.asarray(state).copy(),
        '_observation_mode': mode.value,
    }
    for key, value, convert in (
        ('_observation_step', observation_step, int),
        ('_applied_action_step', applied_action_step, int),
        ('_observation_source', observation_source, str),
        ('_sim_time', sim_time, float),
    ):
        if value is not None:
            result[key] = convert(value)
    for name, image in cameras.items():
        image = np.asarray(image)
        if image.ndim != 3 or image.shape[-1] != 3:
            raise ValueError(f'Camera {name} must be HxWx3, got {image.shape}')
        result[f'cam.{name}'] = image[..., ::-1].copy()
    if joint_trajectory is not None:
        result['_joint_trajectory'] = joint_trajectory
    return result
