import json
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from client.core.data_record_manager import DataRecordManager, LeRobotDatasetRecorder
from client.robots.robocasa.body_robot import RobotBody
from conf.robots_conf import get_robocasa_config
from conf.save_conf import get_record_data_config
from scripts.robocasa_eval import (
    SERVER_UNAVAILABLE_EXIT_CODE,
    ServerUnavailableError,
    _configure_recording_for_robot,
    _discard_recording_episode,
    _merge_parallel_recordings,
    _partition_recording_by_success,
    _prepare_recording,
    _reconcile_recording_progress,
    _recording_date,
    _recording_name,
    _resume_episodes,
    _run_parallel_task,
    _run_supervised_task,
    _wait_for_episode,
    _worker_ranges,
    _save_stats,
    _start_episode,
    build_parser,
    run,
)


class Recorder:
    def __init__(self, events):
        self.events = events
        self.save_path = '/project/data/recording/task_20260827'

    def set_task(self, task):
        self.events.append(('set_task', task))

    def update_camera_shape_dict(self, shapes):
        self.events.append(('shapes', shapes))

    def start_recording(self):
        self.events.append('record')


class RobocasaEvalRecordingTest(unittest.TestCase):
    def test_disk_sync_avoids_pyarrow_and_full_dataset_scan(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = get_record_data_config().lerobot
            video_keys = [
                'observation.images.robot0_agentview_left',
                'observation.images.robot0_agentview_right',
                'observation.images.robot0_eye_in_hand',
            ]
            manager = DataRecordManager.__new__(DataRecordManager)
            manager.save_path = directory
            manager.config = SimpleNamespace(lerobot=config)
            manager._active_episode_index = 2
            manager.lerobot_recorder = SimpleNamespace(
                camera_video_key_dict={str(index): key for index, key in enumerate(video_keys)}
            )
            manager._sync_shared_data = Mock()

            parquet = root / 'data/chunk-000/episode_000002.parquet'
            parquet.parent.mkdir(parents=True)
            parquet.write_bytes(b'PAR1payloadPAR1')
            meta = root / 'meta'
            meta.mkdir()
            (meta / 'episodes.jsonl').write_text(
                json.dumps({'episode_index': 1, 'length': 7}) + '\n'
                + json.dumps({'episode_index': 2, 'length': 9}) + '\n',
                encoding='utf-8',
            )
            (meta / 'info.json').write_text(json.dumps({
                'total_episodes': 3,
                'total_frames': 25,
                'total_videos': 9,
            }), encoding='utf-8')
            for video_key in video_keys:
                video = root / f'videos/chunk-000/{video_key}/episode_000002.mp4'
                video.parent.mkdir(parents=True, exist_ok=True)
                video.write_bytes(b'video')

            with patch.object(pq, 'ParquetFile', side_effect=AssertionError('PyArrow used')):
                committed_index = manager._sync_recording_from_disk()

            self.assertEqual(committed_index, 2)
            manager._sync_shared_data.assert_called_once_with(
                total_frames=25,
                total_videos=9,
                total_episodes=3,
                chunks_size=1000,
            )

    def test_disk_sync_rejects_truncated_parquet_without_pyarrow(self):
        with TemporaryDirectory() as directory:
            manager = DataRecordManager.__new__(DataRecordManager)
            manager.save_path = directory
            manager.config = SimpleNamespace(lerobot=get_record_data_config().lerobot)
            manager._active_episode_index = 0
            parquet = Path(directory) / 'data/chunk-000/episode_000000.parquet'
            parquet.parent.mkdir(parents=True)
            parquet.write_bytes(b'PAR1')

            with self.assertRaisesRegex(RuntimeError, 'Incomplete parquet'):
                manager._sync_recording_from_disk()

    @staticmethod
    def _stopped_manager(exitcode, sync_result=None, sync_error=None):
        manager = DataRecordManager.__new__(DataRecordManager)
        manager.shared_data = SimpleNamespace(running=SimpleNamespace(value=False))
        manager.writer_process = SimpleNamespace(
            exitcode=exitcode,
            is_alive=lambda: False,
        )
        manager._active_episode_index = 40
        manager._bump_recording_session_id = Mock()
        manager._clear_queues = Mock()
        manager.logger = Mock()
        if sync_error is None:
            manager._sync_recording_from_disk = Mock(return_value=sync_result)
        else:
            manager._sync_recording_from_disk = Mock(side_effect=sync_error)
        return manager

    def test_stop_recording_accepts_native_crash_after_complete_commit(self):
        manager = self._stopped_manager(exitcode=-11, sync_result=40)

        committed_index = manager.stop_recording()

        self.assertEqual(committed_index, 40)
        manager.logger.warning.assert_called_once()

    def test_stop_recording_rejects_native_crash_with_incomplete_commit(self):
        manager = self._stopped_manager(
            exitcode=-11,
            sync_error=RuntimeError('missing commit metadata'),
        )

        with self.assertRaisesRegex(RuntimeError, 'not completely committed'):
            manager.stop_recording()

    def test_prepare_recording_uses_run_specific_dataset_and_runtime_shapes(self):
        events = []
        client = SimpleNamespace(data_record_manager=Recorder(events))
        camera = SimpleNamespace(names={'head': 'front', 'hand_left': 'left'})
        robocasa = SimpleNamespace(
            split='target', camera_height=256, camera_width=320, camera=camera
        )
        config = SimpleNamespace(robots=SimpleNamespace(robocasa=robocasa))

        path = _prepare_recording(client, config, 'PnPCounterToCab', 'run-1')

        self.assertEqual(path, '/project/data/recording/task_20260827')
        self.assertEqual(
            events,
            [
                ('set_task', 'robocasa_target_PnPCounterToCab_run-1'),
                ('shapes', {'cam.head': (256, 320, 3), 'cam.hand_left': (256, 320, 3)}),
            ],
        )

    def test_start_episode_starts_recorder_before_pipeline(self):
        events = []
        client = SimpleNamespace(
            data_record_manager=Recorder(events),
            task_language_manager=SimpleNamespace(currt_language_instruction=''),
            start_observe=lambda: events.append('observe'),
            start_inference=lambda: events.append('inference'),
            start_control=lambda: events.append('control'),
            start_visualize=lambda: events.append('visualize'),
        )
        robot = SimpleNamespace(get_task_description=lambda: 'put the mug away')

        _start_episode(client, robot, visualize=False, record=True)

        self.assertEqual(events, ['record', 'observe', 'inference', 'control'])
        self.assertEqual(
            client.task_language_manager.currt_language_instruction,
            'put the mug away',
        )

    def test_record_cli_defaults(self):
        args = build_parser().parse_args(['--env_name', 'robocasa/Test', '--record'])

        self.assertTrue(args.record)
        self.assertEqual(args.record_dir, 'data/robocasa_eval/lerobot')
        self.assertEqual(args.record_fps, 20)
        self.assertEqual(args.worker_episodes, 100)
        self.assertFalse(args.no_process_isolation)
        self.assertEqual(
            _recording_name('target', 'Test', 'run'),
            'robocasa_target_Test_run',
        )

    def test_resume_episodes_requires_matching_run_and_contiguous_indices(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            metadata = {
                'env_name': 'Task', 'split': 'target', 'seed': 5, 'run_id': 'run-1'
            }
            _save_stats(
                output,
                metadata,
                [{'episode': 0, 'success': True}, {'episode': 1, 'success': False}],
            )

            self.assertEqual(len(_resume_episodes(output, metadata)), 2)
            self.assertEqual(_resume_episodes(output, {**metadata, 'run_id': 'run-2'}), [])

    def test_n_envs_cli_and_balanced_episode_ranges(self):
        args = build_parser().parse_args([
            '--env_name', 'robocasa/Test', '--n_episodes', '50', '--n_envs', '10',
        ])

        self.assertEqual(args.n_envs, 10)
        self.assertEqual(
            _worker_ranges(args.n_episodes, args.n_envs),
            [(index * 5, (index + 1) * 5) for index in range(10)],
        )

    def test_parallel_workers_merge_global_episode_order(self):
        with TemporaryDirectory() as directory:
            args = build_parser().parse_args([
                '--env_name', 'robocasa/Test', '--n_episodes', '7',
                '--n_envs', '3', '--output_dir', directory,
            ])
            calls = []

            def run_shard(shard_args, env_name, run_id):
                calls.append((shard_args._episode_start, shard_args._episode_end))
                episodes = [
                    {'episode': episode, 'success': episode % 2 == 0}
                    for episode in range(
                        shard_args._episode_start, shard_args._episode_end
                    )
                ]
                return {
                    'env_name': env_name,
                    'split': shard_args.split,
                    'seed': shard_args.seed,
                    'run_id': run_id,
                    'n_envs': shard_args.n_envs,
                    'worker_index': shard_args._worker_index,
                    'episode_start': shard_args._episode_start,
                    'episode_end': shard_args._episode_end,
                    'num_episodes': len(episodes),
                    'success_rate': 0.0,
                    'episodes': episodes,
                }

            with patch(
                'scripts.robocasa_eval._run_supervised_task', side_effect=run_shard
            ):
                stats = _run_parallel_task(args, 'robocasa/Test', 'run-1')

            self.assertEqual(sorted(calls), [(0, 2), (2, 4), (4, 7)])
            self.assertEqual(
                [episode['episode'] for episode in stats['episodes']], list(range(7))
            )
            self.assertEqual(stats['n_envs'], 3)
            self.assertTrue(
                (Path(directory) / 'evals/target/Test/stats.json').is_file()
            )

    def test_recording_date_is_stable_across_worker_restarts(self):
        self.assertEqual(_recording_date('20260904_165014'), '20260904')

    def test_supervisor_restarts_after_sigsegv_and_resumes(self):
        args = SimpleNamespace(
            _record_date=None,
            n_episodes=2,
            max_native_restarts=3,
            record=False,
        )
        complete = {
            'env_name': 'Task', 'num_episodes': 2,
            'episodes': [{'episode': 0}, {'episode': 1}],
        }
        with patch('scripts.robocasa_eval._read_supervised_stats', side_effect=[
            None, None, None, complete, complete,
        ]), patch(
            'scripts.robocasa_eval._run_worker_process', side_effect=[-11, 0]
        ) as run_worker, patch('scripts.robocasa_eval.time.sleep'):
            stats = _run_supervised_task(args, 'Task', '20260904_run')

        self.assertIs(stats, complete)
        self.assertEqual(run_worker.call_count, 2)

    def test_supervisor_waits_for_server_and_keeps_progress(self):
        args = SimpleNamespace(
            _record_date=None,
            n_episodes=4,
            max_native_restarts=3,
            record=False,
            server_reconnect_interval=10.0,
            server_reconnect_timeout=0.0,
        )
        partial = {
            'env_name': 'Task', 'num_episodes': 3,
            'episodes': [{'episode': index} for index in range(3)],
        }
        complete = {
            'env_name': 'Task', 'num_episodes': 4,
            'episodes': [{'episode': index} for index in range(4)],
        }
        with patch('scripts.robocasa_eval._read_supervised_stats', side_effect=[
            partial, partial, partial, complete, complete,
        ]), patch(
            'scripts.robocasa_eval._run_worker_process',
            side_effect=[SERVER_UNAVAILABLE_EXIT_CODE, 0],
        ) as run_worker, patch('scripts.robocasa_eval.time.sleep') as sleep:
            stats = _run_supervised_task(args, 'Task', '20260929_run')

        self.assertIs(stats, complete)
        self.assertEqual(run_worker.call_count, 2)
        sleep.assert_called_once_with(10.0)

    def test_supervisor_does_not_retry_unrelated_worker_error(self):
        args = SimpleNamespace(
            _record_date=None,
            n_episodes=1,
            max_native_restarts=3,
            record=False,
        )
        with patch(
            'scripts.robocasa_eval._read_supervised_stats', return_value=None
        ), patch('scripts.robocasa_eval._run_worker_process', return_value=1):
            with self.assertRaisesRegex(RuntimeError, 'exited with code 1'):
                _run_supervised_task(args, 'Task', '20260929_run')

    def test_supervisor_server_reconnect_timeout_is_finite_when_configured(self):
        args = SimpleNamespace(
            _record_date=None,
            n_episodes=1,
            max_native_restarts=3,
            record=False,
            server_reconnect_interval=1.0,
            server_reconnect_timeout=5.0,
        )
        with patch(
            'scripts.robocasa_eval._read_supervised_stats', return_value=None
        ), patch(
            'scripts.robocasa_eval._run_worker_process',
            return_value=SERVER_UNAVAILABLE_EXIT_CODE,
        ), patch(
            'scripts.robocasa_eval.time.monotonic', side_effect=[10.0, 16.0]
        ), patch('scripts.robocasa_eval.time.sleep'):
            with self.assertRaisesRegex(ServerUnavailableError, 'unavailable for 5s'):
                _run_supervised_task(args, 'Task', '20260929_run')

    def test_suite_stops_after_server_unavailable(self):
        with TemporaryDirectory() as directory:
            args = build_parser().parse_args([
                '--task_suite', 'Suite', '--output_dir', directory,
                '--run_id', '20260929_run',
            ])
            with patch(
                'scripts.robocasa_eval._task_suite', return_value=['TaskA', 'TaskB']
            ), patch(
                'scripts.robocasa_eval._run_parallel_task',
                side_effect=ServerUnavailableError('offline'),
            ) as run_task:
                with self.assertRaises(ServerUnavailableError):
                    run(args)

            run_task.assert_called_once()
            suite_stats = json.loads((
                Path(directory)
                / 'evals/target/suites/Suite/20260929_run/stats.json'
            ).read_text(encoding='utf-8'))
            self.assertEqual(len(suite_stats['tasks']), 1)
            self.assertEqual(suite_stats['tasks'][0]['status'], 'interrupted')

    def test_episode_wait_classifies_heartbeat_loss_as_server_unavailable(self):
        client = SimpleNamespace(
            episode_done_event=Mock(wait=Mock(return_value=False)),
            pipeline_error=None,
            vla_zmq=SimpleNamespace(is_connected=False),
        )

        with self.assertRaises(ServerUnavailableError):
            _wait_for_episode(client, 7, 60.0, 30.0, 10.0)

    def test_interrupted_recording_episode_is_removed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            meta = root / 'meta'
            data = root / 'data/chunk-000'
            meta.mkdir()
            data.mkdir(parents=True)
            info = {
                'total_episodes': 2,
                'total_frames': 5,
                'total_videos': 0,
                'total_chunks': 1,
                'chunks_size': 1000,
                'splits': {'train': '0:2'},
                'features': {},
            }
            (meta / 'info.json').write_text(json.dumps(info), encoding='utf-8')
            (meta / 'tasks.jsonl').write_text('', encoding='utf-8')
            (meta / 'episodes.jsonl').write_text(
                json.dumps({'episode_index': 0, 'length': 3}) + '\n'
                + json.dumps({'episode_index': 1, 'length': 2}) + '\n',
                encoding='utf-8',
            )
            (meta / 'episodes_stats.jsonl').write_text(
                json.dumps({'episode_index': 0, 'stats': {}}) + '\n'
                + json.dumps({'episode_index': 1, 'stats': {}}) + '\n',
                encoding='utf-8',
            )
            (data / 'episode_000001.parquet').write_bytes(b'partial')

            _discard_recording_episode(root, 1)

            restored = json.loads((meta / 'info.json').read_text(encoding='utf-8'))
            self.assertEqual(restored['total_episodes'], 1)
            self.assertEqual(restored['total_frames'], 3)
            self.assertEqual(restored['splits'], {'train': '0:1'})
            self.assertFalse((data / 'episode_000001.parquet').exists())
            episode_stats = (meta / 'episodes_stats.jsonl').read_text(encoding='utf-8')
            self.assertIn('"episode_index": 0', episode_stats)
            self.assertNotIn('"episode_index": 1', episode_stats)

    def test_resume_reconciles_one_interrupted_dataset_episode(self):
        manager = SimpleNamespace(
            shared_data=SimpleNamespace(episode_index=SimpleNamespace(value=4)),
            _sync_shared_data=Mock(),
        )
        restored_info = {
            'total_frames': 30,
            'total_videos': 9,
            'total_episodes': 3,
            'chunks_size': 1000,
        }
        with patch(
            'scripts.robocasa_eval._discard_recording_episode',
            return_value=restored_info,
        ) as discard:
            _reconcile_recording_progress(manager, '/recording', 3)

        discard.assert_called_once_with('/recording', 3)
        manager._sync_shared_data.assert_called_once_with(
            total_frames=30,
            total_videos=9,
            total_episodes=3,
            chunks_size=1000,
        )

    def test_resume_rejects_larger_recording_mismatch(self):
        manager = SimpleNamespace(
            shared_data=SimpleNamespace(episode_index=SimpleNamespace(value=5))
        )
        with self.assertRaisesRegex(RuntimeError, 'dataset has 5 episodes, stats have 3'):
            _reconcile_recording_progress(manager, '/recording', 3)

    def test_record_config_matches_lerobot_v21_image_keys(self):
        config = get_record_data_config().lerobot

        self.assertEqual(config.codebase_version, 'v2.1')
        self.assertEqual(config.image_feature_keys.head, 'observation.images.head')
        self.assertEqual(config.image_feature_keys.hand_left, 'observation.images.left')
        self.assertEqual(config.image_feature_keys.hand_right, 'observation.images.right')

    def test_stats_have_reference_dataset_fields(self):
        stats = LeRobotDatasetRecorder._array_stats(
            np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        )

        self.assertEqual(set(stats), {'mean', 'std', 'min', 'max', 'q01', 'q99'})
        self.assertEqual(stats['mean'], [2.0, 3.0])

    def test_robocasa_record_config_matches_tao_embodiment(self):
        config = SimpleNamespace(
            record=SimpleNamespace(lerobot=get_record_data_config().lerobot)
        )
        robot = SimpleNamespace(
            DATASET_ROBOT_TYPE=RobotBody.DATASET_ROBOT_TYPE,
            DATASET_CAMERA_KEYS=RobotBody.DATASET_CAMERA_KEYS,
            DATASET_INSTRUCTION_KEY=RobotBody.DATASET_INSTRUCTION_KEY,
            current_state=np.zeros(16),
            action_dim=12,
        )

        _configure_recording_for_robot(config, robot)

        record = config.record.lerobot
        self.assertEqual(record.robot_type, 'PandaOmron')
        self.assertEqual(record.state_shape, 16)
        self.assertEqual(record.action_shape, 12)
        self.assertEqual(
            record.image_feature_keys.to_dict(),
            RobotBody.DATASET_CAMERA_KEYS,
        )
        self.assertEqual(
            record.instruction_key,
            'annotation.human.task_description',
        )
        self.assertTrue(record.strict_shapes)
        self.assertEqual(record.state_action_dtype, 'float64')

    def test_robocasa_action_is_reordered_for_tao_dataset(self):
        robot = RobotBody.__new__(RobotBody)
        robot.action_dim = 12
        robot.action_layout = dict(get_robocasa_config().action_layout)
        action = np.arange(12, dtype=np.float32) / 20

        dataset_action = robot.to_dataset_action(action)

        np.testing.assert_array_equal(
            dataset_action,
            action[[7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 6]],
        )

    def test_robocasa_parquet_schema_contains_tao_instruction_key(self):
        config = get_record_data_config().lerobot
        config.instruction_key = RobotBody.DATASET_INSTRUCTION_KEY
        recorder = LeRobotDatasetRecorder(config)
        with TemporaryDirectory() as directory:
            recorder.set_task(directory)
            schema, path = recorder._prepare_parquet_file()

        self.assertFalse(Path(path).exists())

        self.assertIn(RobotBody.DATASET_INSTRUCTION_KEY, schema.names)

    def test_parallel_recordings_merge_into_one_task_dataset(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            schema = pa.schema([
                ('observation.state', pa.list_(pa.float64(), 16)),
                ('action', pa.list_(pa.float64(), 12)),
                ('episode_index', pa.int64()),
                ('frame_index', pa.int64()),
                ('index', pa.int64()),
                ('task_index', pa.int64()),
                ('annotation.human.task_description', pa.int64()),
                ('timestamp', pa.float32()),
            ])
            info = {
                'codebase_version': 'v2.1',
                'robot_type': 'PandaOmron',
                'total_episodes': 1,
                'total_frames': 2,
                'total_tasks': 2,
                'total_videos': 0,
                'total_chunks': 1,
                'chunks_size': 1000,
                'fps': 20,
                'splits': {'train': '0:1'},
                'data_path': 'data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet',
                'video_path': 'videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4',
                'features': {
                    'observation.state': {'dtype': 'float64', 'shape': [16]},
                    'action': {'dtype': 'float64', 'shape': [12]},
                    'annotation.human.task_description': {
                        'dtype': 'int64', 'shape': [1],
                    },
                    'timestamp': {'dtype': 'float32', 'shape': [1]},
                },
            }
            results = []
            sources = []
            for worker_index, success in enumerate((True, False)):
                source = root / (
                    f'robocasa_target_Test_run-1_env{worker_index:02d}_20260929'
                )
                sources.append(source)
                meta = source / 'meta'
                data = source / 'data/chunk-000'
                meta.mkdir(parents=True)
                data.mkdir(parents=True)
                (meta / 'info.json').write_text(json.dumps(info), encoding='utf-8')
                task_names = (
                    ('task-a', 'task-b') if worker_index == 0
                    else ('task-b', 'task-a')
                )
                (meta / 'tasks.jsonl').write_text(
                    ''.join(
                        json.dumps({'task_index': index, 'task': task}) + '\n'
                        for index, task in enumerate(task_names)
                    ),
                    encoding='utf-8',
                )
                (meta / 'episodes.jsonl').write_text(
                    json.dumps({
                        'episode_index': 0,
                        'tasks': [task_names[0]],
                        'length': 2,
                    })
                    + '\n',
                    encoding='utf-8',
                )
                rows = [{
                    'observation.state': [float(worker_index)] * 16,
                    'action': [float(worker_index)] * 12,
                    'episode_index': 0,
                    'frame_index': frame_index,
                    'index': frame_index,
                    'task_index': 0,
                    'annotation.human.task_description': 0,
                    'timestamp': frame_index / 20,
                } for frame_index in range(2)]
                pq.write_table(
                    pa.Table.from_pylist(rows, schema=schema),
                    data / 'episode_000000.parquet',
                )
                results.append({
                    'worker_index': worker_index,
                    'lerobot_dataset_path': str(source),
                    'episodes': [{
                        'episode': worker_index,
                        'success': success,
                        'recording_episode_index': 0,
                    }],
                })

            paths = _merge_parallel_recordings(results)

            destination = root / 'robocasa_target_Test_run-1_20260929'
            self.assertEqual(paths, {
                'success': str(destination / 'success'),
                'failure': str(destination / 'failure'),
            })
            self.assertTrue((destination / 'success/meta/info.json').is_file())
            self.assertTrue((destination / 'failure/meta/info.json').is_file())
            self.assertFalse(any(source.exists() for source in sources))
            success_rows = pq.read_table(
                destination / 'success/data/chunk-000/episode_000000.parquet'
            ).to_pylist()
            failure_rows = pq.read_table(
                destination / 'failure/data/chunk-000/episode_000000.parquet'
            ).to_pylist()
            self.assertEqual(success_rows[0]['action'], [0.0] * 12)
            self.assertEqual(failure_rows[0]['action'], [1.0] * 12)
            self.assertEqual(success_rows[0]['task_index'], 0)
            self.assertEqual(failure_rows[0]['task_index'], 1)
            self.assertEqual(
                success_rows[0]['annotation.human.task_description'], 0
            )
            self.assertEqual(
                failure_rows[0]['annotation.human.task_description'], 1
            )

    def test_recording_is_partitioned_and_reindexed_by_success(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            meta = root / 'meta'
            data = root / 'data/chunk-000'
            meta.mkdir()
            data.mkdir(parents=True)
            info = {
                'codebase_version': 'v2.1',
                'robot_type': 'PandaOmron',
                'total_episodes': 3,
                'total_frames': 6,
                'total_tasks': 1,
                'total_videos': 0,
                'total_chunks': 1,
                'chunks_size': 1000,
                'fps': 20,
                'splits': {'train': '0:3'},
                'data_path': 'data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet',
                'video_path': 'videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4',
                'features': {
                    'observation.state': {'dtype': 'float64', 'shape': [16]},
                    'action': {'dtype': 'float64', 'shape': [12]},
                },
            }
            (meta / 'info.json').write_text(json.dumps(info), encoding='utf-8')
            (meta / 'tasks.jsonl').write_text(
                json.dumps({'task_index': 0, 'task': 'task'}) + '\n', encoding='utf-8'
            )
            (meta / 'episodes.jsonl').write_text(
                ''.join(
                    json.dumps({'episode_index': index, 'tasks': ['task'], 'length': 2}) + '\n'
                    for index in range(3)
                ),
                encoding='utf-8',
            )
            schema = pa.schema([
                ('observation.state', pa.list_(pa.float64(), 16)),
                ('action', pa.list_(pa.float64(), 12)),
                ('episode_index', pa.int64()),
                ('frame_index', pa.int64()),
                ('index', pa.int64()),
                ('task_index', pa.int64()),
                ('timestamp', pa.float32()),
            ])
            for episode_index in range(3):
                rows = [{
                    'observation.state': [float(episode_index)] * 16,
                    'action': [float(episode_index)] * 12,
                    'episode_index': episode_index,
                    'frame_index': frame_index,
                    'index': episode_index * 2 + frame_index,
                    'task_index': 0,
                    'timestamp': frame_index / 20,
                } for frame_index in range(2)]
                pq.write_table(
                    pa.Table.from_pylist(rows, schema=schema),
                    data / f'episode_{episode_index:06d}.parquet',
                )

            paths = _partition_recording_by_success(root, [
                {'success': True}, {'success': False}, {'success': True},
            ])

            self.assertEqual(set(paths), {'success', 'failure'})
            self.assertFalse((root / 'data').exists())
            success_info = json.loads((root / 'success/meta/info.json').read_text())
            failure_info = json.loads((root / 'failure/meta/info.json').read_text())
            self.assertEqual(success_info['total_episodes'], 2)
            self.assertEqual(success_info['total_frames'], 4)
            self.assertEqual(failure_info['total_episodes'], 1)
            success_second = pq.read_table(
                root / 'success/data/chunk-000/episode_000001.parquet'
            ).to_pylist()
            self.assertEqual([row['episode_index'] for row in success_second], [1, 1])
            self.assertEqual([row['index'] for row in success_second], [2, 3])
            self.assertEqual(success_second[0]['action'], [2.0] * 12)


if __name__ == '__main__':
    unittest.main()
