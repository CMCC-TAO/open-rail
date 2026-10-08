import threading
import time
import unittest
import logging

import numpy as np
from ml_collections import ConfigDict

from client.core.realtime_data_manager import RealtimeDataManager
from client.simulation.vla_client import VLAClientAsync
from client.robots.base_robot import ObservationMode, RobotStepResult
from client.robots.robocasa.body_robot import RobotBody
from client.robots.robocasa.video_recorder import VideoRecorder
from conf.robots_conf import get_robocasa_config


def make_config():
    config = ConfigDict()
    config.max_len = 10
    config.observe_fps_window_size = 2
    config.skip_initial_frames = 0
    config.action_consume_mode = 'sequential'
    config.latency_compensation = False
    return config


class RealtimeDataManagerSequentialTest(unittest.TestCase):
    def setUp(self):
        self.manager = RealtimeDataManager(make_config())
        raw = [np.array([1.0, 10.0]), np.array([2.0, 20.0]), np.array([3.0, 30.0])]
        self.manager.update_action_chunk_raw(raw, [0.0, 0.1, 0.2])
        actions = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
        zeros = np.zeros_like(actions)
        self.manager.update_action_chunk_fitted(
            action_chunk_smoothed=actions,
            vel_chunk_smoothed=zeros,
            acc_chunk_smoothed=zeros,
            timestamps_smoothed=np.array([0.0, 0.1, 0.2]),
            target_chunk_index=0,
        )

    def test_consumes_every_action_once(self):
        selected = []
        for _ in range(3):
            action, _, _, _ = self.manager.get_action_fitted()
            selected.append(action.copy())
            self.manager.mark_action_executed()

        np.testing.assert_array_equal(
            np.stack(selected),
            np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]),
        )
        self.assertEqual(self.manager.get_action_fitted(), (None, None, None, None))

    def test_sync_waits_for_execution_ack(self):
        completed = []
        waiter = threading.Thread(target=lambda: completed.append(self.manager.wait_for_next('sync')))
        waiter.start()

        for _ in range(2):
            self.manager.get_action_fitted()
            self.manager.mark_action_executed()
        time.sleep(0.02)
        self.assertTrue(waiter.is_alive())

        self.manager.get_action_fitted()
        self.manager.mark_action_executed()
        waiter.join(timeout=1.0)
        self.assertEqual(completed, [True])

    def test_cancel_releases_sync_wait(self):
        completed = []
        waiter = threading.Thread(target=lambda: completed.append(self.manager.wait_for_next('sync')))
        waiter.start()
        self.manager.cancel_waiters()
        waiter.join(timeout=1.0)
        self.assertEqual(completed, [False])

    def test_latency_compensation_can_be_disabled(self):
        self.assertEqual(self.manager.get_start_chunk_index(np.array([0.0, 0.1])), 0)

    def test_first_observation_is_available(self):
        self.manager.add_observe_data({'frame': 0})
        self.assertEqual(self.manager.pop_observe_data(), {'frame': 0})

    def test_failed_inference_observation_can_be_restored(self):
        self.manager.add_observe_data({'frame': 0})
        data = self.manager.pop_observe_data()
        self.manager.restore_observe_data(data)
        self.assertEqual(self.manager.pop_observe_data(), {'frame': 0})

    def test_async_inference_drops_stale_observations(self):
        for frame in range(3):
            self.manager.add_observe_data({'frame': frame})

        data = self.manager.pop_observe_data(latest_only=True)

        self.assertEqual(data, {'frame': 2})
        self.assertIsNone(self.manager.pop_observe_data())

    def test_latest_observation_can_be_restored_after_failure(self):
        for frame in range(3):
            self.manager.add_observe_data({'frame': frame})

        data = self.manager.pop_observe_data(latest_only=True)
        self.manager.restore_observe_data(data)

        self.assertEqual(self.manager.pop_observe_data(), {'frame': 2})

    def test_failed_async_inference_does_not_replace_newer_observation(self):
        self.manager.add_observe_data({'frame': 0})
        data = self.manager.pop_observe_data(latest_only=True)
        self.manager.add_observe_data({'frame': 1})

        self.manager.restore_observe_data(data, only_if_empty=True)

        self.assertEqual(self.manager.pop_observe_data(), {'frame': 1})

    def test_action_replenishment_uses_remaining_actions(self):
        self.assertFalse(self.manager.needs_action_replenishment(min_remaining=0))
        self.manager.action_executed_index = 1
        self.assertTrue(self.manager.needs_action_replenishment(min_remaining=1))
        self.manager.action_executed_index = 2
        self.assertTrue(self.manager.needs_action_replenishment(min_remaining=0))


