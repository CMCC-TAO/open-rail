"""Evaluate a VLA policy in RoboCasa through VLAClientAsync."""

import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from client.simulation.evaluation import (
    SERVER_UNAVAILABLE_EXIT_CODE, ServerUnavailableError,
    build_parser as build_simulation_parser,
    build_client as build_simulation_client,
    get_simulation_config,
    configure_mujoco_gpu, worker_gpu,
    sample_ratio as _sample_ratio,
    wait_for_server as _wait_for_server,
    atomic_json as _atomic_json,
    save_stats as _save_stats,
    episode_bounds as _episode_bounds,
    worker_ranges as _worker_ranges,
    save_suite_stats as _save_suite_stats,
    configure_recording_for_robot as _configure_recording_for_robot,
    recording_date as _recording_date,
    resume_episodes as _resume_episodes,
    start_episode as _start_episode,
    reset_episode as _reset_episode,
    discard_recording_episode as _discard_recording_episode,
    reconcile_recording_progress as _reconcile_recording_progress,
    wait_for_episode as _wait_for_episode,
)
from client.simulation.recording_exports import (
    _array_stats as _array_stats,
    _link_or_copy as _link_or_copy,
    _dataset_metadata as _dataset_metadata,
    _task_index_remap as _task_index_remap,
    _remap_table_task_indices as _remap_table_task_indices,
    _write_dataset_selection as _write_dataset_selection,
    _write_dataset_partition as _write_dataset_partition,
    _recording_result_pairs as _recording_result_pairs,
    _resolve_recording_results as _resolve_recording_results,
    _partition_recording_by_success as _partition_recording_by_success,
    _merge_parallel_recordings as _merge_parallel_recordings,
)

from client.core.zmq_client import ZMQClient
from client.utils.util import apply_user_config, load_user_config
from conf.robots_conf import RobotType


def _task_horizon(env_name, fallback):
    if fallback is not None:
        return int(fallback)
    try:
        from robocasa.utils.dataset_registry_utils import get_task_horizon

        return int(get_task_horizon(env_name.split('/')[-1]))
    except (ImportError, KeyError, ValueError):
        return 1000


def _task_suite(task_suite):
    from robocasa.utils.dataset_registry import TASK_SET_REGISTRY

    if ',' in task_suite:
        tasks = [task.strip() for task in task_suite.split(',')]
        if len(tasks) != len(set(tasks)) or any(task not in TASK_SET_REGISTRY['all_tasks'] for task in tasks):
            raise ValueError('Custom RoboCasa task list contains duplicate or unknown tasks')
        return tasks
    if task_suite not in TASK_SET_REGISTRY:
        available = ', '.join(sorted(TASK_SET_REGISTRY))
        raise ValueError(f'Unknown RoboCasa task suite {task_suite!r}; available: {available}')
    tasks = list(TASK_SET_REGISTRY[task_suite])
    if not tasks:
        raise ValueError(f'RoboCasa task suite {task_suite!r} is empty')
    return tasks


def _build_client(config, server_wait_timeout):
    zmq_client = ZMQClient(config.vla_zmq)
    robot = None
    try:
        _wait_for_server(zmq_client, server_wait_timeout)
        from client.robots.robocasa_pandas.body_robot import RobotBody

        robot = RobotBody(config.robots.robocasa_pandas)
        client = build_simulation_client(config, robot, zmq_client)
        return client, robot
    except Exception:
        if robot is not None:
            robot.close()
        zmq_client.close()
        raise


def _recording_name(split, task_name, run_id):
    return f'robocasa_{split}_{task_name}_{run_id}'


def _prepare_recording(client, config, task_name, run_id):
    recorder = client.data_record_manager
    recorder.set_task(_recording_name(config.robots.robocasa_pandas.split, task_name, run_id))
    height = int(config.robots.robocasa_pandas.camera_height)
    width = int(config.robots.robocasa_pandas.camera_width)
    camera_shapes = {
        f'cam.{camera_name}': (height, width, 3)
        for camera_name in config.robots.robocasa_pandas.camera.names
    }
    recorder.update_camera_shape_dict(camera_shapes)
    return recorder.save_path


