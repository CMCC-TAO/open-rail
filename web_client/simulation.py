"""Isolated simulation evaluation jobs for the web client."""

import json
import os
import re
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from typing import Literal

import psutil
import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parent.parent
DEFAULTS_PATH = ROOT / "conf" / "web_simulation.yaml"


def client_evaluation_values(config):
    if not isinstance(config, dict):
        raise ValueError("Configuration snapshot must be an object")
    robots = config.get("robots", {})
    robot_type = robots.get("type")
    platforms = {"robocasa_pandas": "robocasa", "robotwin_aloha": "robotwin"}
    if robot_type not in platforms:
        raise ValueError("Select robocasa_pandas or robotwin_aloha in Configuration")
    robot = robots.get(robot_type, {})
    values = {"platform": platforms[robot_type]}
    mappings = {
        "mode": ("rdm", "mode"),
        "n_action_steps": ("controller", "action_steps"),
        "control_period_ms": ("controller", "period"),
        "intra_chunk_mode": ("intra_chunk", "intra_chunk_mode"),
        "intra_chunk_sample_ratio": ("intra_chunk", "output_sample_ratio"),
        "inter_chunk_mode": ("inter_chunk", "inter_chunk_mode"),
        "max_transition_steps": ("inter_chunk", "max_transition_steps"),
        "server_ip": ("vla_zmq", "ip"),
        "server_port": ("vla_zmq", "port"),
    }
    for key, (group, field) in mappings.items():
        value = config.get(group, {}).get(field)
        if value is not None and value != "":
            values[key] = value
    for key in ("python", "robotwin_root", "gpu", "n_envs", "seed", "split", "task_config", "instruction_type", "render_observation_mode"):
        value = robot.get(key)
        if value is not None and (value != "" or key == "gpu"):
            values[key] = value
    preprocess = config.get("vision", {}).get("preprocess", {}).get("method")
    if preprocess is not None:
        values["preprocess"] = preprocess
    for key, field in (("async_replenish_threshold", "action_replenish_threshold"),
                       ("max_async_observation_lag_steps", "max_async_observation_lag_steps")):
        values[key] = config.get("rdm", {}).get(field) if values.get("mode") == "async" else None
    if robot_type == "robotwin_aloha" and values.get("intra_chunk_mode") != "interpolation":
        values["intra_chunk_sample_ratio"] = 1
    return values


