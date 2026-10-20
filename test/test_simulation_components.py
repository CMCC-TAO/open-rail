from unittest.mock import Mock

import numpy as np
import pytest

from client.robots.base_robot import ObservationMode
from client.simulation.robot_runtime import EpisodeState, SimulationRobot, build_observation


def test_observation_owns_state_and_converts_rgb_without_mutating_input():
    state = np.array([1.0, 2.0], dtype=np.float64)
    image = np.array([[[10, 20, 30]]], dtype=np.uint8)
    observation = build_observation(
        state, {'head': image}, mode=ObservationMode.STEP_RESULT,
        observation_step=4, applied_action_step=3, observation_source='step_result',
    )
    np.testing.assert_array_equal(observation['cam.head'], [[[30, 20, 10]]])
    np.testing.assert_array_equal(image, [[[10, 20, 30]]])
    state.fill(0)
    image.fill(0)
    np.testing.assert_array_equal(observation['obs.state'], [1, 2])
    np.testing.assert_array_equal(observation['cam.head'], [[[30, 20, 10]]])
    assert observation['obs.state'].dtype == np.float64
    assert observation['_observation_step'] == 4
    assert observation['_applied_action_step'] == 3
    assert '_sim_time' not in observation


def test_observation_rejects_non_rgb_images():
    with pytest.raises(ValueError, match='HxWx3'):
        build_observation([], {'head': np.zeros((8, 8))}, mode=ObservationMode.STEP_RESULT)


@pytest.mark.parametrize('success,terminated,truncated', [
    (True, False, False), (False, True, False), (False, False, True),
])
def test_episode_preserves_outcome_and_reset_discards_previous_result(
    success, terminated, truncated,
):
    recorder = Mock(path='episode.mp4', error=None)
    episode = EpisodeState(
        index=2, steps=5, success=success, terminated=terminated, truncated=truncated,
    )
    assert episode.done
    episode.finish(recorder, seed=17, instruction='Pick up the cup')
    result = episode.snapshot()
    assert result['success'] == success
    assert result['terminated'] == terminated
    assert result['truncated'] == truncated
    assert result['seed'] == 17
    assert result['video_path'] == 'episode.mp4'
    recorder.stop.assert_called_once_with(wait=False)
    result['steps'] = 100
    assert episode.snapshot()['steps'] == 5
    episode.reset(3)
    assert episode.index == 3
    assert episode.steps == 0
    assert not episode.done
    assert episode.snapshot() is None


@pytest.mark.parametrize('semantics', ['joint_targets', 'estimated_joint_angles'])
def test_new_adapter_reuses_trajectory_contract_with_independent_joint_dimensions(semantics):
    class NewRobot(SimulationRobot):
        joint_action_semantics = semantics

        def joint_state(self):
            return ['a', 'b', 'c'], [.1, .2, .3]

        def joint_action(self, action):
            return np.asarray(action)[:3]

    robot = NewRobot.__new__(NewRobot)
    robot.current_state = np.zeros(12)
    trajectory = robot.get_joint_trajectory([1, 2, 3, 4], [4, 5, 6, 7])
    assert trajectory == {
        'labels': ['a', 'b', 'c'], 'state': [.1, .2, .3],
        'action_fitted': [1., 2., 3.], 'action_raw': [4., 5., 6.],
        'action_semantics': semantics,
    }
    with pytest.raises(ValueError, match='3 finite values'):
        robot.get_joint_trajectory([1, 2])
    with pytest.raises(ValueError, match='3 finite values'):
        robot.get_joint_trajectory([1, np.nan, 3])
    robot.joint_action_semantics = None
    with pytest.raises(ValueError, match='semantics must be declared'):
        robot.get_joint_trajectory([1, 2, 3])