def _run_task(args, env_name, run_id):
    device = configure_mujoco_gpu(args.gpu, getattr(args, '_worker_index', None))
    if device is not None:
        logging.info('RoboCasa worker %s uses GPU %s', getattr(args, '_worker_index', None), device)
    config = get_simulation_config()
    if args.user_conf:
        config = apply_user_config(config, load_user_config(args.user_conf))

    task_name = env_name.split('/')[-1]
    task_output = Path(args.output_dir) / 'evals' / args.split / task_name
    worker_index = getattr(args, '_worker_index', None)
    if worker_index is not None:
        task_output = task_output / 'workers' / run_id / f'env_{worker_index:02d}'
    episode_start, episode_end = _episode_bounds(args)
    base_metadata = {
        'env_name': env_name,
        'split': args.split,
        'seed': args.seed,
        'run_id': run_id,
        'n_envs': args.n_envs,
    }
    if worker_index is not None:
        base_metadata['worker_index'] = worker_index
        base_metadata['episode_start'] = episode_start
        base_metadata['episode_end'] = episode_end
    episodes = (
        _resume_episodes(task_output, base_metadata, episode_start)
        if args._worker else []
    )
    start_episode = episode_start + len(episodes)
    if start_episode >= episode_end:
        return json.loads((task_output / 'stats.json').read_text(encoding='utf-8'))

    config.vla_zmq.ip = args.server_ip
    config.vla_zmq.port = str(args.server_port)
    config.vla_zmq.infer_timeout = args.infer_timeout_ms
    config.robots.type = RobotType.ROBOCASA_PANDAS
    config.robots.robocasa_pandas.env_name = env_name
    config.robots.robocasa_pandas.enable_render = True
    config.robots.robocasa_pandas.split = args.split
    config.robots.robocasa_pandas.seed = args.seed
    config.robots.robocasa_pandas.episode_offset = start_episode
    config.robots.robocasa_pandas.preview_worker_index = worker_index
    config.robots.robocasa_pandas.max_episode_steps = _task_horizon(env_name, args.max_episode_steps)
    config.robots.robocasa_pandas.video_dir = '' if args.no_video else str(task_output / 'videos' / run_id)
    config.robots.robocasa_pandas.video_fps = args.video_fps
    config.robots.robocasa_pandas.video_layout = args.video_layout
    config.visualize.port = args.visualize_port

    from client.simulation.evaluation import configure_pipeline
    configure_pipeline(config, args)
    if args.mode == 'async' and config.inter_chunk.inter_chunk_mode == 'min_jerk':
        logging.warning(
            'RoboCasa min_jerk smooths delta/velocity command values at every async '
            'replan; compare async raw+sync first when measuring async-mode accuracy.'
        )
    config.record.switch = args.record
    if args.record:
        config.record.save_dir = args.record_dir
        config.record.dataset_date = args._record_date or _recording_date(run_id)
        config.record.lerobot.fps = args.record_fps

    client, robot = _build_client(config, args.server_wait_timeout)
    recording_path = None
    if args.record:
        recording_run_id = (
            run_id if worker_index is None else f'{run_id}_env{worker_index:02d}'
        )
        recording_path = _prepare_recording(client, config, task_name, recording_run_id)
        if args._worker:
            try:
                _reconcile_recording_progress(
                    client.data_record_manager, recording_path, len(episodes)
                )
            except Exception:
                client.close()
                robot.close()
                raise
    metadata = {
        **base_metadata,
        'mode': args.mode,
        'n_action_steps': args.n_action_steps,
        'intra_chunk_mode': config.intra_chunk.intra_chunk_mode,
        'intra_chunk_sample_ratio': config.intra_chunk.output_sample_ratio,
        'inter_chunk_mode': config.inter_chunk.inter_chunk_mode,
        'async_replenish_threshold': config.rdm.action_replenish_threshold,
        'max_async_observation_lag_steps': config.rdm.max_async_observation_lag_steps,
        'lerobot_dataset_path': recording_path,
    }
    end_episode = episode_end
    if args._worker:
        end_episode = min(end_episode, start_episode + args.worker_episodes)
    discard_recording_episode = False
    try:
        _start_episode(client, robot, args.visualize, args.record)
        print(
            f'RoboCasa client started; waiting for inference from {config.vla_zmq.ip}:'
            f'{config.vla_zmq.port} (timeout={config.vla_zmq.infer_timeout} ms, '
            f'mode={config.rdm.mode}, intra={config.intra_chunk.intra_chunk_mode}, '
            f'inter={config.inter_chunk.inter_chunk_mode}, '
            f'replenish={config.rdm.action_replenish_threshold}, '
            f'max_lag={config.rdm.max_async_observation_lag_steps})',
            flush=True,
        )
        for episode in range(start_episode, end_episode):
            completed = _wait_for_episode(
                client,
                episode,
                args.episode_timeout,
                args.stall_timeout,
                args.progress_interval,
            )
            if client.pipeline_error is not None:
                raise RuntimeError(
                    f'RoboCasa evaluation pipeline failed during episode {episode + 1}'
                ) from client.pipeline_error
            result = robot.get_episode_result()
            if not completed or result is None:
                result = {
                    'episode': episode,
                    'success': False,
                    'steps': None,
                    'terminated': False,
                    'truncated': True,
                    'timeout': True,
                }
            result['episode'] = episode
            if args.record:
                recorded_episode_index = client.data_record_manager.stop_recording()
                result['recording_episode_index'] = recorded_episode_index
            episodes.append(result)
            _save_stats(task_output, metadata, episodes)
            success_rate = float(np.mean([item['success'] for item in episodes]))
            print(
                f"Episode {episode + 1}/{args.n_episodes}: success={result['success']}, "
                f"steps={result['steps']}, cumulative_success_rate={success_rate:.3f}",
                flush=True,
            )
            if episode + 1 < end_episode:
                _reset_episode(client, robot, args.visualize, args.record)
    except ServerUnavailableError:
        discard_recording_episode = args.record
        raise
    finally:
        client.close()
        robot.close()
        if discard_recording_episode:
            _discard_recording_episode(recording_path, len(episodes))

    if args.record and not args._worker:
        dataset_paths = _partition_recording_by_success(recording_path, episodes)
        metadata['lerobot_dataset_paths'] = dataset_paths
        metadata.pop('lerobot_dataset_path', None)
        for outcome, path in dataset_paths.items():
            print(f'Saved {outcome} LeRobot dataset to {path}', flush=True)
    stats_path, stats = _save_stats(task_output, metadata, episodes)
    print(f'Saved evaluation statistics to {stats_path}', flush=True)
    return stats