class EvaluationConfig(BaseModel):
    platform: Literal["robocasa", "robotwin"] = "robocasa"
    python: str = sys.executable
    robotwin_root: str = str(ROOT.parent / "RoboTwin")
    task_config: str = "demo_clean"
    instruction_type: Literal["seen", "unseen"] = "unseen"
    render_observation_mode: Literal["chunk_boundary", "per_action"] = "chunk_boundary"
    instruction: str = ""
    no_expert_check: bool = False
    gpu: str = ""
    max_transition_steps: int = Field(5, ge=0)
    max_seed_attempts: int = Field(100, ge=1)
    seed_stride: int = Field(100, ge=1)
    seed_selection_timeout: float = Field(900, gt=0, allow_inf_nan=False)
    worker_episodes: int = Field(100, ge=1)
    max_native_restarts: int = Field(3, ge=0)
    server_reconnect_interval: float = Field(10, gt=0, allow_inf_nan=False)
    server_reconnect_timeout: float = Field(0, ge=0, allow_inf_nan=False)
    env_name: str = ""
    task_suite: str = ""
    split: Literal["target", "pretrain"] = "target"
    n_episodes: int = Field(10, ge=1)
    n_envs: int = Field(1, ge=1)
    n_action_steps: int = Field(16, ge=1)
    control_period_ms: float = Field(1, gt=0, allow_inf_nan=False)
    seed: int = 42
    mode: Literal["sync", "async"] = "sync"
    intra_chunk_mode: Literal["raw", "interpolation", "fitting"] = "raw"
    intra_chunk_sample_ratio: float = Field(1, ge=1, allow_inf_nan=False)
    inter_chunk_mode: Literal["sync", "search_action", "smooth_velocity", "min_jerk"] = "sync"
    async_replenish_threshold: int | None = Field(None, ge=0)
    max_async_observation_lag_steps: int | None = Field(None, ge=0)
    max_episode_steps: int | None = Field(None, ge=1)
    episode_timeout: float = Field(1800, gt=0, allow_inf_nan=False)
    stall_timeout: float = Field(120, gt=0, allow_inf_nan=False)
    server_ip: str = "127.0.0.1"
    server_port: int = Field(1117, ge=1, le=65535)
    mujoco_gl: Literal["egl", "osmesa", "glfw"] = "egl"
    preprocess: Literal["none", "resize"] = "none"
    record: bool = False
    video: bool = True
    record_fps: int = Field(20, ge=1)
    video_fps: int = Field(20, ge=1)
    video_layout: Literal["grid", "single"] = "grid"
    client_config: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def use_client_configuration(cls, data):
        if isinstance(data, dict) and data.get("client_config") is not None:
            data = {**data, **client_evaluation_values(data["client_config"])}
        return data

    @model_validator(mode="after")
    def validate_selection(self):
        self.env_name = self.env_name.strip()
        self.task_suite = self.task_suite.strip()
        self.gpu = self.gpu.strip()
        if self.gpu and not re.fullmatch(r"\d+(,\d+)*", self.gpu):
            raise ValueError("GPU must contain comma-separated indices")
        if self.platform == "robocasa" and "," in self.gpu:
            raise ValueError("RoboCasa requires one rendering GPU index")
        if bool(self.env_name) == bool(self.task_suite):
            raise ValueError("Select exactly one environment or task suite")
        if (
            self.async_replenish_threshold is not None
            and self.async_replenish_threshold >= self.n_action_steps
        ):
            raise ValueError("Async threshold must be less than action steps")
        if self.platform == "robotwin":
            if self.env_name and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.env_name):
                raise ValueError("Invalid RoboTwin task name")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.task_config):
                raise ValueError("Invalid RoboTwin task config")
            if self.no_expert_check and not self.instruction.strip():
                raise ValueError("Disabling expert check requires a fixed instruction")
            if self.max_seed_attempts > self.seed_stride:
                raise ValueError("Seed attempts must not exceed seed stride")
            if self.seed < 0:
                raise ValueError("RoboTwin seed must be non-negative")
        return self