class _FakeManager:
    def __init__(self, events):
        self.events = events

    def get_action_fitted(self):
        return np.zeros(12), np.zeros(12), np.zeros(12), np.zeros(12)

    def mark_action_executed(self):
        self.events.append('ack')

    def cancel_waiters(self):
        self.events.append('cancel')

    def get_prob_progress(self):
        return None


class _FakeVisualizeServer:
    def update_chart_data(self, **kwargs):
        return None


class VLAClientSimulationControlTest(unittest.TestCase):
    def make_client(self, result, events):
        client = VLAClientAsync.__new__(VLAClientAsync)
        client.is_control_thread_running = True
        client.is_inference_thread_running = True
        client.realtime_data_manager = _FakeManager(events)
        client.robot = type(
            'Robot',
            (),
            {
                'current_state': np.zeros(16),
                'control_robot': lambda self, action: events.append('step') or result,
            },
        )()
        client._ingest_observation = lambda obs, **kwargs: events.append('observe')
        client._track_step_result = lambda step_result: None
        client._stop_control_thread_on_error = lambda error: None
        client.episode_done_event = threading.Event()
        client.last_step_result = None
        client.pipeline_error = None
        client._step_meta_lock = threading.Lock()
        client._control_in_flight = False
        client.config = ConfigDict({
            'record': {'switch': False},
            'language': {'auto_mode': False},
            'controller': {'period': 1.0},
        })
        client.show_thread_lock = threading.Lock()
        client.current_prob_progress = 0.0
        client.observe_period = 1.0
        client.visualize_server = _FakeVisualizeServer()
        return client

    def test_observation_precedes_execution_ack(self):
        events = []
        result = RobotStepResult(observation={'frame': 1})
        self.make_client(result, events)._control_thread_fun()
        self.assertEqual(events, ['step', 'observe', 'ack'])

    def test_terminal_step_cancels_without_ack(self):
        events = []
        result = RobotStepResult(observation={'frame': 1}, success=True)
        client = self.make_client(result, events)
        client._control_thread_fun()
        self.assertEqual(events, ['step', 'observe', 'cancel'])
        self.assertTrue(client.episode_done_event.is_set())
        self.assertFalse(client.is_control_thread_running)
        self.assertFalse(client.is_inference_thread_running)

    def test_control_error_wakes_episode_waiter(self):
        events = []
        client = self.make_client(RobotStepResult(), events)
        client.control_thread_timer = type('Timer', (), {'is_alive': lambda self: False})()
        error = RuntimeError('sim step failed')
        VLAClientAsync._stop_control_thread_on_error(client, error)
        self.assertIs(client.pipeline_error, error)
        self.assertTrue(client.episode_done_event.is_set())