def _task_stats_path(args, env_name):
    task_name = env_name.split('/')[-1]
    task_output = Path(args.output_dir) / 'evals' / args.split / task_name
    worker_index = getattr(args, '_worker_index', None)
    if worker_index is not None:
        task_output = task_output / 'workers' / args.run_id / f'env_{worker_index:02d}'
    return task_output / 'stats.json'


def _read_supervised_stats(args, env_name, run_id):
    path = _task_stats_path(args, env_name)
    if not path.is_file():
        return None
    try:
        stats = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if stats.get('run_id') != run_id or stats.get('env_name') != env_name:
        return None
    return stats


def _worker_command(args, env_name, run_id, record_date):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        *sys.argv[1:],
        '--_worker',
        '--_worker_env_name',
        env_name,
        '--_record_date',
        record_date,
        '--run_id',
        run_id,
    ]
    worker_index = getattr(args, '_worker_index', None)
    device = worker_gpu(args.gpu, worker_index)
    if device is not None:
        command.extend(['--gpu', device])
    if worker_index is not None:
        command.extend([
            '--_worker_index', str(worker_index),
            '--_episode_start', str(args._episode_start),
            '--_episode_end', str(args._episode_end),
        ])
    return command


def _run_worker_process(command, cancel_event=None):
    from client.simulation.evaluation import run_isolated_worker
    return run_isolated_worker(command, cancel_event=cancel_event)