class EvaluationJobs:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.directory = self.root / "data/simulation_web/jobs"
        self.legacy_directory = self.root / "data/robocasa_web/jobs"
        self.lock = threading.RLock()
        self.jobs = {}
        self.processes = {}
        for directory in (self.legacy_directory, self.directory):
            for path in directory.glob("*/job.json"):
                try:
                    job = json.loads(path.read_text())
                    if job["status"] in ("running", "stopping"):
                        job["status"] = "interrupted"
                    self.jobs[path.parent.name] = job
                except (ValueError, KeyError, OSError):
                    continue

    def job_directory(self, job_id):
        folder = self.directory / job_id
        legacy = self.legacy_directory / job_id
        return legacy if not folder.exists() and legacy.is_dir() else folder

    def _save(self, job):
        path = self.job_directory(job["id"]) / "job.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2))
        temporary.replace(path)

    def command(self, config, job_id):
        folder = self.job_directory(job_id)
        robotwin = config.platform == "robotwin"
        script = "aloha_robotwin_eval.py" if robotwin else "robocasa_eval.py"
        command = [config.python, "-u", str(self.root / "scripts" / script)]
        robotwin_fields = {
            "render_observation_mode",
            "robotwin_root",
            "task_config",
            "instruction_type",
            "instruction",
            "gpu",
            "max_transition_steps",
            "max_seed_attempts",
            "seed_stride",
            "seed_selection_timeout",
        }
        excluded = {
            "platform",
            "python",
            "record",
            "video",
            "env_name",
            "task_suite",
            "no_expert_check",
            "client_config",
        }
        excluded |= {"split", "mujoco_gl"} if robotwin else robotwin_fields
        for key, value in config.model_dump().items():
            if key not in excluded and value is not None and value != "":
                command.extend(["--" + key, str(value)])
        command.extend(
            [
                "--env_name" if config.env_name else "--task_suite",
                config.env_name or config.task_suite,
                "--output_dir",
                str(folder / "output"),
                "--run_id",
                job_id,
                "--progress_interval",
                "5",
                "--record_dir",
                str(folder.relative_to(self.root) / "lerobot"),
            ]
        )
        if config.record:
            command.append("--record")
        if not config.video:
            command.append("--no_video")
        if robotwin and config.no_expert_check:
            command.append("--no_expert_check")
        if config.client_config is not None:
            command.extend(["--user_conf", str(folder / "client_config.py")])
        return command

    def start(self, config, job_id=None):
        with self.lock:
            if self.processes:
                raise ValueError("An evaluation is already running")
            for previous in self.jobs.values():
                if previous["status"] != "interrupted" or not previous.get("pid"):
                    continue
                try:
                    old = psutil.Process(previous["pid"])
                    if (
                        old.create_time() == previous.get("process_created")
                        and old.status() != psutil.STATUS_ZOMBIE
                    ):
                        raise ValueError(
                            "Previous evaluation process is still alive; stop the interrupted job first"
                        )
                except psutil.NoSuchProcess:
                    pass
            executable = Path(config.python).expanduser().absolute()
            if not executable.is_file() or not os.access(executable, os.X_OK):
                raise ValueError("Python executable does not exist or is not executable")
            config.python = str(executable)
            dependencies = (
                ["zmq", "numpy", "sapien", "torch", "yaml", "curobo"]
                if config.platform == "robotwin"
                else ["robocasa", "robosuite", "zmq", "numpy"]
            )
            if config.platform == "robotwin":
                root = Path(config.robotwin_root).expanduser().resolve()
                if (
                    not (root / "envs").is_dir()
                    or not (root / "task_config" / (config.task_config + ".yml")).is_file()
                ):
                    raise ValueError("RoboTwin root or task config is unavailable")
                if config.env_name and not (root / "envs" / (config.env_name + ".py")).is_file():
                    raise ValueError("RoboTwin task is unavailable")
                config.robotwin_root = str(root)
                if config.task_suite:
                    from scripts.aloha_robotwin_eval import _task_names

                    selection = Path(config.task_suite).expanduser()
                    if ',' not in config.task_suite and selection.is_file():
                        config.task_suite = str(selection.resolve())
                    task_names = _task_names(config.task_suite)
                    config.task_suite = ",".join(task_names)
                    for name in task_names:
                        if not (root / "envs" / (name + ".py")).is_file():
                            raise ValueError(f"RoboTwin task is unavailable: {name}")
            check_code = "import importlib.util,sys; missing=[n for n in sys.argv[1:] if importlib.util.find_spec(n) is None]; print(', '.join(missing)); raise SystemExit(bool(missing))"
            check = subprocess.run(
                [config.python, "-c", check_code, *dependencies],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if check.returncode:
                raise ValueError(
                    "Simulation environment unavailable: " + (check.stdout + check.stderr)[-2000:]
                )
            job_id = job_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
            job = {
                "id": job_id,
                "config": config.model_dump(),
                "status": "running",
                "started": time.time(),
                "returncode": None,
            }
            self._save(job)
            folder = self.job_directory(job_id)
            if config.client_config is not None:
                snapshot = json.dumps(config.client_config, ensure_ascii=True, indent=2)
                (folder / "client_config.json").write_text(snapshot)
                (folder / "client_config.py").write_text(
                    "import json\n\ndef get_user_config():\n    return json.loads(" + repr(snapshot) + ")\n"
                )
            log = open(folder / "evaluation.log", "ab", buffering=0)
            environment = os.environ.copy()
            environment['VLA_SIM_PREVIEW_PATH'] = str(folder / 'preview.json')
            if config.platform == "robocasa" and config.gpu:
                environment["CUDA_VISIBLE_DEVICES"] = config.gpu
                environment["MUJOCO_EGL_DEVICE_ID"] = config.gpu
            try:
                process = subprocess.Popen(
                    self.command(config, job_id),
                    cwd=self.root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env=environment,
                )
            except Exception:
                log.close()
                job["status"] = "failed"
                self._save(job)
                self.jobs[job_id] = job
                raise
            log.close()
            job["pid"] = process.pid
            try:
                job["process_created"] = psutil.Process(process.pid).create_time()
            except psutil.NoSuchProcess:
                job["process_created"] = None
            self._save(job)
            self.jobs[job_id] = job
            self.processes[job_id] = process
            threading.Thread(target=self._watch, args=(job_id, process), daemon=True).start()
            return job.copy()

    def _watch(self, job_id, process):
        code = process.wait()
        with self.lock:
            job = self.jobs[job_id]
            if job["status"] != "stopping":
                failed_tasks = any(s.get("num_failed_tasks", 0) for s in self._stats(job_id))
                job["status"] = "completed" if code == 0 and not failed_tasks else "failed"
                self.processes.pop(job_id, None)
            job["returncode"] = code
            self._save(job)

    def stop(self, job_id):
        with self.lock:
            job = self.get(job_id)
            process = self.processes.get(job_id)
            recovered = None
            if process is None and job["status"] == "interrupted" and job.get("pid"):
                try:
                    candidate = psutil.Process(job["pid"])
                    if candidate.create_time() == job.get("process_created"):
                        recovered = candidate
                except psutil.NoSuchProcess:
                    pass
            if process is None and recovered is None:
                return job
            self.jobs[job_id]["status"] = "stopping"
            self._save(self.jobs[job_id])
            try:
                parent = recovered or psutil.Process(process.pid)
                children = parent.children(recursive=True)
                targets = [parent] + children
            except psutil.NoSuchProcess:
                targets = []
        for target in targets:
            try:
                target.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(targets, timeout=5)
        for target in alive:
            try:
                target.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(alive, timeout=3)
        if process is not None:
            process.wait(timeout=5)
        with self.lock:
            self.processes.pop(job_id, None)
            self.jobs[job_id]["status"] = "cancelled"
            self._save(self.jobs[job_id])
            return self.get(job_id)

    def close(self):
        for job_id in list(self.processes):
            self.stop(job_id)

    def _stats(self, job_id):
        result = []
        for path in (self.job_directory(job_id) / "output").rglob("stats.json"):
            try:
                stats = json.loads(path.read_text())
                if stats.get("run_id") == job_id:
                    result.append(stats)
            except (OSError, ValueError):
                pass
        return result

    def get(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise KeyError(job_id)
            job = self.jobs[job_id].copy()
        job["directory"] = str(self.job_directory(job_id).relative_to(self.root))
        job["stats"] = self._stats(job_id)
        grouped = {}
        for stats in job["stats"]:
            if not stats.get("env_name"):
                continue
            episodes = grouped.setdefault(stats["env_name"], {})
            for episode in stats.get("episodes", []):
                episodes[episode["episode"]] = episode
        job["progress"] = [
            {
                "env_name": name,
                "num_episodes": len(episodes),
                "success_rate": sum(bool(e.get("success")) for e in episodes.values())
                / len(episodes)
                if episodes
                else 0,
            }
            for name, episodes in grouped.items()
        ]
        return job

    def artifact(self, job_id, name):
        self.get(job_id)
        folder = self.job_directory(job_id).resolve()
        path = (folder / name).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise KeyError(name)
        return path


manager = EvaluationJobs()
router = APIRouter(prefix="/api/simulation")


@router.get("/options")
def options(platform: Literal["robocasa", "robotwin"] = "robocasa"):
    defaults = EvaluationConfig(env_name="PickPlaceCounterToCabinet").model_dump()
    if platform == "robotwin":
        defaults.update(n_action_steps=50, seed=0)
    else:
        defaults.update(gpu="2")
    if DEFAULTS_PATH.exists():
        settings = yaml.safe_load(DEFAULTS_PATH.read_text()) or {}
        defaults.update(settings.get("defaults", {}))
        defaults.update(settings.get("platforms", {}).get(platform, {}))
    if not defaults.get("python"):
        defaults["python"] = sys.executable
    defaults["platform"] = platform
    try:
        from conf.client_conf import get_client_config

        config = get_client_config()
        defaults["server_port"] = int(config.vla_zmq.port)
        defaults["server_ip"] = config.vla_zmq.ip
    except (ImportError, AttributeError):
        pass
    if hasattr(manager, "connection_provider"):
        defaults["server_ip"], defaults["server_port"] = manager.connection_provider()
    elif hasattr(manager, "connection_defaults"):
        defaults["server_ip"], defaults["server_port"] = manager.connection_defaults
    return EvaluationConfig(**defaults).model_dump()


@router.get("/task-catalog")
def get_task_catalog(platform: Literal["robocasa", "robotwin"]):
    from web_client.task_catalog import task_catalog

    config = options(platform)
    try:
        return task_catalog(platform, config['python'], config['robotwin_root'], str(ROOT))
    except (OSError, ValueError, KeyError, SyntaxError, subprocess.SubprocessError) as error:
        raise HTTPException(400, str(error)) from error


@router.get("/jobs")
def list_jobs():
    with manager.lock:
        return sorted(
            (j.copy() for j in manager.jobs.values()), key=lambda j: j["started"], reverse=True
        )


@router.get("/preview")
def camera_preview():
    with manager.lock:
        jobs = [j.copy() for j in manager.jobs.values() if j['status'] == 'running']
    if not jobs:
        return {'job': None, 'frames': []}
    job = max(jobs, key=lambda j: j['started'])
    result = {
        'job': {'id': job['id'], 'env_name': job['config'].get('env_name') or job['config'].get('task_suite')},
        'frames': [],
    }
    try:
        snapshot = json.loads((manager.job_directory(job['id']) / 'preview.json').read_text())
        if snapshot['timestamp'] >= job['started'] and time.time() - snapshot['timestamp'] < 5:
            result.update(snapshot)
    except (OSError, ValueError, KeyError):
        pass
    return result


@router.post("/jobs")
def start_job(config: EvaluationConfig):
    try:
        return manager.start(config)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        raise HTTPException(400, str(error)) from error


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    try:
        return manager.get(job_id)
    except KeyError as error:
        raise HTTPException(404, "Job not found") from error


@router.post("/jobs/{job_id}/stop")
def stop_job(job_id: str):
    try:
        return manager.stop(job_id)
    except KeyError as error:
        raise HTTPException(404, "Job not found") from error


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    job = get_job(job_id)
    if job["status"] not in ("cancelled", "failed", "interrupted"):
        raise HTTPException(409, "Only stopped or failed jobs can resume")
    try:
        return manager.start(EvaluationConfig(**job["config"]), job_id)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        raise HTTPException(400, str(error)) from error


@router.get("/jobs/{job_id}/logs")
def logs(job_id: str):
    get_job(job_id)
    path = manager.job_directory(job_id) / "evaluation.log"
    if not path.exists():
        return {"text": ""}
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - 64000))
        return {"text": handle.read(64000).decode("utf-8", errors="replace")}


@router.get("/jobs/{job_id}/files")
def files(job_id: str):
    get_job(job_id)
    folder = manager.job_directory(job_id)
    return [
        str(p.relative_to(folder))
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix in (".json", ".mp4", ".parquet")
        and p.resolve().is_relative_to(folder.resolve())
    ]


@router.get("/jobs/{job_id}/artifact/{name:path}")
def artifact(job_id: str, name: str):
    try:
        return FileResponse(manager.artifact(job_id, name))
    except KeyError as error:
        raise HTTPException(404, "File not found") from error