class RoboCasaActionMappingTest(unittest.TestCase):
    def test_flat_action_mapping(self):
        robot = RobotBody.__new__(RobotBody)
        robot.action_dim = 12
        robot.action_layout = dict(get_robocasa_config().action_layout)
        action = np.arange(12, dtype=np.float32) / 10.0
        mapped = robot._flat_to_action_dict(action)

        np.testing.assert_array_equal(mapped['action.end_effector_position'], action[0:3])
        np.testing.assert_array_equal(mapped['action.end_effector_rotation'], action[3:6])
        np.testing.assert_array_equal(mapped['action.gripper_close'], action[6:7])
        np.testing.assert_array_equal(mapped['action.base_motion'], action[7:11])
        np.testing.assert_array_equal(mapped['action.control_mode'], np.array([1.0]))

    def test_vla_observation_carries_step_metadata(self):
        robot = RobotBody.__new__(RobotBody)
        robot.config = ConfigDict({
            'camera': {
                'names': {
                    'head': 'head_image',
                },
            },
        })
        robot.current_state = np.array([1.0, 2.0], dtype=np.float32)
        robot.observation_mode = ObservationMode.STEP_RESULT
        obs = {
            'head_image': np.zeros((2, 2, 3), dtype=np.uint8),
        }

        result = robot._to_vla_observation(
            obs,
            observation_step=3,
            applied_action_step=2,
            observation_source=ObservationMode.STEP_RESULT.value,
            sim_time=0.12,
        )

        self.assertEqual(result['_observation_step'], 3)
        self.assertEqual(result['_applied_action_step'], 2)
        self.assertEqual(result['_observation_mode'], ObservationMode.STEP_RESULT.value)
        self.assertEqual(result['_observation_source'], ObservationMode.STEP_RESULT.value)
        self.assertEqual(result['_sim_time'], 0.12)


class VLAClientAsyncStepMetadataTest(unittest.TestCase):
    def make_client(self, max_lag=4):
        client = VLAClientAsync.__new__(VLAClientAsync)
        client.config = ConfigDict({
            'rdm': {
                'mode': 'async',
                'max_async_observation_lag_steps': max_lag,
            },
        })
        client.logger = logging.getLogger(__name__)
        client._step_meta_lock = threading.Lock()
        client._latest_observation_step = 3
        client._latest_applied_action_step = 2
        client._last_accepted_observation_step = None
        client._control_in_flight = False
        client._inference_in_flight = False
        client._episode_generation = 1
        client.is_inference_thread_running = True
        return client

    def test_previous_episode_inference_result_is_rejected(self):
        client = self.make_client()
        generation = client._begin_inference_request()
        client._episode_generation += 1
        client._finish_inference_request()
        self.assertFalse(client._inference_request_is_current(generation))

    def test_async_inference_trims_expired_action_prefix(self):
        client = self.make_client(max_lag=4)
        action_data = {
            'type': 'vla_action',
            'pred_action': np.arange(5),
            'ref_timestamp': 0,
            'loc_timestamp': 0.0,
        }

        result = client._prepare_action_data_for_current_step(action_data, request_observation_step=1)

        np.testing.assert_array_equal(result['pred_action'], np.array([2, 3, 4]))
        self.assertEqual(result['_async_alignment_step'], 3)

    def test_async_lag_includes_action_currently_executing(self):
        client = self.make_client(max_lag=4)
        client._control_in_flight = True
        action_data = {
            'type': 'vla_action',
            'pred_action': np.arange(6),
            'ref_timestamp': 0,
            'loc_timestamp': 0.0,
        }

        result = client._prepare_action_data_for_current_step(
            action_data, request_observation_step=1
        )

        np.testing.assert_array_equal(result['pred_action'], np.array([3, 4, 5]))
        self.assertEqual(result['_async_alignment_step'], 4)

    def test_async_commit_trims_steps_advanced_during_processing(self):
        client = self.make_client(max_lag=4)
        client._latest_observation_step = 4
        client.is_control_thread_running = True
        client.config.controller = ConfigDict({'gripper_offset': 0})
        committed = {}

        class Manager:
            def set_inter_traj_time_marker(self):
                pass

            def get_start_chunk_index(self, timestamps):
                return 0

            def get_current_state(self):
                zeros = np.zeros(2)
                return zeros, zeros, zeros

            def set_control_time_marker(self):
                pass

            def update_action_chunk_fitted(self, **kwargs):
                committed.update(kwargs)

        class Fuser:
            def process(self, **kwargs):
                return (
                    kwargs['next_action_chunk'],
                    kwargs['next_vel_chunk'],
                    kwargs['next_acc_chunk'],
                    kwargs['target_chunk_index'],
                )

        client.realtime_data_manager = Manager()
        client.inter_chunk_fuser = Fuser()
        client.robot = type(
            'Robot',
            (),
            {
                'get_joint_indices': lambda self: [0, 1],
                'get_step_indices': lambda self: [],
            },
        )()
        actions = np.array([[0.0, 1.0, 2.0, 3.0], [10.0, 11.0, 12.0, 13.0]])
        zeros = np.zeros_like(actions)

        accepted = client._commit_async_action_chunk(
            action_data={'_async_alignment_step': 3},
            source_action_count=4,
            action_chunk_fitted=actions,
            vel_chunk_fitted=zeros,
            acc_chunk_fitted=zeros,
            timestamps_fitted=np.arange(4, dtype=float),
            task_progress_fitted=np.arange(4, dtype=float),
        )

        self.assertTrue(accepted)
        np.testing.assert_array_equal(
            committed['action_chunk_smoothed'], actions[:, 1:]
        )
        np.testing.assert_array_equal(
            committed['timestamps_smoothed'], np.arange(1, 4, dtype=float)
        )

    def test_async_inference_rejects_excessive_lag(self):
        client = self.make_client(max_lag=1)
        action_data = {
            'type': 'vla_action',
            'pred_action': np.arange(5),
            'ref_timestamp': 0,
            'loc_timestamp': 0.0,
        }

        self.assertIsNone(
            client._prepare_action_data_for_current_step(action_data, request_observation_step=1)
        )

    def test_older_inference_result_cannot_replace_newer_chunk(self):
        client = self.make_client(max_lag=4)
        client._last_accepted_observation_step = 2
        action_data = {
            'type': 'vla_action',
            'pred_action': np.arange(5),
            'ref_timestamp': 0,
            'loc_timestamp': 0.0,
        }

        self.assertIsNone(
            client._prepare_action_data_for_current_step(action_data, request_observation_step=1)
        )