def _finalize_supervised_recording(args, stats):
    if not args.record or 'lerobot_dataset_paths' in stats:
        return stats
    recording_path = stats.get('lerobot_dataset_path')
    if not recording_path:
        raise RuntimeError('Completed recording has no LeRobot dataset path')
    dataset_paths = _partition_recording_by_success(recording_path, stats['episodes'])
    metadata = {
        key: value for key, value in stats.items()
        if key not in {'num_episodes', 'success_rate', 'episodes', 'lerobot_dataset_path'}
    }
    metadata['lerobot_dataset_paths'] = dataset_paths
    task_output = _task_stats_path(args, stats['env_name']).parent
    _, stats = _save_stats(task_output, metadata, stats['episodes'])
    for outcome, path in dataset_paths.items():
        print(f'Saved {outcome} LeRobot dataset to {path}', flush=True)
    return stats


def _run_supervised_task(args, env_name, run_id):
    from client.simulation.evaluation import EvaluationRunner
    return EvaluationRunner(sys.modules[__name__], 'RoboCasa')._run_supervised_task(args, env_name, run_id)


def _run_parallel_task(args, env_name, run_id):
    from client.simulation.evaluation import EvaluationRunner
    return EvaluationRunner(sys.modules[__name__], 'RoboCasa')._run_parallel_task(args, env_name, run_id)


