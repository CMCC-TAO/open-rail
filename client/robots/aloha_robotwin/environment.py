"""Lazy RoboTwin environment loading and deterministic episode selection."""

import importlib
import json
from pathlib import Path
import re
import sys
import time

import numpy as np
import yaml


def _load_yaml(path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _prepare_robotwin(robotwin_root, task_name, task_config):
    validate_name(task_name)
    validate_name(task_config)
    for path in (
        robotwin_root,
        robotwin_root / "policy",
        robotwin_root / "description" / "utils",
    ):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from envs import CONFIGS_PATH

    args = _load_yaml(robotwin_root / "task_config" / f"{task_config}.yml")
    args["task_name"] = task_name
    args["task_config"] = task_config
    args["eval_mode"] = True
    args["eval_video_save_dir"] = None
    embodiment = args.get("embodiment")
    if embodiment != ["aloha-agilex"]:
        raise ValueError(f"aloha_robotwin requires embodiment [aloha-agilex], got {embodiment}")

    configs_path = Path(CONFIGS_PATH)
    if not configs_path.is_absolute():
        configs_path = robotwin_root / configs_path
    embodiment_registry = _load_yaml(configs_path / "_embodiment_config.yml")
    camera_registry = _load_yaml(configs_path / "_camera_config.yml")
    robot_file = Path(embodiment_registry["aloha-agilex"]["file_path"])
    if not robot_file.is_absolute():
        robot_file = (robotwin_root / robot_file).resolve()
    embodiment_config = _load_yaml(robot_file / "config.yml")
    args["left_robot_file"] = str(robot_file)
    args["right_robot_file"] = str(robot_file)
    args["dual_arm_embodied"] = True
    args["left_embodiment_config"] = embodiment_config
    args["right_embodiment_config"] = embodiment_config
    head_camera = camera_registry[args["camera"]["head_camera_type"]]
    args["head_camera_h"] = head_camera["h"]
    args["head_camera_w"] = head_camera["w"]
    args["policy_name"] = "vla_infer"

    env_module = importlib.import_module(f"envs.{task_name}")
    env_class = getattr(env_module, task_name)
    return args, env_class


def _setup_env(sim_executor, env_class, env_args, episode, seed):
    def setup():
        env = env_class()
        try:
            env.setup_demo(now_ep_num=episode, seed=seed, is_test=True, **env_args)
        except Exception:
            try:
                env.close_env()
            except Exception:
                pass
            raise
        return env

    return sim_executor.submit(setup).result()


def validate_name(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid RoboTwin task/config name: {name!r}")
    return name


def select_episode(
    executor,
    env_class,
    env_args,
    task_name,
    episode,
    seed,
    instruction_type,
    expert_check,
    fixed_instruction,
    max_attempts,
    timeout,
    checkpoint=None,
):
    from envs.utils.create_actor import UnStableError
    from generate_episode_instructions import generate_episode_descriptions

    saved = json.loads(checkpoint.read_text()) if checkpoint and checkpoint.exists() else None
    if saved:
        if saved["episode"] != episode or saved["initial_seed"] != seed:
            raise ValueError("Episode checkpoint identity changed")
        env = _setup_env(executor, env_class, env_args, episode, saved["seed"])
        try:
            executor.submit(env.set_instruction, instruction=saved["instruction"]).result()
            return env, saved["instruction"], saved["seed"]
        except BaseException:
            executor.submit(env.close_env).result()
            raise
    started = time.monotonic()
    initial_seed = seed
    for attempt in range(max_attempts):
        if time.monotonic() - started >= timeout:
            raise TimeoutError(f"RoboTwin episode {episode} seed selection timed out")
        candidate = seed + attempt
        episode_info = None
        if expert_check:
            expert = None
            try:
                expert = _setup_env(executor, env_class, env_args, episode, candidate)
                episode_info = executor.submit(expert.play_once).result()
                valid = executor.submit(
                    lambda: bool(expert.plan_success and expert.check_success())
                ).result()
            except UnStableError:
                valid = False
            finally:
                if expert is not None:
                    executor.submit(expert.close_env).result()
            if not valid:
                continue
        env = _setup_env(executor, env_class, env_args, episode, candidate)
        try:
            if fixed_instruction:
                instruction = fixed_instruction
            elif episode_info is not None:
                descriptions = generate_episode_descriptions(task_name, [episode_info["info"]], 100)
                candidates = descriptions[0][instruction_type]
                if not candidates:
                    raise RuntimeError(f"No {instruction_type} instruction for seed {candidate}")
                instruction = str(np.random.default_rng(candidate).choice(candidates))
            else:
                raise ValueError("--no_expert_check requires --instruction")
            executor.submit(env.set_instruction, instruction=instruction).result()
            if checkpoint:
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                temporary = checkpoint.with_suffix(".tmp")
                temporary.write_text(
                    json.dumps(
                        {
                            "episode": episode,
                            "initial_seed": initial_seed,
                            "seed": candidate,
                            "instruction": instruction,
                        }
                    )
                )
                temporary.replace(checkpoint)
            return env, instruction, candidate
        except BaseException:
            executor.submit(env.close_env).result()
            raise
    raise RuntimeError(f"No valid RoboTwin seed after {max_attempts} attempts")
