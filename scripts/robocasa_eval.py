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
from client.core.vla_client import VLAClientAsync
from client.core.zmq_client import ZMQClient
from client.utils.util import apply_user_config, load_user_config
from conf.client_conf import get_client_config
from conf.robots_conf import RobotType


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
    raise RuntimeError(f'VLA server is not responding at {client.client_addr}')


def _save_stats(output_dir, metadata, episodes):
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = {
        **metadata,
        'num_episodes': len(episodes),
        'success_rate': float(np.mean([item['success'] for item in episodes])) if episodes else 0.0,
        'episodes': episodes,
    }
    path = output_dir / 'stats.json'
    with path.open('w', encoding='utf-8') as file:
        json.dump(stats, file, indent=2)
    return path, stats


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
    with path.open('w', encoding='utf-8') as file:
        json.dump(stats, file, indent=2)
    return path, stats


def _build_client(config, server_wait_timeout):
    zmq_client = ZMQClient(config.vla_zmq)
    robot = None
    try:
        _wait_for_server(zmq_client, server_wait_timeout)
        from client.robots.robocasa.body_robot import RobotBody

        robot = RobotBody(config.robots.robocasa)
        config.rdm.action_layout = config.robots.robocasa.action_layout
        config.intra_chunk.action_layout = config.robots.robocasa.action_layout
        config.record.lerobot.robot_type = RobotType.ROBOCASA.value
        config.record.lerobot.state_shape = int(robot.current_state.size)
        config.record.lerobot.action_shape = int(robot.action_dim)
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


def _start_episode(client, robot, visualize):
    language = robot.get_task_description()
    if not language:
        raise RuntimeError('RoboCasa did not provide a task description')
    client.task_language_manager.currt_language_instruction = language
    client.start_observe()
    client.start_inference()
    client.start_control()
    if visualize:
        client.start_visualize()


def _reset_episode(client, robot, visualize):
    client.pause()
    client.realtime_data_manager.cancel_waiters()
    client.realtime_data_manager.clear()
    client.reset()
    robot.reset()
    _start_episode(client, robot, visualize)


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

    config.vla_zmq.ip = args.server_ip
    config.vla_zmq.port = str(args.server_port)
    config.vla_zmq.infer_timeout = args.infer_timeout_ms
    config.robots.type = RobotType.ROBOCASA
    config.robots.robocasa.env_name = env_name
    config.robots.robocasa.split = args.split
    config.robots.robocasa.seed = args.seed
    config.robots.robocasa.max_episode_steps = _task_horizon(env_name, args.max_episode_steps)
    task_name = env_name.split('/')[-1]
    task_output = Path(args.output_dir) / 'evals' / args.split / task_name
    config.robots.robocasa.video_dir = '' if args.no_video else str(task_output / 'videos' / run_id)
    config.robots.robocasa.video_fps = args.video_fps
    config.robots.robocasa.video_layout = args.video_layout
    config.visualize.port = args.visualize_port

    config.rdm.mode = args.mode
    config.rdm.skip_initial_frames = 0
    config.rdm.action_consume_mode = 'sequential'
    config.rdm.latency_compensation = False
    config.rdm.action_replenish_threshold = (
        args.async_replenish_threshold
        if args.async_replenish_threshold is not None
        else max(1, args.n_action_steps // 2)
    ) if args.mode == 'async' else 0
    config.rdm.max_async_observation_lag_steps = (
        args.max_async_observation_lag_steps
        if args.max_async_observation_lag_steps is not None
        else max(1, args.n_action_steps - 1)
    )
    config.intra_chunk.intra_chunk_mode = args.intra_chunk_mode or 'raw'
    config.intra_chunk.output_sample_ratio = (
        1.0
        if config.intra_chunk.intra_chunk_mode == 'raw'
        else args.intra_chunk_sample_ratio
    )
    config.inter_chunk.inter_chunk_mode = args.inter_chunk_mode or 'sync'
    if args.mode == 'async' and config.inter_chunk.inter_chunk_mode == 'min_jerk':
        logging.warning(
            'RoboCasa min_jerk smooths delta/velocity command values at every async '
            'replan; compare async raw+sync first when measuring async-mode accuracy.'
        )
    config.controller.gripper_offset = 0
    config.controller.period = 1.0
    config.controller.action_steps = args.n_action_steps
    config.vision.preprocess.method = args.preprocess

    client, robot = _build_client(config, args.server_wait_timeout)
    metadata = {
        'env_name': env_name,
        'split': args.split,
        'seed': args.seed,
        'run_id': run_id,
        'mode': args.mode,
        'n_action_steps': args.n_action_steps,
        'intra_chunk_mode': config.intra_chunk.intra_chunk_mode,
        'intra_chunk_sample_ratio': config.intra_chunk.output_sample_ratio,
        'inter_chunk_mode': config.inter_chunk.inter_chunk_mode,
        'async_replenish_threshold': config.rdm.action_replenish_threshold,
        'max_async_observation_lag_steps': config.rdm.max_async_observation_lag_steps,
    }
    episodes = []
    try:
        _start_episode(client, robot, args.visualize)
        print(
            f'RoboCasa client started; waiting for inference from {config.vla_zmq.ip}:'
            f'{config.vla_zmq.port} (timeout={config.vla_zmq.infer_timeout} ms, '
            f'mode={config.rdm.mode}, intra={config.intra_chunk.intra_chunk_mode}, '
            f'inter={config.inter_chunk.inter_chunk_mode}, '
            f'replenish={config.rdm.action_replenish_threshold}, '
            f'max_lag={config.rdm.max_async_observation_lag_steps})',
            flush=True,
        )
        for episode in range(args.n_episodes):
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
            episodes.append(result)
            _save_stats(task_output, metadata, episodes)
            success_rate = float(np.mean([item['success'] for item in episodes]))
            print(
                f"Episode {episode + 1}/{args.n_episodes}: success={result['success']}, "
                f"steps={result['steps']}, cumulative_success_rate={success_rate:.3f}",
                flush=True,
            )
            if episode + 1 < args.n_episodes:
                _reset_episode(client, robot, args.visualize)
    finally:
        client.close()
        robot.close()

    stats_path, stats = _save_stats(task_output, metadata, episodes)
    print(f'Saved evaluation statistics to {stats_path}', flush=True)
    return stats


def run(args):
    run_id = args.run_id or time.strftime('%Y%m%d_%H%M%S')
    if args.env_name:
        return _run_task(args, args.env_name, run_id)

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
            stats = _run_task(args, env_name, run_id)
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
    parser.add_argument('--n_action_steps', type=int, default=16)
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
    parser.add_argument('--no_video', action='store_true')
    parser.add_argument('--video_fps', type=int, default=20)
    parser.add_argument('--video_layout', choices=['grid', 'single'], default='grid')
    parser.add_argument('--run_id')
    parser.add_argument('--server_ip', default='127.0.0.1')
    parser.add_argument('--server_port', type=int, default=5566)
    parser.add_argument('--server_wait_timeout', type=float, default=30.0)
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
        args.n_action_steps,
        args.infer_timeout_ms,
        args.episode_timeout,
        args.stall_timeout,
        args.progress_interval,
    )
    if any(value <= 0 for value in positive_args):
        raise ValueError('episode counts, action counts, and timeouts must be positive')
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
    os.chdir(PROJECT_ROOT)
    try:
        from conf.logging_conf import setup_logging

        setup_logging('robocasa_eval.log', __name__)
    except ImportError:
        logging.basicConfig(level=logging.INFO)
    run(args)


if __name__ == '__main__':
    main()
