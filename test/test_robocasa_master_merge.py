import time
from types import SimpleNamespace

import numpy as np
import pytest

from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.robots.robocasa_pandas.body_robot import RobotBody
from client.simulation.vla_client import VLAClientAsync
from conf.client_conf import get_client_config
from scripts.robocasa_eval import _start_episode, _wait_for_episode


class FakeEnvironment:
    def __init__(self, config):
        self.config = config
        self.actions = []

    def observation(self):
        observation = {key: np.zeros(3) for key in self.config.state_keys}
        observation.update({key: np.zeros((16, 16, 3), dtype=np.uint8)
                            for key in self.config.camera.names.values()})
        observation['annotation.human.task_description'] = 'Open the cabinet'
        return observation

    def reset(self, seed=None):
        self.actions.clear()
        return self.observation(), {}

    def step(self, action):
        time.sleep(0.002)
        self.actions.append(action)
        return self.observation(), 0.0, False, False, {}

    def close(self):
        pass


class FakeTransport:
    is_connected = True
    client_addr = 'fake://model'

    def __init__(self):
        self.observation_steps = []

    def sendMessage(self, data, meta):
        frame = data[0] if isinstance(data, list) else data
        self.frame, self.meta = frame, meta
        self.observation_steps.append(frame['meta']['observation_step'])
        return True

    def recvMessage(self, timeout_ms):
        time.sleep(0.003)
        action = np.linspace(0, 0.2, 8)[:, None] * np.ones((1, 12))
        action[:, 6] = np.where(np.arange(8) % 2, 1, -1)
        action[:, 11] = -1
        return {'meta': self.meta, 'data': {
            'type': 'vla_action', 'pred_action': action,
            'ref_timestamp': self.frame['ref_timestamp'],
            'loc_timestamp': self.frame['loc_timestamp'],
        }}

    def close(self):
        pass


@pytest.mark.parametrize('mode', ['sync', 'async'])
@pytest.mark.parametrize('intra', ['raw', 'interpolation', 'fitting'])
@pytest.mark.parametrize('inter', ['sync', 'search_action', 'smooth_velocity', 'min_jerk'])
def test_threaded_simulation_with_upstream_algorithms(monkeypatch, mode, intra, inter):
    config = get_client_config()
    config.rdm.mode = mode
    config.rdm.skip_initial_frames = 0
    config.rdm.action_consume_mode = 'sequential'
    config.rdm.latency_compensation = False
    config.rdm.action_replenish_threshold = 4
    config.rdm.max_async_observation_lag_steps = 7
    config.intra_chunk.intra_chunk_mode = intra
    config.intra_chunk.output_sample_ratio = 1.0
    config.inter_chunk.inter_chunk_mode = inter
    config.controller.period = 1.0
    config.controller.wait_time = 1
    config.controller.action_steps = 8
    config.controller.gripper_offset = 0
    config.vision.preprocess.method = 'none'
    config.robots.robocasa_pandas.max_episode_steps = 24
    env = FakeEnvironment(config.robots.robocasa_pandas)
    monkeypatch.setattr(RobotBody, '_create_env', lambda self: env)
    monkeypatch.setattr('client.simulation.vla_client.DataRecordManager',
                        lambda **kwargs: SimpleNamespace(close=lambda: None))
    robot = RobotBody(config.robots.robocasa_pandas)
    transport = FakeTransport()
    client = VLAClientAsync(
        config, RealtimeDataManager(config.rdm, simulation_mode=True),
        InterChunkFuser(config.inter_chunk, simulation_mode=True),
        IntraChunkSmoother(config.intra_chunk, simulation_mode=True), TaskLanguageManager(config.language),
        transport, robot,
    )
    try:
        assert client.visualize_server.server is None
        _start_episode(client, robot, False)
        _wait_for_episode(client, 0, 10.0, 5.0, 30.0)
        assert client.pipeline_error is None
        result = robot.get_episode_result()
        assert result['steps'] == 24 and result['truncated']
        assert len(env.actions) == 24
        assert len(transport.observation_steps) > 1
        assert transport.observation_steps == sorted(transport.observation_steps)
        for action in env.actions:
            flat = np.concatenate(list(action.values()))
            assert flat.shape == (12,) and np.isfinite(flat).all()
    finally:
        client.close()