def run(args):
    worker_gpu(args.gpu)
    run_id = args.run_id or time.strftime('%Y%m%d_%H%M%S')
    if args._worker:
        return _run_task(args, args._worker_env_name or args.env_name, run_id)
    if args.env_name:
        if args.no_process_isolation:
            return _run_task(args, args.env_name, run_id)
        if args.n_envs > 1:
            return _run_parallel_task(args, args.env_name, run_id)
        return _run_supervised_task(args, args.env_name, run_id)

    if args.split != 'target' and args.task_suite == 'target50':
        raise ValueError('target50 must be evaluated with --split target')
    task_names = _task_suite(args.task_suite)
    suite_name = 'custom' if ',' in args.task_suite else args.task_suite
    suite_output = Path(args.output_dir) / 'evals' / args.split / 'suites' / suite_name / run_id
    suite_metadata = {
        'task_suite': args.task_suite,
        'split': args.split,
        'run_id': run_id,
        'n_episodes_per_task': args.n_episodes,
        'mode': args.mode,
        'n_action_steps': args.n_action_steps,
        'intra_chunk_mode': args.intra_chunk_mode or 'raw',
        'intra_chunk_sample_ratio': (
            1.0 if (args.intra_chunk_mode or 'raw') == 'raw'
            else args.intra_chunk_sample_ratio
        ),
        'inter_chunk_mode': args.inter_chunk_mode or 'sync',
        'async_replenish_threshold': (
            args.async_replenish_threshold
            if args.async_replenish_threshold is not None
            else max(1, args.n_action_steps // 4 *3)
        ) if args.mode == 'async' else 0,
        'max_async_observation_lag_steps': (
            args.max_async_observation_lag_steps
            if args.max_async_observation_lag_steps is not None
            else max(1, args.n_action_steps - 1)
        ),
    }
    task_results = []
    for index, env_name in enumerate(task_names, start=1):
        print(f'[{index}/{len(task_names)}] Evaluating RoboCasa task {env_name}', flush=True)
        try:
            stats = (
                _run_task(args, env_name, run_id)
                if args.no_process_isolation
                else (
                    _run_parallel_task(args, env_name, run_id)
                    if args.n_envs > 1
                    else _run_supervised_task(args, env_name, run_id)
                )
            )
            task_name = env_name.split('/')[-1]
            task_results.append({
                'env_name': env_name,
                'status': 'completed',
                'num_episodes': stats['num_episodes'],
                'num_successes': sum(item['success'] for item in stats['episodes']),
                'success_rate': stats['success_rate'],
                'stats_path': str(
                    Path(args.output_dir) / 'evals' / args.split / task_name / 'stats.json'
                ),
            })
        except ServerUnavailableError as exc:
            logging.exception('RoboCasa task %s paused because the server is unavailable', env_name)
            task_results.append({
                'env_name': env_name,
                'status': 'interrupted',
                'error': f'{type(exc).__name__}: {exc}',
            })
            _save_suite_stats(suite_output, suite_metadata, task_results)
            raise
        except Exception as exc:
            logging.exception('RoboCasa task %s failed', env_name)
            task_results.append({
                'env_name': env_name,
                'status': 'failed',
                'error': f'{type(exc).__name__}: {exc}',
            })
        suite_path, _ = _save_suite_stats(suite_output, suite_metadata, task_results)

    suite_path, suite_stats = _save_suite_stats(
        suite_output, suite_metadata, task_results
    )
    print(f'Saved suite statistics to {suite_path}', flush=True)
    return suite_stats


def build_parser():
    parser = build_simulation_parser(__doc__)
    parser.add_argument('--split', choices=['pretrain', 'target'], default='target')
    parser.add_argument('--mujoco_gl', choices=['egl', 'osmesa', 'glfw'])
    parser.set_defaults(output_dir='data/robocasa_eval', record_dir='data/robocasa_eval/lerobot')
    return parser


def main():
    args = build_parser().parse_args()
    positive_args = (
        args.n_episodes,
        args.n_envs,
        args.n_action_steps,
        args.infer_timeout_ms,
        args.control_period_ms,
        args.episode_timeout,
        args.stall_timeout,
        args.progress_interval,
        args.record_fps,
        args.worker_episodes,
        args.server_reconnect_interval,
    )
    if any(value <= 0 for value in positive_args):
        raise ValueError('episode counts, action counts, and timeouts must be positive')
    if args.max_native_restarts < 0:
        raise ValueError('max_native_restarts must be non-negative')
    if args.server_reconnect_timeout < 0:
        raise ValueError('server_reconnect_timeout must be non-negative')
    if args.n_envs > 1 and args.no_process_isolation:
        raise ValueError('n_envs > 1 requires process isolation')
    if args.n_envs > 1 and args.visualize:
        raise ValueError('visualization is not supported with n_envs > 1')
    if args.async_replenish_threshold is not None and not (
        0 <= args.async_replenish_threshold < args.n_action_steps
    ):
        raise ValueError('async_replenish_threshold must be in [0, n_action_steps)')
    if (
        args.max_async_observation_lag_steps is not None
        and args.max_async_observation_lag_steps < 0
    ):
        raise ValueError('max_async_observation_lag_steps must be non-negative')
    if args.mujoco_gl:
        os.environ['MUJOCO_GL'] = args.mujoco_gl
    if args.record and Path(args.record_dir).is_absolute():
        raise ValueError('record_dir must be relative to the project root')
    os.chdir(PROJECT_ROOT)
    try:
        from conf.logging_conf import setup_logging

        setup_logging('robocasa_eval.log', __name__)
    except ImportError:
        logging.basicConfig(level=logging.INFO)
    try:
        run(args)
    except ServerUnavailableError as exc:
        if not args._worker:
            raise
        logging.error('%s', exc)
        raise SystemExit(SERVER_UNAVAILABLE_EXIT_CODE) from exc


if __name__ == '__main__':
    main()
