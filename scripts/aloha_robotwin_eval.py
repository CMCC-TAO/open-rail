"""Evaluate RoboTwin/Aloha through the shared simulation pipeline."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import robocasa_eval as casa
from client.simulation.evaluation import (
    EvaluationRunner,
    configure_pipeline as configure_shared_pipeline,
)
from client.simulation import recording_exports
from client.robots.aloha_robotwin.body_robot import RobotBody
from client.robots.aloha_robotwin.environment import (
    _prepare_robotwin,
    select_episode,
    validate_name,
)
from conf.robots_conf import RobotType

SERVER_UNAVAILABLE_EXIT_CODE = casa.SERVER_UNAVAILABLE_EXIT_CODE
ServerUnavailableError = casa.ServerUnavailableError
_episode_bounds = casa._episode_bounds
_worker_ranges = casa._worker_ranges
_recording_date = casa._recording_date
_merge_parallel_recordings = recording_exports._merge_parallel_recordings
_save_stats = casa._save_stats


def build_parser():
    parser = casa.build_parser()
    parser.description = __doc__
    parser.set_defaults(
        n_envs=1,
        n_action_steps=50,
        seed=0,
        output_dir="data/aloha_robotwin_eval",
        record_dir="data/aloha_robotwin_eval/lerobot",
    )
    for existing, alias in (("--env_name", "--task_name"), ("--task_suite", "--tasks")):
        action = parser._option_string_actions[existing]
        action.option_strings.append(alias)
        parser._option_string_actions[alias] = action
    parser._option_string_actions["--tasks"].help = "Comma-separated tasks or a YAML task-list file"
    for option in ("--split", "--mujoco_gl"):
        action = parser._option_string_actions.pop(option)
        parser._remove_action(action)
        for group in parser._action_groups:
            if action in group._group_actions:
                group._group_actions.remove(action)
    parser.set_defaults(split="unseen")
    parser.add_argument("--robotwin_root", default=str(PROJECT_ROOT.parent / "RoboTwin"))
    parser.add_argument("--task_config", default="demo_clean")
    parser.add_argument("--instruction_type", choices=["seen", "unseen"], default="unseen")
    parser.add_argument("--instruction")
    parser.add_argument("--no_expert_check", action="store_true")
    parser.add_argument("--gpu", help="GPU index or comma-separated GPU indices")
    parser.add_argument("--control_period_ms", type=float, default=1.0)
    parser.add_argument("--max_transition_steps", type=int, default=5)
    parser.add_argument("--max_seed_attempts", type=int, default=100)
    parser.add_argument("--seed_stride", type=int, default=10000)
    parser.add_argument("--seed_selection_timeout", type=float, default=300)
    parser.add_argument(
        "--interpolation_sample_ratio",
        dest="intra_chunk_sample_ratio",
        type=casa._sample_ratio,
        default=argparse.SUPPRESS,
    )
    parser.add_argument("--verbose_dependencies", action="store_true")
    return parser


def configure_pipeline(config, args):
    configure_shared_pipeline(config, args)
    config.intra_chunk.preserve_input_timestamps = True
    if config.intra_chunk.intra_chunk_mode != "interpolation":
        config.intra_chunk.output_sample_ratio = 1.0
    config.inter_chunk.max_transition_steps = args.max_transition_steps
    return config


def validate_args(args):
    for name in (
        "n_episodes",
        "n_envs",
        "n_action_steps",
        "worker_episodes",
        "video_fps",
        "record_fps",
        "episode_timeout",
        "stall_timeout",
        "progress_interval",
        "infer_timeout_ms",
        "server_wait_timeout",
        "server_reconnect_interval",
        "control_period_ms",
        "max_seed_attempts",
        "seed_stride",
        "seed_selection_timeout",
    ):
        if not math.isfinite(getattr(args, name)) or getattr(args, name) <= 0:
            raise ValueError(f"{name} must be positive")
    if args.max_seed_attempts > args.seed_stride:
        raise ValueError("max_seed_attempts must not exceed seed_stride")
    if (
        args.seed < 0
        or args.max_transition_steps < 0
        or args.max_native_restarts < 0
        or args.server_reconnect_timeout < 0
    ):
        raise ValueError(
            "seed, transition steps, retries and reconnect timeout must be non-negative"
        )
    if not 1 <= args.server_port <= 65535:
        raise ValueError("server_port must be in [1, 65535]")
    if args.max_episode_steps is not None and args.max_episode_steps <= 0:
        raise ValueError("max_episode_steps must be positive")
    if (
        args.async_replenish_threshold is not None
        and not 0 <= args.async_replenish_threshold < args.n_action_steps
    ):
        raise ValueError("async_replenish_threshold must be in [0, n_action_steps)")
    if (
        args.max_async_observation_lag_steps is not None
        and args.max_async_observation_lag_steps < 0
    ):
        raise ValueError("max_async_observation_lag_steps must be non-negative")
    if args.no_expert_check and not (args.instruction and args.instruction.strip()):
        raise ValueError("--no_expert_check requires --instruction")
    if args.n_envs > 1 and (args.no_process_isolation or args.visualize):
        raise ValueError("Parallel evaluation requires isolation and disables live visualization")
    if args.record and (Path(args.record_dir).is_absolute() or ".." in Path(args.record_dir).parts):
        raise ValueError("record_dir must be relative to the project root without traversal")
    if args.no_process_isolation and args.seed_selection_timeout:
        logging.warning("Hard environment setup deadlines require process isolation")
    if not math.isfinite(args.intra_chunk_sample_ratio) or args.intra_chunk_sample_ratio < 1:
        raise ValueError("intra_chunk_sample_ratio must be finite and at least 1")
    if not math.isfinite(args.server_reconnect_timeout):
        raise ValueError("server_reconnect_timeout must be finite")
    if args.run_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.run_id):
        raise ValueError("Invalid run_id")
    if args.user_conf:
        args.user_conf = str(Path(args.user_conf).expanduser().resolve())
        if not Path(args.user_conf).is_file():
            raise ValueError("User configuration file is unavailable")
    if args.task_suite:
        names = _task_names(args.task_suite)
        args.task_suite = ",".join(names)
    validate_name(args.task_config)
    if args.env_name:
        validate_name(args.env_name)
    if args.gpu is not None:
        if not re.fullmatch(r"\d+(,\d+)*", args.gpu):
            raise ValueError("gpu must contain comma-separated GPU indices")
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu
    args.robotwin_root = str(Path(args.robotwin_root).expanduser().resolve())
    args.output_dir = str(Path(args.output_dir).expanduser().resolve())
    args.split = args.instruction_type


def _identity(args, task_name):
    names = (
        "task_config",
        "instruction_type",
        "instruction",
        "no_expert_check",
        "seed",
        "seed_stride",
        "max_seed_attempts",
        "n_envs",
        "n_action_steps",
        "mode",
        "intra_chunk_mode",
        "intra_chunk_sample_ratio",
        "inter_chunk_mode",
        "max_transition_steps",
        "record",
        "record_fps",
        "record_dir",
        "n_episodes",
        "max_episode_steps",
        "preprocess",
        "server_ip",
        "server_port",
        "robotwin_root",
    )
    values = {key: getattr(args, key) for key in names}
    values["task_name"] = task_name
    if args.user_conf:
        values["user_conf"] = Path(args.user_conf).read_text()
    for key in (
        "async_replenish_threshold",
        "max_async_observation_lag_steps",
        "control_period_ms",
    ):
        values[key] = getattr(args, key)
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def _task_stats_path(args, env_name):
    folder = Path(args.output_dir) / "evals" / args.split / env_name / args.run_id
    if args._worker_index is not None:
        folder = folder / "workers" / f"env_{args._worker_index:02d}"
    return folder / "stats.json"


def _finalize_supervised_recording(args, stats):
    if not args.record or "lerobot_dataset_paths" in stats:
        return stats
    path = stats.get("lerobot_dataset_path")
    if not path:
        raise RuntimeError("Completed recording has no LeRobot dataset path")
    metadata = {
        key: value
        for key, value in stats.items()
        if key not in ("episodes", "num_episodes", "success_rate", "lerobot_dataset_path")
    }
    metadata["lerobot_dataset_paths"] = recording_exports._partition_recording_by_success(
        path, stats["episodes"]
    )
    return _save_stats(
        _task_stats_path(args, stats["env_name"]).parent, metadata, stats["episodes"]
    )[1]


def _read_supervised_stats(args, env_name, run_id):
    path = _task_stats_path(args, env_name)
    if not path.is_file():
        return None
    stats = json.loads(path.read_text())
    if stats.get("run_id") != run_id or stats.get("env_name") != env_name:
        raise ValueError("Saved evaluation identity differs from requested run")
    if stats and stats.get("config_identity") != _identity(args, env_name):
        raise ValueError("Resume configuration differs from the saved evaluation")
    return stats


def _run_worker_process(command, cancel_event=None):
    from client.simulation.evaluation import run_isolated_worker

    args = build_parser().parse_args(command[3:])
    args.split = args.instruction_type
    phase = _task_stats_path(args, args._worker_env_name).parent / "phase.json"
    return run_isolated_worker(
        command, phase, cancel_event, args.seed_selection_timeout + args.server_wait_timeout + 120
    )


def _phase(task_output, stage, timeout):
    now = time.time()
    casa._atomic_json(
        task_output / "phase.json", {"stage": stage, "started": now, "deadline": now + timeout}
    )


def _worker_command(args, env_name, run_id, record_date):
    command = [
        sys.executable,
        "-u",
        str(Path(__file__).resolve()),
        *sys.argv[1:],
        "--_worker",
        "--_worker_env_name",
        env_name,
        "--_record_date",
        record_date,
        "--run_id",
        run_id,
        "--output_dir",
        args.output_dir,
        "--robotwin_root",
        args.robotwin_root,
    ]
    if args.user_conf:
        command += ["--user_conf", args.user_conf]
    if args.task_suite:
        command += ["--task_suite", args.task_suite]
    if args.gpu and args._worker_index is not None:
        devices = args.gpu.split(",")
        command += ["--gpu", devices[args._worker_index % len(devices)]]
    if args._worker_index is not None:
        command += [
            "--_worker_index",
            str(args._worker_index),
            "--_episode_start",
            str(args._episode_start),
            "--_episode_end",
            str(args._episode_end),
        ]
    return command


def _run_supervised_task(args, env_name, run_id):
    return EvaluationRunner(sys.modules[__name__], "RoboTwin")._run_supervised_task(
        args, env_name, run_id
    )


def _run_parallel_task(args, env_name, run_id):
    return EvaluationRunner(sys.modules[__name__], "RoboTwin")._run_parallel_task(
        args, env_name, run_id
    )


def _run_task(args, task_name, run_id):
    validate_name(task_name)
    task_output = _task_stats_path(args, task_name).parent
    identity = _identity(args, task_name)
    task_output.mkdir(parents=True, exist_ok=True)
    identity_path = task_output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != {
        "run_id": run_id,
        "config": identity,
    }:
        raise ValueError("Existing run directory belongs to a different evaluation")
    casa._atomic_json(identity_path, {"run_id": run_id, "config": identity})
    metadata = {
        "env_name": task_name,
        "task_name": task_name,
        "platform": "robotwin",
        "split": args.split,
        "seed": args.seed,
        "run_id": run_id,
        "n_envs": args.n_envs,
        "config_identity": identity,
        "task_config": args.task_config,
        "instruction_type": args.instruction_type,
        "seed_stride": args.seed_stride,
        "expert_check": not args.no_expert_check,
    }
    start, end = _episode_bounds(args)
    if args._worker_index is not None:
        metadata.update(worker_index=args._worker_index, episode_start=start, episode_end=end)
    episodes = casa._resume_episodes(task_output, metadata, start)
    start += len(episodes)
    if start >= end:
        return json.loads((task_output / "stats.json").read_text())
    if args._worker:
        end = min(end, start + args.worker_episodes)
    config = casa.get_client_config()
    if args.user_conf:
        config = casa.apply_user_config(config, casa.load_user_config(args.user_conf))
    configure_pipeline(config, args)
    config.robots.type = RobotType.ALOHA_ROBOTWIN
    config.vla_zmq.ip, config.vla_zmq.port = args.server_ip, str(args.server_port)
    config.vla_zmq.infer_timeout = args.infer_timeout_ms
    config.visualize.port = args.visualize_port
    config.record.switch = args.record
    config.record.save_dir = args.record_dir
    config.record.dataset_date = args._record_date or _recording_date(run_id)
    config.record.lerobot.fps = args.record_fps
    cfg = config.robots.aloha_robotwin
    cfg.preview_worker_index = getattr(args, '_worker_index', None)
    cfg.task_name = task_name
    cfg.video_dir = "" if args.no_video else str(task_output / "videos" / run_id)
    cfg.video_fps, cfg.video_layout = args.video_fps, args.video_layout
    cfg.video_title = "ROBOTWIN EVALUATION"
    metadata.update(
        mode=args.mode,
        n_action_steps=args.n_action_steps,
        intra_chunk_mode=config.intra_chunk.intra_chunk_mode,
        intra_chunk_sample_ratio=config.intra_chunk.output_sample_ratio,
        inter_chunk_mode=config.inter_chunk.inter_chunk_mode,
        max_transition_steps=args.max_transition_steps,
        async_replenish_threshold=config.rdm.action_replenish_threshold,
        max_async_observation_lag_steps=config.rdm.max_async_observation_lag_steps,
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
    )
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="robotwin_sim")
    robot = client = env = zmq = None
    recording_path = None
    previous_cwd = Path.cwd()
    try:
        zmq = casa.ZMQClient(config.vla_zmq)
        casa._wait_for_server(zmq, args.server_wait_timeout)
        _phase(task_output, "environment setup", args.seed_selection_timeout)
        os.chdir(args.robotwin_root)
        env_args, env_class = _prepare_robotwin(
            Path(args.robotwin_root), task_name, args.task_config
        )
        for episode in range(start, end):
            if client is not None:
                client.pause()
                client.realtime_data_manager.clear()
                client.reset()
                robot.detach_env()
            _phase(task_output, "seed selection", args.seed_selection_timeout)
            env, instruction, seed = select_episode(
                executor,
                env_class,
                env_args,
                task_name,
                episode,
                args.seed + episode * args.seed_stride,
                args.instruction_type,
                not args.no_expert_check,
                args.instruction,
                args.max_seed_attempts,
                args.seed_selection_timeout,
                task_output / "episodes" / f"{episode:06d}.json",
            )
            if args.max_episode_steps is not None:
                env.step_lim = args.max_episode_steps
            if robot is None:
                robot = RobotBody(cfg, env, instruction, episode, seed, executor)
                config.rdm.action_layout = cfg.action_layout
                config.intra_chunk.action_layout = cfg.action_layout
                casa._configure_recording_for_robot(config, robot)
                client = casa.VLAClientAsync(
                    config=config,
                    realtime_data_manager=casa.RealtimeDataManager(config.rdm),
                    inter_chunk_fuser=casa.InterChunkFuser(config.inter_chunk),
                    intra_chunk_smoother=casa.IntraChunkSmoother(config.intra_chunk),
                    task_language_manager=casa.TaskLanguageManager(config.language),
                    vla_zmq_client=zmq,
                    robot=robot,
                )
                if args.record:
                    record_id = (
                        run_id
                        if args._worker_index is None
                        else f"{run_id}_env{args._worker_index:02d}"
                    )
                    recorder = client.data_record_manager
                    recorder.set_task(f"robotwin_{args.split}_{task_name}_{record_id}")
                    shapes = {
                        key: frame.shape
                        for key, frame in robot._to_vla_observation(
                            robot._last_obs, 0, "reset"
                        ).items()
                        if key.startswith("cam.")
                    }
                    recorder.update_camera_shape_dict(shapes)
                    recording_path = recorder.save_path
                    casa._reconcile_recording_progress(recorder, recording_path, len(episodes))
                    metadata["lerobot_dataset_path"] = recording_path
            else:
                robot.reset(env, instruction, episode, seed)
            _phase(task_output, "episode execution", args.episode_timeout + 10)
            casa._start_episode(client, robot, args.visualize, args.record)
            completed = casa._wait_for_episode(
                client, episode, args.episode_timeout, args.stall_timeout, args.progress_interval
            )
            if client.pipeline_error:
                raise RuntimeError(
                    f"RoboTwin pipeline failed at episode {episode}"
                ) from client.pipeline_error
            client.pause()
            result = robot.get_episode_result()
            video = robot.stop_video()
            if not completed or result is None:
                result = {
                    "episode": episode,
                    "seed": seed,
                    "instruction": instruction,
                    "success": False,
                    "steps": robot.get_episode_steps(),
                    "terminated": False,
                    "truncated": True,
                    "timeout": True,
                }
            result.update(video)
            if args.record:
                result["recording_episode_index"] = client.data_record_manager.stop_recording()
            episodes.append(result)
            _save_stats(task_output, metadata, episodes)
            print(
                f"Episode {episode + 1}/{args.n_episodes}: seed={seed}, success={result['success']}, steps={result['steps']}",
                flush=True,
            )
    finally:
        _phase(task_output, "cleanup", 120)
        if client is not None:
            client.close()
        elif zmq is not None:
            zmq.close()
        if robot is not None:
            robot.close()
        elif env is not None:
            executor.submit(env.close_env).result()
        executor.shutdown(wait=True)
        os.chdir(previous_cwd)
    stats = _save_stats(task_output, metadata, episodes)[1]
    return _finalize_supervised_recording(args, stats) if not args._worker else stats


def _task_names(selection):
    path = Path(selection).expanduser()
    if path.is_file():
        import yaml

        data = yaml.safe_load(path.read_text())
        names = data.get("tasks") if isinstance(data, dict) else data
    else:
        names = selection.split(",")
    if not isinstance(names, list) or not names:
        raise ValueError("Task suite must contain a nonempty task list")
    names = [validate_name(str(name).strip()) for name in names]
    if len(set(names)) != len(names):
        raise ValueError("Task suite contains duplicate tasks")
    return names


def run(args):
    args.run_id = args.run_id or time.strftime("%Y%m%d_%H%M%S")
    if args._worker:
        return _run_task(args, args._worker_env_name or args.env_name, args.run_id)
    if args.env_name:
        return (
            _run_task
            if args.no_process_isolation
            else _run_parallel_task
            if args.n_envs > 1
            else _run_supervised_task
        )(args, args.env_name, args.run_id)
    names = _task_names(args.task_suite)
    results = []
    output = Path(args.output_dir) / "evals" / args.split / "suites" / "robotwin" / args.run_id
    identity = {name: _identity(args, name) for name in names}
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("Task suite resume configuration differs from saved evaluation")
    casa._atomic_json(identity_path, identity)
    metadata = {
        "platform": "robotwin",
        "task_suite": "robotwin",
        "task_names": names,
        "split": args.split,
        "run_id": args.run_id,
        "n_episodes_per_task": args.n_episodes,
    }
    for index, name in enumerate(names):
        print(f"[{index + 1}/{len(names)}] Evaluating RoboTwin task {name}", flush=True)
        try:
            stats = (
                _run_task
                if args.no_process_isolation
                else _run_parallel_task
                if args.n_envs > 1
                else _run_supervised_task
            )(args, name, args.run_id)
            results.append(
                {
                    "env_name": name,
                    "status": "completed",
                    "num_episodes": stats["num_episodes"],
                    "num_successes": sum(bool(e["success"]) for e in stats["episodes"]),
                    "success_rate": stats["success_rate"],
                }
            )
        except Exception as error:
            results.append(
                {"env_name": name, "status": "failed", "error": f"{type(error).__name__}: {error}"}
            )
            casa._save_suite_stats(output, metadata, results)
            if isinstance(error, ServerUnavailableError):
                raise
        casa._save_suite_stats(output, metadata, results)
    return casa._save_suite_stats(output, metadata, results)[1]


def main():
    args = build_parser().parse_args()
    validate_args(args)
    logging.basicConfig(level=logging.INFO if args.verbose_dependencies else logging.WARNING)
    os.chdir(PROJECT_ROOT)
    try:
        stats = run(args)
        if stats.get("num_failed_tasks", 0):
            raise SystemExit(1)
    except ServerUnavailableError as error:
        if args._worker:
            raise SystemExit(SERVER_UNAVAILABLE_EXIT_CODE) from error
        raise


if __name__ == "__main__":
    main()
