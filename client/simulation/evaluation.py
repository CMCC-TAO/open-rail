"""Shared CLI, device assignment, and evaluation lifecycle."""

import argparse
import copy
import json
import os
import re
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np


SERVER_UNAVAILABLE_EXIT_CODE = 75


class ServerUnavailableError(RuntimeError):
    pass


def get_simulation_config():
    from conf.client_conf import get_client_config

    config = get_client_config()
    record = config.record.lerobot
    record.codebase_version = 'v2.1'
    record.image_feature_keys = {
        'head': 'observation.images.head',
        'hand_left': 'observation.images.left',
        'hand_right': 'observation.images.right',
    }
    for key in ('cam.head', 'cam.hand_left', 'cam.hand_right'):
        record[key].encode.codec = 'h264'
    return config


def sample_ratio(value):
    ratio = float(value)
    if ratio < 1.0:
        raise argparse.ArgumentTypeError('sample ratio must be at least 1.0')
    return ratio


def wait_for_server(client, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.is_connected:
            return
        time.sleep(0.1)
    raise ServerUnavailableError(
        f'VLA server is not responding at {client.client_addr}'
    )


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def save_stats(output_dir, metadata, episodes):
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


def episode_bounds(args):
    episode_start = getattr(args, '_episode_start', None)
    episode_end = getattr(args, '_episode_end', None)
    start = 0 if episode_start is None else episode_start
    end = args.n_episodes if episode_end is None else episode_end
    return start, end


def worker_ranges(n_episodes, n_envs):
    worker_count = min(n_episodes, n_envs)
    return [
        (index * n_episodes // worker_count, (index + 1) * n_episodes // worker_count)
        for index in range(worker_count)
    ]


def save_suite_stats(output_dir, metadata, tasks):
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
    atomic_json(path, stats)
    return path, stats


def configure_recording_for_robot(config, robot):
    record_config = config.record.lerobot
    record_config.robot_type = robot.DATASET_ROBOT_TYPE
    record_config.state_shape = int(robot.current_state.size)
    record_config.action_shape = int(robot.action_dim)
    record_config.image_feature_keys = robot.DATASET_CAMERA_KEYS
    record_config.instruction_key = robot.DATASET_INSTRUCTION_KEY
    record_config.strict_shapes = True
    record_config.state_action_dtype = 'float64'


def build_client(config, robot, transport):
    """Assemble the common policy pipeline; resource ownership remains with the caller."""
    from client.core.inter_chunk_fuser import InterChunkFuser
    from client.core.intra_chunk_smoother import IntraChunkSmoother
    from client.core.realtime_data_manager import RealtimeDataManager
    from client.core.task_language_manager import TaskLanguageManager
    from client.simulation.vla_client import VLAClientAsync

    config.rdm.action_layout = robot.config.action_layout
    config.intra_chunk.action_layout = robot.config.action_layout
    configure_recording_for_robot(config, robot)
    return VLAClientAsync(
        config=config,
        realtime_data_manager=RealtimeDataManager(config.rdm, simulation_mode=True),
        inter_chunk_fuser=InterChunkFuser(config.inter_chunk, simulation_mode=True),
        intra_chunk_smoother=IntraChunkSmoother(config.intra_chunk, simulation_mode=True),
        task_language_manager=TaskLanguageManager(config.language),
        vla_zmq_client=transport,
        robot=robot,
    )


def recording_date(run_id):
    candidate = str(run_id)[:8]
    try:
        time.strptime(candidate, '%Y%m%d')
    except ValueError:
        return time.strftime('%Y%m%d')
    return candidate


def resume_episodes(task_output, metadata, episode_start=0):
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


def start_episode(client, robot, visualize, record=False):
    language = robot.get_task_description()
    if not language:
        raise RuntimeError('Simulation backend did not provide a task description')
    client.task_language_manager.currt_language_instruction = language
    if record:
        client.data_record_manager.start_recording()
    client.start_observe()
    client.start_inference()
    client.start_control()
    if visualize:
        client.start_visualize()


def reset_episode(client, robot, visualize, record=False):
    client.pause()
    client.realtime_data_manager.cancel_waiters()
    client.realtime_data_manager.clear()
    client.reset()
    robot.reset()
    start_episode(client, robot, visualize, record)


def discard_recording_episode(recording_path, episode_index):
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


def reconcile_recording_progress(manager, recording_path, expected_episodes):
    recorded_episodes = int(manager.shared_data.episode_index.value)
    if recorded_episodes == expected_episodes:
        return
    if recorded_episodes != expected_episodes + 1:
        raise RuntimeError(
            'Cannot resume recording: '
            f'dataset has {recorded_episodes} episodes, stats have {expected_episodes}'
        )
    info = discard_recording_episode(recording_path, expected_episodes)
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


def wait_for_episode(client, episode, timeout, stall_timeout, progress_interval):
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
                f'Simulation evaluation pipeline failed during episode {episode + 1}'
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
                f'Simulation episode {episode + 1} stalled for {stall_timeout:g}s '
                f'at simulation step {current_step}; check the client and model-server logs'
            )
        if now >= next_report_at:
            print(
                f'Episode {episode + 1} running: simulation_step={current_step}',
                flush=True,
            )
            next_report_at = now + progress_interval


def worker_gpu(gpu, worker_index=None):
    if not gpu:
        return None
    if not re.fullmatch(r'\d+(,\d+)*', gpu):
        raise ValueError('GPU must contain comma-separated indices')
    devices = gpu.split(',')
    return devices[(worker_index or 0) % len(devices)]


def configure_mujoco_gpu(gpu, worker_index=None):
    device = worker_gpu(gpu, worker_index)
    if device is not None:
        os.environ['CUDA_VISIBLE_DEVICES'] = device
        os.environ['MUJOCO_EGL_DEVICE_ID'] = device
    return device


def build_parser(description=None):
    parser = argparse.ArgumentParser(description=description)
    task_selection = parser.add_mutually_exclusive_group(required=True)
    task_selection.add_argument('--env_name')
    task_selection.add_argument(
        '--task_suite',
        help='Task suite name or task list',
    )
    parser.add_argument('--n_episodes', type=int, default=50)
    parser.add_argument('--n_envs', type=int, default=10)
    parser.add_argument('--gpu', help='GPU index or comma-separated GPU indices, assigned per worker')
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
        type=sample_ratio,
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
    parser.add_argument('--output_dir', default='data/simulation_eval')
    parser.add_argument(
        '--record',
        action='store_true',
        help='Save each evaluation episode as a LeRobot dataset episode',
    )
    parser.add_argument(
        '--record_dir',
        default='data/simulation_eval/lerobot',
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
        help='Episodes per isolated simulation worker process (default: 100)',
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
        help='Run simulation in the main process without native-crash recovery',
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
    parser.add_argument('--user_conf')
    parser.add_argument('--io_profile', help='Override the model layout: YAML path or YAML path#profile')
    parser.add_argument('--embodiment_tag', help='Simulation robot name, shared with run_server.py')
    return parser


class EvaluationRunner:
    def __init__(self, api, label):
        self.api = api
        self.label = label

    def _run_supervised_task(self, args, env_name, run_id):
        record_date = args._record_date or self.api._recording_date(run_id)
        consecutive_native_crashes = 0
        crash_progress = None
        server_unavailable_since = None
        while True:
            cancel_event = getattr(args, "_cancel_event", None)
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Parallel evaluation cancelled after another worker failed")
            stats = self.api._read_supervised_stats(args, env_name, run_id)
            progress = 0 if stats is None else int(stats.get("num_episodes", 0))
            episode_start, episode_end = self.api._episode_bounds(args)
            if progress >= episode_end - episode_start:
                if getattr(args, "_defer_recording_finalize", False):
                    return stats
                return self.api._finalize_supervised_recording(args, stats)
            command = self.api._worker_command(args, env_name, run_id, record_date)
            return_code = (
                self.api._run_worker_process(command, cancel_event=cancel_event)
                if cancel_event is not None
                else self.api._run_worker_process(command)
            )
            stats = self.api._read_supervised_stats(args, env_name, run_id)
            new_progress = 0 if stats is None else int(stats.get("num_episodes", 0))
            if return_code == 0:
                if new_progress <= progress:
                    raise RuntimeError(f"{self.label} worker exited without recording progress")
                consecutive_native_crashes = 0
                crash_progress = None
                server_unavailable_since = None
                continue
            if return_code == self.api.SERVER_UNAVAILABLE_EXIT_CODE:
                now = time.monotonic()
                if server_unavailable_since is None:
                    server_unavailable_since = now
                reconnect_timeout = getattr(args, "server_reconnect_timeout", 0.0)
                if reconnect_timeout > 0 and now - server_unavailable_since >= reconnect_timeout:
                    raise self.api.ServerUnavailableError(
                        f"VLA server remained unavailable for {reconnect_timeout:g}s; "
                        f"last completed episode: {new_progress}"
                    )
                reconnect_interval = getattr(args, "server_reconnect_interval", 10.0)
                print(
                    "VLA server is unavailable; preserving completed episodes and "
                    f"retrying in {reconnect_interval:g}s from episode {new_progress + 1}",
                    flush=True,
                )
                cancel_event.wait(reconnect_interval) if cancel_event is not None else time.sleep(
                    reconnect_interval
                )
                continue
            native_signals = {
                -signal.SIGSEGV,
                -signal.SIGABRT,
                -signal.SIGBUS,
                -signal.SIGILL,
            }
            if return_code in native_signals:
                if new_progress == crash_progress:
                    consecutive_native_crashes += 1
                else:
                    consecutive_native_crashes = 1
                    crash_progress = new_progress
                if consecutive_native_crashes > args.max_native_restarts:
                    raise RuntimeError(
                        f"{self.label} worker repeatedly crashed at episode {new_progress + 1} "
                        f"with signal {-return_code}"
                    )
                print(
                    f"{self.label} worker crashed with signal {-return_code}; "
                    f"resuming from episode {new_progress + 1} "
                    f"({consecutive_native_crashes}/{args.max_native_restarts})",
                    flush=True,
                )
                time.sleep(1.0)
                continue
            raise RuntimeError(f"{self.label} worker exited with code {return_code}")

    def _run_parallel_task(self, args, env_name, run_id):
        ranges = self.api._worker_ranges(args.n_episodes, args.n_envs)
        worker_args = []
        cancel_event = threading.Event()
        for worker_index, (episode_start, episode_end) in enumerate(ranges):
            shard_args = copy.copy(args)
            shard_args.run_id = run_id
            shard_args._worker_index = worker_index
            shard_args._episode_start = episode_start
            shard_args._episode_end = episode_end
            shard_args._defer_recording_finalize = args.record
            shard_args._cancel_event = cancel_event
            worker_args.append(shard_args)

        results = []
        with ThreadPoolExecutor(max_workers=len(worker_args)) as executor:
            futures = {
                executor.submit(
                    self.api._run_supervised_task, shard_args, env_name, run_id
                ): shard_args
                for shard_args in worker_args
            }
            try:
                for future in as_completed(futures):
                    results.append(future.result())
            except BaseException:
                cancel_event.set()
                for future in futures:
                    future.cancel()
                raise

        episodes = sorted(
            (episode for stats in results for episode in stats["episodes"]),
            key=lambda episode: episode["episode"],
        )
        expected = list(range(args.n_episodes))
        actual = [int(episode["episode"]) for episode in episodes]
        if actual != expected:
            raise RuntimeError(f"Parallel {self.label} workers returned episode indices {actual}")

        metadata = {
            key: value
            for key, value in results[0].items()
            if key
            not in {
                "num_episodes",
                "success_rate",
                "episodes",
                "worker_index",
                "episode_start",
                "episode_end",
                "lerobot_dataset_path",
                "lerobot_dataset_paths",
            }
        }
        metadata["n_envs"] = args.n_envs
        if args.record:
            metadata["lerobot_dataset_paths"] = self.api._merge_parallel_recordings(results)
        task_output = self.api._task_stats_path(args, env_name).parent
        stats_path, stats = self.api._save_stats(task_output, metadata, episodes)
        print(f"Saved merged evaluation statistics to {stats_path}", flush=True)
        return stats


def configure_pipeline(config, args, platform=None):
    tag = getattr(args, 'embodiment_tag', None) or config.vla_zmq.get('embodiment_tag', '')
    profile = getattr(args, 'io_profile', None) or config.vla_zmq.get('io_profile', '')
    if tag:
        from conf.embodiments_conf import select_evaluation_embodiment

        select_evaluation_embodiment(config, tag, platform)
    if profile:
        from client.simulation.io_adapter import resolve_profile_path

        config.vla_zmq.io_profile = resolve_profile_path(profile)
    config.rdm.mode = args.mode
    config.rdm.skip_initial_frames = 0
    config.rdm.action_consume_mode = "sequential"
    config.rdm.latency_compensation = False
    config.rdm.action_replenish_threshold = (
        (
            args.async_replenish_threshold
            if args.async_replenish_threshold is not None
            else max(1, args.n_action_steps // 2)
        )
        if args.mode == "async"
        else 0
    )
    config.rdm.max_async_observation_lag_steps = (
        args.max_async_observation_lag_steps
        if args.max_async_observation_lag_steps is not None
        else max(1, args.n_action_steps - 1)
    )
    config.intra_chunk.intra_chunk_mode = args.intra_chunk_mode or "raw"
    config.intra_chunk.output_sample_ratio = (
        1.0 if config.intra_chunk.intra_chunk_mode == "raw" else args.intra_chunk_sample_ratio
    )
    config.inter_chunk.inter_chunk_mode = args.inter_chunk_mode or "sync"
    config.controller.gripper_offset = 0
    config.controller.period = getattr(args, "control_period_ms", 1.0)
    config.controller.action_steps = args.n_action_steps
    config.vision.preprocess.method = args.preprocess


def run_isolated_worker(command, phase_path=None, cancel_event=None, startup_timeout=None):
    import json
    import os
    from pathlib import Path
    import subprocess
    import psutil

    environment = os.environ.copy()
    environment.setdefault("PYTHONFAULTHANDLER", "1")
    started = time.time()
    process = subprocess.Popen(command, start_new_session=True, env=environment)
    timed_out = False
    seen_phase = False
    owned = {}
    try:
        while process.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                timed_out = True
                break
            try:
                for child in psutil.Process(process.pid).children(recursive=True):
                    owned[(child.pid, child.create_time())] = child
            except psutil.NoSuchProcess:
                pass
            if startup_timeout and not seen_phase and time.time() - started > startup_timeout:
                print("Simulation worker startup timed out", flush=True)
                timed_out = True
                break
            if phase_path and Path(phase_path).exists():
                try:
                    phase = json.loads(Path(phase_path).read_text())
                    seen_phase = seen_phase or phase["started"] >= started
                    if phase["started"] >= started and time.time() > phase["deadline"]:
                        print(f"Simulation worker timed out during {phase['stage']}", flush=True)
                        timed_out = True
                        break
                except (OSError, ValueError, KeyError):
                    pass
            time.sleep(0.2)
    finally:
        try:
            parent = psutil.Process(process.pid)
            targets = [parent] + parent.children(recursive=True) + list(owned.values())
        except psutil.NoSuchProcess:
            targets = list(owned.values())
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        for target in targets:
            try:
                target.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(targets, timeout=3)
        for target in alive:
            try:
                target.kill()
            except psutil.NoSuchProcess:
                pass
        process.wait()
    return 124 if timed_out else process.returncode