class RoboCasaVideoRecorderTest(unittest.TestCase):
    def test_grid_uses_fourth_cell_for_episode_information(self):
        frames = []

        class Writer:
            def append_data(self, frame):
                frames.append(frame)

        config = ConfigDict({
            'env_name': 'PickPlaceCounterToCabinet',
            'camera_width': 256,
            'camera_height': 256,
            'video_layout': 'grid',
            'camera': {
                'names': {
                    'head': 'head_image',
                    'left': 'left_image',
                    'right': 'right_image',
                },
            },
        })
        recorder = VideoRecorder(config, logging.getLogger(__name__))
        recorder.writer = Writer()
        obs = {
            'head_image': np.full((256, 256, 3), 10, dtype=np.uint8),
            'left_image': np.full((256, 256, 3), 20, dtype=np.uint8),
            'right_image': np.full((256, 256, 3), 30, dtype=np.uint8),
        }

        recorder.write(obs, {
            'episode': 3,
            'step': 16,
            'max_steps': 1000,
            'reward': 0.0,
            'success': False,
            'sim_time': 1.25,
        })

        self.assertEqual(frames[0].shape, (512, 512, 3))
        np.testing.assert_array_equal(frames[0][:256, :256], obs['head_image'])
        np.testing.assert_array_equal(frames[0][:256, 256:], obs['left_image'])
        np.testing.assert_array_equal(frames[0][256:, :256], obs['right_image'])
        self.assertTrue(np.any(frames[0][256:, 256:] != 0))

    def test_async_finalize_does_not_block_control(self):
        release = threading.Event()

        class Writer:
            def close(self):
                release.wait(timeout=1.0)

        recorder = VideoRecorder(ConfigDict(), logging.getLogger(__name__))
        recorder.writer = Writer()
        start = time.perf_counter()
        recorder.stop(wait=False)
        self.assertLess(time.perf_counter() - start, 0.1)
        self.assertIsNone(recorder.writer)
        release.set()
        recorder.close()


if __name__ == '__main__':
    unittest.main()