@pytest.mark.parametrize('ratio', [1.0, 2.0])
@pytest.mark.parametrize('mode', ['interpolation', 'fitting'])
def test_smoothing_preserves_sample_count_and_discrete_controls(ratio, mode):
    config = get_client_config()
    config.intra_chunk.intra_chunk_mode = mode
    config.intra_chunk.output_sample_ratio = ratio
    smoother = IntraChunkSmoother(config.intra_chunk, simulation_mode=True)
    smoother.set_action_layout(config.robots.robocasa_pandas.action_layout)
    timestamps = np.linspace(0, 0.35, 8)
    actions = np.tile(np.linspace(0, 0.2, 8), (12, 1))
    actions[6] = np.where(np.arange(8) % 2, 1, -1)
    actions[11] = -1
    fitted, velocity, acceleration, samples, _ = smoother.process(
        timestamps, actions, joint_indices=list(range(12)), step_indices=[6, 11]
    )
    assert fitted.shape == (12, int(8 * ratio))
    assert len(samples) == int(8 * ratio)
    assert set(fitted[6]).issubset({-1, 1})
    np.testing.assert_array_equal(fitted[11], -np.ones(len(samples)))
    assert np.isfinite(velocity).all() and np.isfinite(acceleration).all()


def test_recording_commits_real_parquet_and_videos(monkeypatch, tmp_path):
    import json
    from pathlib import Path
    import pyarrow.parquet as pq
    from scripts.robocasa_eval import _configure_recording_for_robot, _prepare_recording

    config = get_client_config()
    config.rdm.mode = 'sync'
    config.rdm.skip_initial_frames = 0
    config.rdm.action_consume_mode = 'sequential'
    config.rdm.latency_compensation = False
    config.intra_chunk.intra_chunk_mode = 'raw'
    config.inter_chunk.inter_chunk_mode = 'sync'
    config.controller.period = 1.0
    config.controller.action_steps = 8
    config.controller.gripper_offset = 0
    config.vision.preprocess.method = 'none'
    config.record.switch = True
    config.record.save_dir = str(tmp_path)
    config.robots.robocasa_pandas.camera_width = 16
    config.robots.robocasa_pandas.camera_height = 16
    config.robots.robocasa_pandas.max_episode_steps = 8
    env = FakeEnvironment(config.robots.robocasa_pandas)
    monkeypatch.setattr(RobotBody, '_create_env', lambda self: env)
    robot = RobotBody(config.robots.robocasa_pandas)
    _configure_recording_for_robot(config, robot)
    client = VLAClientAsync(
        config, RealtimeDataManager(config.rdm, simulation_mode=True),
        InterChunkFuser(config.inter_chunk, simulation_mode=True),
        IntraChunkSmoother(config.intra_chunk, simulation_mode=True), TaskLanguageManager(config.language),
        FakeTransport(), robot,
    )
    try:
        _prepare_recording(client, config, 'merge_check', '20261008-test')
        _start_episode(client, robot, False, record=True)
        assert _wait_for_episode(client, 0, 10.0, 5.0, 30.0)
        assert client.pipeline_error is None
        client.pause()
        assert client.data_record_manager.stop_recording() == 0
        root = Path(client.data_record_manager.save_path)
        table = pq.read_table(next(root.glob('data/**/*.parquet')))
        assert table.num_rows == 8
        assert 'annotation.human.task_description' in table.column_names
        assert all(len(row) == 12 for row in table['action'].to_pylist())
        videos = list(root.glob('videos/**/*.mp4'))
        assert len(videos) == 3 and all(path.stat().st_size > 0 for path in videos)
        metadata = json.loads((root / 'meta/info.json').read_text())
        assert metadata['total_episodes'] == 1 and metadata['total_frames'] == 8
        assert metadata['robot_type'] == 'PandaOmron'
    finally:
        client.close()
