"""Shared worker supervision for simulation backends."""

import copy
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def configure_pipeline(config, args):
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
