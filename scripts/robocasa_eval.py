"""Evaluate a VLA policy in RoboCasa through VLAClientAsync."""

import argparse
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

from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
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

from client.simulation.vla_client import VLAClientAsync
from client.core.zmq_client import ZMQClient
from client.utils.util import apply_user_config, load_user_config
from conf.client_conf import get_client_config
from conf.robots_conf import RobotType


SERVER_UNAVAILABLE_EXIT_CODE = 75


class ServerUnavailableError(RuntimeError):
    pass


def _sample_ratio(value):
    ratio = float(value)
    if ratio < 1.0:
        raise argparse.ArgumentTypeError('sample ratio must be at least 1.0')
    return ratio


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

    if task_suite not in TASK_SET_REGISTRY:
        available = ', '.join(sorted(TASK_SET_REGISTRY))
        raise ValueError(f'Unknown RoboCasa task suite {task_suite!r}; available: {available}')
    tasks = list(TASK_SET_REGISTRY[task_suite])
    if not tasks:
        raise ValueError(f'RoboCasa task suite {task_suite!r} is empty')
    return tasks


def _wait_for_server(client, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.is_connected:
            return
        time.sleep(0.1)
    raise ServerUnavailableError(
        f'VLA server is not responding at {client.client_addr}'
    )


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def _save_stats(output_dir, metadata, episodes):
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = {
        **metadata,
        'num_episodes': len(episodes),
        'success_rate': float(np.mean([item['success'] for item in episodes])) if episodes else 0.0,
        'episodes': episodes,
    }
    path = output_dir / 'stats.json'
    temporary_path = path.with_suffix('.json.tmp')
    with temporary_path.open('w', encoding='utf-8') as file:
        json.dump(stats, file, indent=2)
    os.replace(temporary_path, path)
    return path, stats


def _episode_bounds(args):
    episode_start = getattr(args, '_episode_start', None)
    episode_end = getattr(args, '_episode_end', None)
    start = 0 if episode_start is None else episode_start
    end = args.n_episodes if episode_end is None else episode_end
    return start, end


def _worker_ranges(n_episodes, n_envs):
    worker_count = min(n_episodes, n_envs)
    return [
        (index * n_episodes // worker_count, (index + 1) * n_episodes // worker_count)
        for index in range(worker_count)
    ]


def _save_suite_stats(output_dir, metadata, tasks):
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = [task for task in tasks if task['status'] == 'completed']
    total_episodes = sum(task['num_episodes'] for task in completed)
    total_successes = sum(task['num_successes'] for task in completed)
    stats = {
        **metadata,
        'num_tasks': len(tasks),
        'num_completed_tasks': len(completed),
        'num_failed_tasks': len(tasks) - len(completed),
        'num_episodes': total_episodes,
        'success_rate': total_successes / total_episodes if total_episodes else 0.0,
        'macro_task_success_rate': (
            float(np.mean([task['success_rate'] for task in completed]))
            if completed else 0.0
        ),
        'tasks': tasks,
    }
    path = output_dir / 'stats.json'
    _atomic_json(path, stats)
    return path, stats


def _configure_recording_for_robot(config, robot):
    record_config = config.record.lerobot
    record_config.robot_type = robot.DATASET_ROBOT_TYPE
    record_config.state_shape = int(robot.current_state.size)
    record_config.action_shape = int(robot.action_dim)
    record_config.image_feature_keys = robot.DATASET_CAMERA_KEYS
    record_config.instruction_key = robot.DATASET_INSTRUCTION_KEY
    record_config.strict_shapes = True
    record_config.state_action_dtype = 'float64'


def _build_client(config, server_wait_timeout):
    zmq_client = ZMQClient(config.vla_zmq)
    robot = None
    try:
        _wait_for_server(zmq_client, server_wait_timeout)
        from client.robots.robocasa.body_robot import RobotBody

        robot = RobotBody(config.robots.robocasa)
        config.rdm.action_layout = config.robots.robocasa.action_layout
        config.intra_chunk.action_layout = config.robots.robocasa.action_layout
        _configure_recording_for_robot(config, robot)
        client = VLAClientAsync(
            config=config,
            realtime_data_manager=RealtimeDataManager(config.rdm),
            inter_chunk_fuser=InterChunkFuser(config.inter_chunk),
            intra_chunk_smoother=IntraChunkSmoother(config.intra_chunk),
            task_language_manager=TaskLanguageManager(config.language),
            vla_zmq_client=zmq_client,
            robot=robot,
        )
        return client, robot
    except Exception:
        if robot is not None:
            robot.close()
        zmq_client.close()
        raise


def _recording_name(split, task_name, run_id):
    return f'robocasa_{split}_{task_name}_{run_id}'


def _recording_date(run_id):
    candidate = str(run_id)[:8]
    try:
        time.strptime(candidate, '%Y%m%d')
    except ValueError:
        return time.strftime('%Y%m%d')
    return candidate


def _resume_episodes(task_output, metadata, episode_start=0):
    path = task_output / 'stats.json'
    if not path.is_file():
        return []
    try:
        stats = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []
    identity = ['env_name', 'split', 'seed', 'run_id', 'n_envs']
    identity.extend(
        key for key in ('worker_index', 'episode_start', 'episode_end')
        if key in metadata
    )
    if any(stats.get(key) != metadata.get(key) for key in identity):
        return []
    episodes = stats.get('episodes', [])
    if not isinstance(episodes, list):
        raise RuntimeError(f'Invalid resumable statistics: {path}')
    for index, episode in enumerate(episodes, start=episode_start):
        if int(episode.get('episode', -1)) != index:
            raise RuntimeError(f'Non-contiguous episode results in {path}')
    return episodes




def _prepare_recording(client, config, task_name, run_id):
    recorder = client.data_record_manager
    recorder.set_task(_recording_name(config.robots.robocasa.split, task_name, run_id))
    height = int(config.robots.robocasa.camera_height)
    width = int(config.robots.robocasa.camera_width)
    camera_shapes = {
        f'cam.{camera_name}': (height, width, 3)
        for camera_name in config.robots.robocasa.camera.names
    }
    recorder.update_camera_shape_dict(camera_shapes)
    return recorder.save_path


def _start_episode(client, robot, visualize, record=False):
    language = robot.get_task_description()
    if not language:
        raise RuntimeError('RoboCasa did not provide a task description')
    client.task_language_manager.currt_language_instruction = language
    if record:
        client.data_record_manager.start_recording()
    client.start_observe()
    client.start_inference()
    client.start_control()
    if visualize:
        client.start_visualize()


def _reset_episode(client, robot, visualize, record=False):
    client.pause()
    client.realtime_data_manager.cancel_waiters()
    client.realtime_data_manager.clear()
    client.reset()
    robot.reset()
    _start_episode(client, robot, visualize, record)


def _discard_recording_episode(recording_path, episode_index):
    from client.simulation.data_record_manager import LeRobotDatasetParser

    parser = LeRobotDatasetParser(recording_path)
    chunk_index = episode_index // max(1, parser.chunks_size)
    parser.delete_episode(
        f'chunk-{chunk_index:03d}/episode_{episode_index:06d}'
    )
    info_path = Path(recording_path) / 'meta' / 'info.json'
    info = json.loads(info_path.read_text(encoding='utf-8'))
    if int(info.get('total_episodes', -1)) != episode_index:
        raise RuntimeError(
            f'Cannot discard interrupted recording episode {episode_index} from '
            f'{recording_path}'
        )
    info['splits'] = {'train': f'0:{episode_index}'}
    temporary_path = info_path.with_suffix('.json.tmp')
    temporary_path.write_text(json.dumps(info, indent=2), encoding='utf-8')
    os.replace(temporary_path, info_path)
    episode_stats_path = Path(recording_path) / 'meta' / 'episodes_stats.jsonl'
    if episode_stats_path.is_file():
        rows = [
            json.loads(line)
            for line in episode_stats_path.read_text(encoding='utf-8').splitlines()
            if line.strip()
        ]
        episode_stats_path.write_text(
            ''.join(
                json.dumps(row, ensure_ascii=False) + '\n'
                for row in rows
                if int(row.get('episode_index', -1)) != episode_index
            ),
            encoding='utf-8',
        )
    return info


def _reconcile_recording_progress(manager, recording_path, expected_episodes):
    recorded_episodes = int(manager.shared_data.episode_index.value)
    if recorded_episodes == expected_episodes:
        return
    if recorded_episodes != expected_episodes + 1:
        raise RuntimeError(
            'Cannot resume recording: '
            f'dataset has {recorded_episodes} episodes, stats have {expected_episodes}'
        )
    info = _discard_recording_episode(recording_path, expected_episodes)
    manager._sync_shared_data(
        total_frames=int(info['total_frames']),
        total_videos=int(info['total_videos']),
        total_episodes=int(info['total_episodes']),
        chunks_size=int(info['chunks_size']),
    )
    print(
        f'Removed interrupted LeRobot episode {expected_episodes} from {recording_path}',
        flush=True,
    )


def _wait_for_episode(client, episode, timeout, stall_timeout, progress_interval):
    deadline = time.monotonic() + timeout
    last_progress_at = time.monotonic()
    next_report_at = last_progress_at + progress_interval
    last_step = None
    while True:
        now = time.monotonic()
        if now >= deadline:
            return False
        if client.episode_done_event.wait(min(1.0, deadline - now)):
            return True
        if client.pipeline_error is not None:
            raise RuntimeError(
                f'RoboCasa evaluation pipeline failed during episode {episode + 1}'
            ) from client.pipeline_error
        if not client.vla_zmq.is_connected:
            raise ServerUnavailableError(
                f'VLA server disconnected during episode {episode + 1}'
            )

        step_result = client.last_step_result
        current_step = None if step_result is None else step_result.observation_step
        now = time.monotonic()
        if current_step != last_step:
            last_step = current_step
            last_progress_at = now
        if now - last_progress_at >= stall_timeout:
            raise TimeoutError(
                f'RoboCasa episode {episode + 1} stalled for {stall_timeout:g}s '
                f'at simulation step {current_step}; check the client and model-server logs'
            )
        if now >= next_report_at:
            print(
                f'Episode {episode + 1} running: simulation_step={current_step}',
                flush=True,
            )
            next_report_at = now + progress_interval


def _run_task(args, env_name, run_id):
    config = get_client_config()
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
    config.robots.type = RobotType.ROBOCASA
    config.robots.robocasa.env_name = env_name
    config.robots.robocasa.split = args.split
    config.robots.robocasa.seed = args.seed
    config.robots.robocasa.episode_offset = start_episode
    config.robots.robocasa.preview_worker_index = worker_index
    config.robots.robocasa.max_episode_steps = _task_horizon(env_name, args.max_episode_steps)
    config.robots.robocasa.video_dir = '' if args.no_video else str(task_output / 'videos' / run_id)
    config.robots.robocasa.video_fps = args.video_fps
    config.robots.robocasa.video_layout = args.video_layout
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
    suite_output = (
        Path(args.output_dir) / 'evals' / args.split / 'suites' / args.task_suite / run_id
    )
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
    parser = argparse.ArgumentParser(description=__doc__)
    task_selection = parser.add_mutually_exclusive_group(required=True)
    task_selection.add_argument('--env_name')
    task_selection.add_argument(
        '--task_suite',
        help='RoboCasa registry task suite, for example target50',
    )
    parser.add_argument('--split', choices=['pretrain', 'target'], default='target')
    parser.add_argument('--n_episodes', type=int, default=50)
    parser.add_argument('--n_envs', type=int, default=10)
    parser.add_argument('--n_action_steps', type=int, default=16)
    parser.add_argument('--control_period_ms', type=float, default=1.0)
    parser.add_argument('--mode', choices=['sync', 'async'], default='sync')
    parser.add_argument(
        '--async_replenish_threshold',
        type=int,
        help='Request a new chunk when this many actions remain (default: half the chunk)',
    )
    parser.add_argument(
        '--max_async_observation_lag_steps',
        type=int,
        help='Maximum simulation-step lag accepted in async mode (default: chunk size - 1)',
    )
    parser.add_argument(
        '--intra_chunk_mode',
        choices=['raw', 'interpolation', 'fitting'],
        help='Override intra-chunk processing mode (default: raw)',
    )
    parser.add_argument(
        '--intra_chunk_sample_ratio',
        type=_sample_ratio,
        default=1.0,
        help='Smoothed action count relative to the raw chunk (default: 1.0)',
    )
    parser.add_argument(
        '--inter_chunk_mode',
        choices=['search_action', 'smooth_velocity', 'min_jerk', 'sync'],
        help='Override inter-chunk bridging mode (default: sync)',
    )
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max_episode_steps', type=int)
    parser.add_argument('--episode_timeout', type=float, default=1800.0)
    parser.add_argument('--stall_timeout', type=float, default=120.0)
    parser.add_argument('--progress_interval', type=float, default=30.0)
    parser.add_argument('--output_dir', default='data/robocasa_eval')
    parser.add_argument(
        '--record',
        action='store_true',
        help='Save each evaluation episode as a LeRobot dataset episode',
    )
    parser.add_argument(
        '--record_dir',
        default='data/robocasa_eval/lerobot',
        help='LeRobot dataset directory relative to the project root',
    )
    parser.add_argument('--record_fps', type=int, default=20)
    parser.add_argument('--no_video', action='store_true')
    parser.add_argument('--video_fps', type=int, default=20)
    parser.add_argument('--video_layout', choices=['grid', 'single'], default='grid')
    parser.add_argument('--run_id')
    parser.add_argument(
        '--worker_episodes',
        type=int,
        default=100,
        help='Episodes per isolated RoboCasa worker process (default: 100)',
    )
    parser.add_argument(
        '--max_native_restarts',
        type=int,
        default=3,
        help='Retries after repeated native crashes at one checkpoint (default: 3)',
    )
    parser.add_argument(
        '--no_process_isolation',
        action='store_true',
        help='Run RoboCasa in the main process without native-crash recovery',
    )
    parser.add_argument('--_worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--_worker_env_name', help=argparse.SUPPRESS)
    parser.add_argument('--_record_date', help=argparse.SUPPRESS)
    parser.add_argument('--_worker_index', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--_episode_start', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--_episode_end', type=int, help=argparse.SUPPRESS)
    parser.add_argument('--server_ip', default='127.0.0.1')
    parser.add_argument('--server_port', type=int, default=5566)
    parser.add_argument('--server_wait_timeout', type=float, default=30.0)
    parser.add_argument(
        '--server_reconnect_interval',
        type=float,
        default=10.0,
        help='Seconds between worker restarts while the VLA server is unavailable',
    )
    parser.add_argument(
        '--server_reconnect_timeout',
        type=float,
        default=0.0,
        help='Stop waiting after this many seconds; 0 waits indefinitely',
    )
    parser.add_argument('--infer_timeout_ms', type=int, default=2000)
    parser.add_argument('--visualize', action='store_true')
    parser.add_argument('--visualize_port', type=int, default=8765)
    parser.add_argument('--preprocess', choices=['none', 'resize'], default='none')
    parser.add_argument('--mujoco_gl', choices=['egl', 'osmesa', 'glfw'])
    parser.add_argument('--user_conf')
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
