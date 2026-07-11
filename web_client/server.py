"""
VLA Web Client Server
FastAPI-based web server that wraps run_client.py logic for browser-based control.

Architecture:
    - REST API  : config load/save/update, client start/stop
    - WebSocket : real-time runtime stats push (replaces Rich Live)
    - Port 9000 : this server (HTTP + WS)
    - Port 8765 : visual/ WebSocket data stream  (visual integration ready)
    - Port 8080 : visual/ static file server      (visual integration ready)
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    psutil = None
    _HAS_PSUTIL = False

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── project root on sys.path ────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from conf.client_conf import get_client_config
from conf.robots_conf import RobotType
from conf.logging_conf import setup_logging
from client.core.zmq_client import ZMQClient
from client.core.inter_chunk_fuser import InterChunkFuser
from client.core.intra_chunk_smoother import IntraChunkSmoother
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.task_language_manager import TaskLanguageManager
from client.utils.util import load_user_config, apply_user_config, parse_action_layout
from client.robots.base_robot import RobotBase

logger = logging.getLogger(__name__)


def _finalize_pyarrow_s3():
    """Release PyArrow's global S3 resources on graceful shutdown."""
    try:
        import pyarrow.fs as arrow_fs
        arrow_fs.finalize_s3()
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.debug(f"PyArrow S3 cleanup skipped: {e}")


# ── FastAPI app ──────────────────────────────────────────────────────────────
# lifespan replaces the deprecated @app.on_event("startup"/"shutdown") pattern.
# The context manager is defined inline here; module-level globals (client_state, etc.)
# are accessible at call-time (not at definition time), so forward-use is safe.
@asynccontextmanager
async def _lifespan(_: FastAPI):
    # ── startup ──
    setup_logging("client.log")
    client_state.config = get_client_config()
    client_state.conf_file = os.environ.get("conf_file", "default_conf.yaml")
    # print(f"Initial client.record config: {client_state.config.record}")
    DEFAULT_YAML = ROOT / "conf" / client_state.conf_file
    if DEFAULT_YAML.exists():
        try:
            _apply_yaml_config(client_state.config, DEFAULT_YAML)
        except Exception as e:
            logger.warning(f"Failed to apply yaml conf: {e}")
    # print(f"Debug: config_file = {client_state.conf_file}")
    # print(f"Initial client.record config: {client_state.config.record}")
    # print(f"Visualize trajectory config: {client_state.config.visualize.trajectory}")

    # Use a dedicated thread pool for the asyncio event loop so that
    # asyncio.to_thread() tasks are never queued behind business threads
    # (image encoding, ZMQ, robot SDK) that compete for the GIL.
    _api_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="api_worker")
    loop = asyncio.get_running_loop()
    loop.set_default_executor(_api_executor)

    asyncio.create_task(_stats_push_loop())
    _ensure_vla_client_created()
    logger.info("VLA Web Client server started on http://localhost:9000")
    yield
    # ── shutdown ──
    _shutdown_stop_if_running()
    # Avoid closing low-level robot SDK from a detached daemon cleanup thread,
    # which can crash (segfault) during interpreter shutdown.
    _cleanup(force_release_robot=True, skip_robot_close_if_threads_alive=True)
    _api_executor.shutdown(wait=False)
    _finalize_pyarrow_s3()

app = FastAPI(title="VLA Web Client", version="1.0.0", lifespan=_lifespan)

STATIC_DIR  = Path(__file__).parent / "static"
VISUAL_DIR  = ROOT / "visual"

# Default config files bundled with the project
DEFAULT_LANG_CMD = ROOT / "conf" / "lang_cmd.json"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Expose visual/ libs (Chart.js, hammer, zoom plugin) used by web_client
if VISUAL_DIR.exists():
    app.mount("/visual", StaticFiles(directory=str(VISUAL_DIR)), name="visual")


# ─────────────────────────────────────────────────────────────────────────────
#  Global client_state
# ─────────────────────────────────────────────────────────────────────────────
class ClientState:
    def __init__(self):
        self.vla_client = None
        self.robot = None
        self.config = None
        self.conf_file = None
        self.running = False
        self.starting = False
        self.stopping = False
        self.paused = False
        self.lock = threading.Lock()
        self.ws_clients: set[WebSocket] = set()
        self.ws_lock = threading.Lock()
        self._broadcast_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.paused_thread_state: Optional[dict] = None
        self.worker_thread: Optional[threading.Thread] = None

client_state = ClientState()
select_directory_lock = asyncio.Lock()

_RESOURCE_CACHE = {
    "ts": 0.0,
    "data": {
        "cpu_usage": None,
        "gpu_usage": None,
        "mem_usage": None,
        "bandwidth_m": None,
    }
}
_LAST_CPU_STAT = None
_LAST_NET_STAT = None
_NVIDIA_SMI_BIN = shutil.which("nvidia-smi")
_HAS_NVIDIA_SMI = _NVIDIA_SMI_BIN is not None


def _read_linux_cpu_usage() -> Optional[float]:
    """Read CPU usage percentage from /proc/stat without extra dependencies."""
    global _LAST_CPU_STAT
    try:
        with open("/proc/stat", "r", encoding="utf-8") as f:
            line = f.readline().strip()
        parts = line.split()
        if len(parts) < 8 or parts[0] != "cpu":
            return None
        vals = [int(x) for x in parts[1:8]]
        idle = vals[3] + vals[4]
        total = sum(vals)
        if _LAST_CPU_STAT is None:
            _LAST_CPU_STAT = (idle, total)
            return None
        prev_idle, prev_total = _LAST_CPU_STAT
        _LAST_CPU_STAT = (idle, total)
        total_delta = total - prev_total
        idle_delta = idle - prev_idle
        if total_delta <= 0:
            return None
        usage = (1.0 - (idle_delta / total_delta)) * 100.0
        return max(0.0, min(100.0, usage))
    except Exception:
        return None


def _read_linux_mem_usage() -> Optional[float]:
    """Read memory usage percentage from /proc/meminfo."""
    try:
        mem_total = None
        mem_available = None
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = float(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = float(line.split()[1])
                if mem_total is not None and mem_available is not None:
                    break
        if not mem_total or mem_available is None:
            return None
        usage = (1.0 - mem_available / mem_total) * 100.0
        return max(0.0, min(100.0, usage))
    except Exception:
        return None


def _parse_gpu_util_lines(raw_text: str) -> list[float]:
    vals: list[float] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.replace("%", "").strip()
        try:
            vals.append(float(line))
        except Exception:
            continue
    return vals


def _read_gpu_usage() -> Optional[float]:
    """Read average GPU utilization from NVIDIA GPUs via nvidia-smi."""
    try:
        if not _HAS_NVIDIA_SMI or not _NVIDIA_SMI_BIN:
            return None

        # Prefer nounits format; fallback to plain csv for older drivers/toolchains.
        cmd_list = [
            [_NVIDIA_SMI_BIN, "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            [_NVIDIA_SMI_BIN, "--query-gpu=utilization.gpu", "--format=csv,noheader"],
        ]

        for cmd in cmd_list:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            if proc.returncode != 0:
                continue
            vals = _parse_gpu_util_lines(proc.stdout)
            if vals:
                usage = sum(vals) / len(vals)
                return max(0.0, min(100.0, usage))
        return None
    except Exception:
        return None


def _read_linux_net_bytes_total() -> Optional[float]:
    """Read total network bytes (rx + tx) from /proc/net/dev."""
    try:
        total = 0.0
        with open("/proc/net/dev", "r", encoding="utf-8") as f:
            lines = f.readlines()[2:]
        for line in lines:
            if ":" not in line:
                continue
            _, payload = line.split(":", 1)
            parts = payload.split()
            if len(parts) < 16:
                continue
            rx_bytes = float(parts[0])
            tx_bytes = float(parts[8])
            total += rx_bytes + tx_bytes
        return total
    except Exception:
        return None


def _read_bandwidth_m() -> Optional[float]:
    """Read total communication bandwidth in MB/s (rx + tx)."""
    global _LAST_NET_STAT
    now = time.time()

    total_bytes = None
    if _HAS_PSUTIL and psutil is not None:
        try:
            io = psutil.net_io_counters()
            total_bytes = float(io.bytes_recv + io.bytes_sent)
        except Exception:
            total_bytes = None

    if total_bytes is None:
        total_bytes = _read_linux_net_bytes_total()

    if total_bytes is None:
        return None

    if _LAST_NET_STAT is None:
        _LAST_NET_STAT = (now, total_bytes)
        return None

    prev_ts, prev_total = _LAST_NET_STAT
    _LAST_NET_STAT = (now, total_bytes)
    dt = now - prev_ts
    if dt <= 0:
        return None

    delta = max(0.0, total_bytes - prev_total)
    return delta / dt / (1024.0 * 1024.0)


def _collect_resource_stats() -> dict:
    """Collect resource stats with 1s cache to reduce overhead."""
    now = time.time()
    if now - _RESOURCE_CACHE["ts"] < 1.0:
        return _RESOURCE_CACHE["data"]

    cpu_usage = None
    mem_usage = None

    if _HAS_PSUTIL and psutil is not None:
        try:
            cpu_usage = float(psutil.cpu_percent(interval=None))
        except Exception:
            cpu_usage = None
        try:
            mem_usage = float(psutil.virtual_memory().percent)
        except Exception:
            mem_usage = None

    if cpu_usage is None:
        cpu_usage = _read_linux_cpu_usage()
    if mem_usage is None:
        mem_usage = _read_linux_mem_usage()

    gpu_usage = _read_gpu_usage()
    bandwidth_m = _read_bandwidth_m()

    data = {
        "cpu_usage": round(cpu_usage, 1) if cpu_usage is not None else None,
        "gpu_usage": round(gpu_usage, 1) if gpu_usage is not None else None,
        "mem_usage": round(mem_usage, 1) if mem_usage is not None else None,
        "bandwidth_m": round(bandwidth_m, 2) if bandwidth_m is not None else None,
    }
    _RESOURCE_CACHE["ts"] = now
    _RESOURCE_CACHE["data"] = data
    return data


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers: config serialization
# ─────────────────────────────────────────────────────────────────────────────
def _config_to_dict(cfg) -> dict:
    """Recursively convert a ConfigDict (or any object) to a plain dict."""
    if cfg is None:
        return {}
    try:
        from ml_collections import ConfigDict
        if isinstance(cfg, ConfigDict):
            result = {}
            for k in cfg:
                v = cfg[k]
                if isinstance(v, ConfigDict):
                    result[k] = _config_to_dict(v)
                elif hasattr(v, 'value'):           # Enum
                    result[k] = v.value
                elif isinstance(v, (list, tuple)):
                    result[k] = [x.value if hasattr(x, 'value') else x for x in v]
                else:
                    result[k] = v
            return result
    except Exception:
        pass
    return {}


def _normalize_record_features_cam(cfg_dict: dict) -> dict:
    """Normalize legacy nested record.lerobot.features.cam.* into dotted cam.* keys."""
    if not isinstance(cfg_dict, dict):
        return cfg_dict

    record_cfg = cfg_dict.get("record", {})
    lerobot_cfg = record_cfg.get("lerobot")
    features = lerobot_cfg.get("features", {}) if isinstance(lerobot_cfg, dict) else {}
    if isinstance(features, dict):
        cam = features.get("cam")
        if isinstance(cam, dict):
            features.pop("cam", None)
            for cam_key, cam_val in cam.items():
                features[f"cam.{cam_key}"] = cam_val
    return cfg_dict

def _apply_flat_patch_new(config, patch: dict):
    """Apply flat patch only to existing config leaf keys (no new key creation)."""
    import enum
    from ml_collections import ConfigDict

    if not isinstance(patch, dict) or config is None:
        return

    legacy_inter_chunk_keys = {
        "inter_chunk.search_length": "inter_chunk.search_action.search_length",
    }
    patch = {
        legacy_inter_chunk_keys.get(key, key): value
        for key, value in patch.items()
    }

    def _is_mapping(obj):
        return isinstance(obj, (dict, ConfigDict))

    def _iter_keys(obj):
        if not _is_mapping(obj):
            return []
        return list(obj.keys())

    def _get(obj, key, default=None):
        if _is_mapping(obj):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return obj[key] if key in obj else default
        return getattr(obj, key, default)

    def _set(obj, key, value):
        if _is_mapping(obj):
            obj[key] = value
        else:
            setattr(obj, key, value)

    def _walk_leaf_paths(node, prefix=""):
        if not _is_mapping(node):
            return

        for key in _iter_keys(node):
            child = _get(node, key, None)
            path = f"{prefix}.{key}" if prefix else str(key)
            if _is_mapping(child):
                yield from _walk_leaf_paths(child, path)
            else:
                yield path, node, key, child

    applied = 0
    for dotkey, parent, leaf_key, current_val in _walk_leaf_paths(config):
        if dotkey not in patch:
            continue

        value = patch[dotkey]
        # logger.info(f"Applied config key= {dotkey}, value = {value}")
        if isinstance(current_val, enum.Enum):
            enum_cls = current_val.__class__
            try:
                value = enum_cls(value)
            except Exception:
                pass

        try:
            _set(parent, leaf_key, value)
            applied += 1
        except Exception as e:
            logger.warning(f"Failed to patch config key '{dotkey}': {e}")

    dropped = [k for k in patch.keys() if k not in {p for p, _, _, _ in _walk_leaf_paths(config)}]
    if dropped:
        logger.debug(f"Ignored non-existing config keys in patch: {dropped}")

    logger.info(f"Applied config patch keys: {applied}/{len(patch)}")
robot_instance = None
_cleanup_guard = threading.Lock()

def _get_robot(robot_type, robot_config):
    global robot_instance

    # Reuse existing robot instance when the type matches.
    # This avoids re-initializing A2D DDS node after stop/start cycles.
    if robot_instance is not None:
        module_name = getattr(robot_instance.__class__, "__module__", "")
        if robot_type == RobotType.A2D and module_name.endswith("client.robots.a2d.body_robot"):
            return robot_instance, True
        
        if robot_type == RobotType.TI5_T170C and module_name.endswith("client.robots.ti5_t170c.body_robot"):
            return robot_instance, True

        if robot_type == RobotType.NAVI_WA2 and module_name.endswith("client.robots.navi_wa2.body_robot"):
            return robot_instance, True

        if robot_type == RobotType.MOCK and module_name.endswith("client.robots.mock.body_robot"):
            desired_path = str(getattr(robot_config, 'dataset_path', '') or '')
            current_path = str(getattr(robot_instance, 'dataset_path', '') or '')
            if desired_path and desired_path != current_path and hasattr(robot_instance, 'reset'):
                try:
                    robot_instance.reset(dataset_path=desired_path, reload_dataset=True)
                    logger.info(f"Reload mock dataset during robot reuse: {current_path} -> {desired_path}")
                except Exception as e:
                    logger.warning(f"Failed to reload reused mock robot with new dataset path, will recreate robot: {e}")
                    try:
                        robot_instance.close()
                    except Exception:
                        pass
                    robot_instance = None
                else:
                    return robot_instance, True
            else:
                return robot_instance, True

        try:
            robot_instance.close()
        except Exception:
            pass
        robot_instance = None

    if robot_type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        robot_instance = RobotBody(robot_config)
    elif robot_type == RobotType.NAVI_WA2:
        from client.robots.navi_wa2.body_robot import RobotBody
        robot_instance = RobotBody(robot_config)
    elif robot_type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        robot_instance = RobotBody(robot_config)
    elif robot_type == RobotType.TI5_T170C:
        from client.robots.ti5_t170c.body_robot import RobotBody
        robot_instance = RobotBody(robot_config)
    else:
        raise ValueError(f"Unsupported robot type: {robot_type}")
    return robot_instance, False


def _bind_robot_to_vla_client(vla_client, robot):
    if vla_client is not None:
        vla_client.robot = robot
    with client_state.lock:
        if client_state.vla_client is vla_client:
            client_state.robot = robot


def _sync_robot_action_layout(client_config, robot_config, vla_client=None):
    if robot_config is None or not hasattr(robot_config, 'action_layout'):
        return
    layout = robot_config.action_layout
    client_config.rdm.action_layout = layout
    client_config.intra_chunk.action_layout = layout
    if vla_client is not None:
        changed = vla_client.intra_chunk_smoother.action_layout != dict(layout)
        smoother = vla_client.intra_chunk_smoother
        smoother.action_layout = dict(layout)
        smoother.action_dim, smoother.joint_indices, smoother.step_indices = parse_action_layout(layout)
        if changed:
            vla_client.realtime_data_manager.clear()


def _ensure_config_robot_bound(force_recreate: bool = False):
    """Create robot by current config and inject into existing vla_client."""
    global robot_instance

    with client_state.lock:
        vla_client = client_state.vla_client
        client_config = client_state.config
        current_robot = client_state.robot

    if vla_client is None:
        return None
    if client_config is None:
        client_config = get_client_config()
        client_state.config = client_config

    if force_recreate and robot_instance is not None:
        try:
            robot_instance.close()
        except Exception:
            pass
        robot_instance = None

    robot_config = getattr(client_config.robots, client_config.robots.type.value, None)
    _sync_robot_action_layout(client_config, robot_config, vla_client)

    robot, _ = _get_robot(client_config.robots.type, robot_config)
    if current_robot is robot:
        _bind_robot_to_vla_client(vla_client, robot)
        return robot

    # Default RobotBase instance used at init can be replaced directly.
    # Non-cached previous robot release is handled by _get_robot() path.
    _bind_robot_to_vla_client(vla_client, robot)
    return robot


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket broadcast
# ─────────────────────────────────────────────────────────────────────────────
async def _broadcast_to_web(message: dict):
    """Send JSON to all connected WebSocket clients."""
    if not client_state.ws_clients:
        return
    data = json.dumps(message)
    dead = set()
    with client_state.ws_lock:
        clients = set(client_state.ws_clients)
    for ws in clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    if dead:
        with client_state.ws_lock:
            client_state.ws_clients -= dead


async def _stats_push_loop():
    """Background coroutine: push runtime stats to all WS clients every 250 ms."""
    while True:
        await asyncio.sleep(0.25)
        if not client_state.ws_clients:
            continue
        try:
            stats = await asyncio.to_thread(_collect_stats)
            # print("Debug: pushing stats to WS clients.")
            await _broadcast_to_web({"type": "stats", "data": stats})
        except Exception as e:
            logger.debug(f"stats push error: {e}")

def _collect_stats() -> dict:
    """Gather runtime stats from the running vla_client."""
    base = {
        "running": client_state.running,
        "paused": False,
        "observe_running": False,
        "inference_running": False,
        "control_running": False,
        "infer_count": 0,
        "avg_infer_time": 0.0,
        "avg_comm_time": 0.0,
        "avg_intra_traj_time": 0.0,
        "avg_inter_traj_time": 0.0,
        "obv_fps": 0.0,
        "img_proc_time": 0.0,
        "current_prob_progress": 0.0,
        "language": "",
        # "current_state": [],
        # "current_action": [],
        # "info_obs": {},
        # "info_act": {},
        # "debug_info": "",
        "config_snapshot": {},
        "cpu_usage": None,
        "gpu_usage": None,
        "mem_usage": None,
        "bandwidth_m": None,
        "zmq_connected": False,  # 添加 ZMQ 连接状态
    }
    with client_state.lock:
        vla_client = client_state.vla_client
        base["paused"] = bool(client_state.running and (client_state.paused_thread_state is not None))
    base.update(_collect_resource_stats())

    if vla_client is None:
        return base

    try:
        base["observe_running"] = bool(getattr(vla_client, "is_observe_thread_running", False))
        base["inference_running"] = bool(getattr(vla_client, "is_inference_thread_running", False))
        base["control_running"] = bool(getattr(vla_client, "is_control_thread_running", False))
        base["img_proc_time"] = float(getattr(vla_client, "image_process_time", 0.0))
        base["current_prob_progress"] = float(getattr(vla_client, "current_prob_progress", 0.0))
        base["infer_count"]     = int(vla_client.realtime_data_manager.infer_count)
        base["avg_infer_time"]  = float(vla_client.realtime_data_manager.avg_infer_time)
        base["avg_comm_time"]  = float(vla_client.realtime_data_manager.avg_comm_time)
        base["avg_intra_traj_time"]   = float(vla_client.realtime_data_manager.avg_intra_traj_time)
        base["avg_inter_traj_time"]   = float(vla_client.realtime_data_manager.avg_inter_traj_time)
        base["obv_fps"]         = float(vla_client.realtime_data_manager.get_observe_fps())
        base["language"]        = str(vla_client.task_language_manager.currt_language_instruction)
        # 添加 ZMQ 客户端连接状态
        if hasattr(vla_client, 'vla_zmq') and vla_client.vla_zmq is not None:
            base["zmq_connected"] = bool(getattr(vla_client.vla_zmq, "is_connected", False))
            # Update server_ip, server_port, model_type, model_path, lang_cmd
            base.update(vla_client.vla_zmq.get_heartbeat_info())
        
        # Use show_thread_lock to snapshot mutable state safely (written by observe/control threads)
        # acquired = vla_client.show_thread_lock.acquire(timeout=0.05)
        # try:
        #     # current_state  = list(vla_client.info_current_state)
        #     # current_action = list(vla_client.info_current_action)
        #     # info_obs = dict(vla_client.info_obs)
        #     # info_act = dict(vla_client.info_act)
        # finally:
        #     pass
            # if acquired:
            #     vla_client.show_thread_lock.release()
        # base["current_state"]   = [round(float(x), 4) for x in current_state]
        # base["current_action"]  = [round(float(x), 4) for x in current_action]
        # base["info_obs"]        = {k: str(v) for k, v in info_obs.items()}
        # base["info_act"]        = {k: str(v) for k, v in info_act.items()}
        try:
            # base["current_prob_progress"] = float(info_act.get("current_prob_progress", 0.0))
            base["sub_task_id"] = int(vla_client.config.language.sub_task_id) if hasattr(vla_client.config.language, 'sub_task_id') else None
            # print(f"Debug: sub_task_id: {vla_client.config.language.sub_task_id}")
        except Exception as e:
            # base["current_prob_progress"] = 0.0
            logger.error("Failed to get sub task id from language config: {e}")
        # base["debug_info"]      = str(vla_client.debug_info)
        # base["config_snapshot"] = {
        #     "fps":              cfg.observer.fps,
        #     "wait_time":        cfg.controller.wait_time,
        #     "inter_chunk_mode": cfg.inter_chunk.inter_chunk_mode,
        #     "intra_chunk_mode": cfg.intra_chunk.intra_chunk_mode,
        #     "gripper_offset":   cfg.controller.gripper_offset,
        #     "preprocess":       cfg.preprocess,
        #     "robots_type":      cfg.robots.type.value if hasattr(cfg.robots.type, 'value') else str(cfg.robots.type),
        #     "record":           cfg.record.switch,
        #     "task_progress_threshold": cfg.task_progress_threshold,
        # }
    except Exception as e:
        # base["debug_info"] = f"stats error: {e}"
        logger.error(f"Failed to collect stats: {e}")
    return base


# ─────────────────────────────────────────────────────────────────────────────
#  REST: root
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/favicon.ico")
async def favicon():
    icon_path = STATIC_DIR / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    raise HTTPException(status_code=404, detail="favicon.ico not found")


# ─────────────────────────────────────────────────────────────────────────────
#  REST: config
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/client/config/path")
async def get_conf_dir():
    """Return the absolute path of the project conf/ directory."""
    # conf_dir = ROOT / "conf" / client_state.conf_file
    return {"status": "ok", "path": str(client_state.conf_file)}

class ConfigFileRequest(BaseModel):
    path: str

@app.post("/api/client/config/path")
async def set_conf_dir(req: ConfigFileRequest):
    """Load a yaml conf file and apply it. Effective immediately when possible."""
    client_state.conf_file = req.path
    return {"status": "ok", "path": str(client_state.conf_file)}

@app.get("/api/client/robot/select_directory")
async def select_directory(path: Optional[str] = None):
    """Open a native directory chooser and return an absolute path."""
    selected = ""
    initial_dir = str(ROOT)
    if path:
        try:
            p = Path(path).expanduser()
            if p.exists():
                initial_dir = str(p if p.is_dir() else p.parent)
        except Exception:
            initial_dir = str(ROOT)

    async with select_directory_lock:
        has_gui = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        used_zenity = False
        zenity_failed = False
        if has_gui and shutil.which("zenity"):
            used_zenity = True
            try:
                zenity_cmd = ["zenity", "--file-selection", "--directory", "--title=Select Dataset Directory"]
                if initial_dir:
                    zenity_cmd.extend(["--filename", str(Path(initial_dir).resolve())])
                proc = await asyncio.to_thread(
                    subprocess.run,
                    zenity_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
                if proc.returncode == 0:
                    selected = proc.stdout.strip()
                elif proc.returncode == 1:
                    # User explicitly cancelled zenity dialog.
                    return {"status": "cancelled", "path": ""}
                else:
                    zenity_failed = True
                    logger.warning(f"zenity directory picker failed: {proc.stderr.strip()}")
            except Exception as e:
                zenity_failed = True
                logger.warning(f"zenity directory picker exception: {e}")

        if not selected and (zenity_failed or not used_zenity):
            try:
                selected = await asyncio.to_thread(_ask_directory_with_tk, initial_dir)
            except Exception as e:
                logger.warning(f"tk directory picker failed: {e}")

    selected = str(selected).strip()
    if not selected:
        return {"status": "cancelled", "path": ""}

    p = Path(selected).expanduser().resolve()
    return {"status": "ok", "path": str(p)}


def _ask_directory_with_tk(initial_dir: str) -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(title="Select Dataset Directory", initialdir=initial_dir) or ""
    root.destroy()
    return selected


@app.get("/api/client/record/episodes")
async def get_recording_files(task: Optional[str] = None, chunk: Optional[str] = None):
    """List recording task folders and parsed LeRobot episode records."""
    save_dir = str(getattr(getattr(client_state.config, 'record', None), 'save_dir', 'data/recording') or 'data/recording')
    base_dir = ROOT / save_dir.lstrip('/').lstrip('\\')

    if not base_dir.exists():
        return {
            "status": "ok",
            "base_dir": str(base_dir.relative_to(ROOT)),
            "tasks": [],
            "selected_task": "",
            "chunks": [],
            "selected_chunk": "",
            "episodes": [],
            "files": [],
        }

    tasks = []
    episodes = []
    chunk_values: list[str] = []
    selected_chunk = ""
    try:
        task_dirs = [p for p in base_dir.iterdir() if p.is_dir()]
        # Default task order: newest first by modification time (fallback by name).
        task_dirs.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
        tasks = [p.name for p in task_dirs]
        selected_task = task if task in tasks else (tasks[0] if tasks else "")

        if selected_task:
            from client.core.data_record_manager import LeRobotDatasetParser

            task_dir = base_dir / selected_task
            parser = LeRobotDatasetParser(str(task_dir), logger=logger)
            chunk_ids = parser.get_chunk_ids()
            chunk_values = [f"{x:03d}" for x in chunk_ids]
            if chunk_values:
                selected_chunk = chunk if chunk in chunk_values else chunk_values[-1]
                episodes = parser.parse_episode_records(chunk_id=int(selected_chunk))
            else:
                episodes = parser.parse_episode_records()
    except Exception as e:
        raise HTTPException(500, f"Failed to list recording files: {e}")

    return {
        "status": "ok",
        "base_dir": str(base_dir.relative_to(ROOT)),
        "tasks": tasks,
        "selected_task": selected_task,
        "chunks": chunk_values,
        "selected_chunk": selected_chunk,
        "episodes": episodes,
        "files": episodes,
    }


class RecordingEpisodeDeleteRequest(BaseModel):
    task: str
    episode_id: str


@app.delete("/api/client/record/delete")
async def delete_recording_episode(req: RecordingEpisodeDeleteRequest):
    recoding_dir = ROOT / "data" / "recoding"
    fallback_dir = ROOT / "data" / "recording"
    base_dir = recoding_dir if (recoding_dir.exists() or not fallback_dir.exists()) else fallback_dir

    if not base_dir.exists():
        raise HTTPException(404, "Recording directory does not exist.")

    task = str(req.task or "").strip()
    if not task:
        raise HTTPException(400, "Task is required.")

    task_dir = (base_dir / task).resolve()
    try:
        task_dir.relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(400, "Task path is outside recording directory.")

    if not task_dir.exists() or not task_dir.is_dir():
        raise HTTPException(404, f"Task directory not found: {task}")

    try:
        from client.core.data_record_manager import LeRobotDatasetParser

        parser = LeRobotDatasetParser(str(task_dir), logger=logger)
        result = parser.delete_episode(req.episode_id)
        if not result.get("deleted"):
            raise HTTPException(404, f"Episode not found: {req.episode_id}")
        return {"status": "ok", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete recording episode: {e}")


@app.get("/api/client/language/load/default")
async def get_default_lang_file():
    """Return the path and contents of the default language command JSON file."""
    if not DEFAULT_LANG_CMD.exists():
        raise HTTPException(404, "Default lang_cmd.json not found.")
    try:
        data = json.loads(DEFAULT_LANG_CMD.read_text(encoding="utf-8"))
        rel_path = str(DEFAULT_LANG_CMD.relative_to(ROOT))
        return {"status": "ok", "path": rel_path, "data": data}
    except Exception as e:
        raise HTTPException(400, f"Failed to parse lang_cmd.json: {e}")


class LangFileRequest(BaseModel):
    path: str


@app.post("/api/client/language/load")
async def load_lang_file(req: LangFileRequest):
    """Load a JSON language command file and return its contents."""
    # print(f"Loading language file: {req.path}")
    p = Path(req.path)
    if "conf" not in req.path:
        p = "conf" / p
    if not p.is_absolute():
        p = ROOT / p
    # Guard against path-traversal: resolved path must stay inside ROOT
    # print(f"language file path: {p}")
    try:
        p = p.resolve()
        p.relative_to(ROOT.resolve())
        # print(f"resolved path: {p}")
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")
    if not p.exists():
        raise HTTPException(404, f"File not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {"status": "ok", "data": data}
    except Exception as e:
        raise HTTPException(400, f"Failed to parse JSON: {e}")


class LangSaveRequest(BaseModel):
    path: str
    data: dict


@app.post("/api/client/language/save")
async def save_lang_file(req: LangSaveRequest):
    """Save the language command JSON file."""
    p = Path(req.path)
    if "conf" not in req.path:
        p = "conf" / p
    if not p.is_absolute():
        p = ROOT / p
    try:
        p = p.resolve()
        p.relative_to(ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(req.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "ok", "path": str(p.relative_to(ROOT))}
    except Exception as e:
        raise HTTPException(500, f"Failed to save language file: {e}")


@app.get("/api/client/config")
async def get_config():
    """Return current config as a nested dict."""
    if client_state.config is None:
        cfg = get_client_config()
        client_state.config = cfg
        # print(f"Debug: return default config")
    # print(f"DEBUG: visualize trajectory: {client_state.config.visualize.trajectory}")
    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    return {"status": "ok", "config": cfg_dict}


@app.get("/api/client/config/yaml_files")
async def list_yaml_configs():
    """List all .yaml files in the conf directory."""
    conf_dir = ROOT / "conf"
    yaml_files = []
    if conf_dir.exists():
        for f in sorted(conf_dir.glob("*.yaml")):
            yaml_files.append(f.name)
        for f in sorted(conf_dir.glob("*.yml")):
            yaml_files.append(f.name)
    return {"status": "ok", "files": yaml_files}


class ConfigPatchRequest(BaseModel):
    patch: dict   # flat dot-key → value  OR  nested dict


class VisualCameraConfigRequest(BaseModel):
    open_head: Optional[bool] = None
    open_wrist_left: Optional[bool] = None
    open_wrist_right: Optional[bool] = None

@app.post("/api/client/config/patch")
async def patch_config(req: ConfigPatchRequest):
    """Apply a partial update to in-memory config. Effective immediately when possible."""
    if client_state.config is None:
        client_state.config = get_client_config()

    # Support both nested dict and flat dot-key dict
    def _flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_flatten(v, full))
            else:
                out[full] = v
        return out

    flat = _flatten(req.patch)
    vision_preprocess_keys = []
    dataset_path_changed = False
    robot_type_changed = False
    current_vla_client = None
    current_robot = None
    is_running = False
    prev_robot_type = None
    next_robot_type = None

    acquired = client_state.lock.acquire(timeout=2.0)
    if not acquired:
        raise HTTPException(503, "Config is busy. Please retry.")
    try:
        prev_robot_type = str(getattr(getattr(client_state.config, 'robots', None), 'type', ''))
        _apply_flat_patch_new(client_state.config, flat)
        next_robot_type = str(getattr(getattr(client_state.config, 'robots', None), 'type', ''))
        cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
        current_vla_client = client_state.vla_client
        current_robot = client_state.robot
        is_running = bool(client_state.running)

        for k in flat.keys():
            if k.startswith('vision.preprocess'):
                vision_preprocess_keys.append(k)
            elif k.startswith('robots.mock.dataset_path'):
                dataset_path_changed = True
                next_dataset_path = str(flat[k]).strip()
            elif k.startswith('robots.type'):
                robot_type_changed = True
            elif k.startswith('controller.period'):
                if current_vla_client is not None:
                    current_vla_client.set_control_period(float(flat[k]))
                else:
                    pass
            elif k.startswith('controller.speed'):
                # print(f"Debug: key={k}, value={flat[k]}")
                if current_vla_client is not None:
                    current_vla_client.set_observe_period(float(flat[k]))
                else:
                    pass
            else:
                # print(f"Debug: key={k}, value={flat[k]}")
                pass
        if vision_preprocess_keys and current_vla_client is not None:
            try:
                current_vla_client.update_preprocess_func()
                logger.info(f"Updated preprocess function due to vision.preprocess config changes: {vision_preprocess_keys}")
            except Exception as e:
                logger.error(f"Failed to update preprocess function: {e}")
    finally:
        client_state.lock.release()
    if (
        robot_type_changed
        and is_running
        and current_vla_client is not None
        and prev_robot_type != next_robot_type
    ):
        try:
            with client_state.lock:
                client_state.paused_thread_state = _pause_vla_client(current_vla_client)
            await asyncio.to_thread(_ensure_config_robot_bound, True)
            logger.info(f"Robot type changed: {prev_robot_type} -> {next_robot_type}. Recreated and rebound robot instance.")
        except Exception as e:
            logger.error(f"Failed to recreate robot for type change {prev_robot_type} -> {next_robot_type}: {e}")
            raise HTTPException(500, f"Failed to recreate robot for type change: {e}")
        finally:
            with client_state.lock:
                try:
                    _resume_vla_client(current_vla_client, client_state.paused_thread_state)
                except Exception as e:
                    logger.error(f"Failed to resume client after robot recreate: {e}")

    if dataset_path_changed and not (robot_type_changed and prev_robot_type != next_robot_type):
        targets = []
        if current_robot is not None:
            targets.append(current_robot)
        if robot_instance is not None and robot_instance is not current_robot:
            targets.append(robot_instance)

        for robot in targets:
            module_name = getattr(robot.__class__, "__module__", "")
            if not module_name.endswith("client.robots.mock.body_robot"):
                continue
            if not hasattr(robot, 'reset'):
                continue
            try:
                if is_running and current_vla_client is not None and robot is current_robot:
                    with client_state.lock:
                        client_state.paused_thread_state = _pause_vla_client(current_vla_client)
                robot.reset(dataset_path=next_dataset_path or None, reload_dataset=True)
                logger.info(f"Applied mock dataset_path change: {next_dataset_path}")
            except Exception as e:
                logger.error(f"Failed to apply mock dataset_path change '{next_dataset_path}': {e}")
                raise HTTPException(500, f"Failed to reload mock dataset: {e}")
            finally:
                with client_state.lock:
                    try:
                        _resume_vla_client(current_vla_client, client_state.paused_thread_state)
                    except Exception as e:
                        logger.error(f"Failed to resume client after dataset reload: {e}")

    return {"status": "ok", "config": cfg_dict}



@app.post("/api/client/config/load")
async def load_config_file(req: ConfigFileRequest):
    """Load a yaml conf file and apply it. Effective immediately when possible."""
    # Guard against path-traversal
    p = Path(req.path)
    # print(f"DEBUG: Logger name is: {logger.name}")
    # print(f"DEBUG: Logger effective level is: {logger.getEffectiveLevel()}")
    # print(f"DEBUG: Logging module root level is: {logging.root.getEffectiveLevel()}")
    if not p.is_absolute():
        p = ROOT / "conf" / p
    try:
        p.resolve().relative_to(ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")

    current_vla_client = None
    is_running = False
    prev_robot_type = None
    next_robot_type = None

    with client_state.lock:
        prev_robot_type = str(getattr(getattr(client_state.config, 'robots', None), 'type', ''))
        _apply_yaml_config(client_state.config, p)
        next_robot_type = str(getattr(getattr(client_state.config, 'robots', None), 'type', ''))
        current_vla_client = client_state.vla_client
        is_running = bool(client_state.running)

    if (
        is_running
        and current_vla_client is not None
        and prev_robot_type != next_robot_type
    ):
        try:
            with client_state.lock:
                client_state.paused_thread_state = _pause_vla_client(current_vla_client)
            await asyncio.to_thread(_ensure_config_robot_bound, True)
            logger.info(f"Robot type changed by config load: {prev_robot_type} -> {next_robot_type}. Recreated and rebound robot instance.")
        finally:
            with client_state.lock:
                try:
                    await asyncio.to_thread(_resume_vla_client, current_vla_client, client_state.paused_thread_state)
                except Exception as e:
                    logger.error(f"Failed to resume client after config-load robot recreate: {e}")

    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    return {"status": "ok", "config": cfg_dict}


@app.post("/api/client/config/save")
async def save_config_file(req: ConfigFileRequest):
    """Save current in-memory config to a file.

    Supported formats (determined by file extension):
      .yaml / .yml  →  YAML  (via _dict_to_user_conf_yaml)
    """
    if client_state.config is None:
        raise HTTPException(400, "No config loaded.")
    # print(f"DEBUG: save path = {req.path}")
    save_path = Path(req.path)
    if not save_path.is_absolute():
        save_path = ROOT / 'conf' / save_path
    # Guard against path-traversal: resolved path must stay inside ROOT
    try:
        save_path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")
    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    if save_path.suffix in (".yaml", ".yml"):
        content = _dict_to_user_conf_yaml(cfg_dict)
    else:
        content = _dict_to_user_conf_py(cfg_dict)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(content, encoding="utf-8")
    return {"status": "ok", "path": str(save_path)}


def _apply_yaml_config(config, yaml_conf_path: Path):
    """Read yaml conf file and apply flat/nested overrides onto config (best-effort)."""
    if not _HAS_YAML:
        # Fallback: simple line-by-line key: value parser (no nested support)
        text = yaml_conf_path.read_text(encoding="utf-8")
        patch = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line and not line.startswith('-'):
                k, _, v = line.partition(':')
                k = k.strip(); v = v.strip()
                if v and not v.startswith('#'):
                    patch[k] = v
        _apply_flat_patch_new(config, patch)
        return

    text = yaml_conf_path.read_text(encoding="utf-8")
    data = _yaml.safe_load(text)
    if not isinstance(data, dict):
        return

    def _flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_flatten(v, full))
            else:
                out[full] = v
        return out

    flat = _flatten(data)
    # print(f"config patch: {flat}")
    # cam_head = config.record.lerobot.features.get('cam.head')
    # print(f"config before flat patch: {config.record.lerobot.features.keys()}")
    # print(f"config before flat patch: {cam_head}")
    _apply_flat_patch_new(config, flat)
    # print(f"config after flat patch: {config}")
    # print(f"config after flat patch: {config.record.lerobot.features.keys()}")
    # print(f"config after flat patch: {cam_head}")
    config.language.sub_task_id = 0  # reset sub_task_id to avoid invalid value after patch
    logger.info(f"Load and apply yaml config overrides from {yaml_conf_path}")


def _dict_to_user_conf_py(d: dict, indent=0) -> str:
    """Convert a nested dict to a user_conf.py source string."""
    lines = []
    if indent == 0:
        lines.append('"""Auto-generated user configuration."""\n')
        lines.append("def get_user_config():")
        lines.append("    return " + _fmt_dict(d, indent=1))
    return "\n".join(lines) + "\n"


def _fmt_dict(d: dict, indent: int) -> str:
    sp = "    " * indent
    sp1 = "    " * (indent + 1)
    if not d:
        return "{}"
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            items.append(f"{sp1}{repr(k)}: {_fmt_dict(v, indent+1)}")
        elif isinstance(v, list):
            inner = ", ".join(repr(x) for x in v)
            items.append(f"{sp1}{repr(k)}: [{inner}]")
        else:
            items.append(f"{sp1}{repr(k)}: {repr(v)}")
    return "{\n" + ",\n".join(items) + f",\n{sp}}}"


def _dict_to_user_conf_yaml(d: dict) -> str:
    """Convert a nested dict to a YAML config string.

    Uses PyYAML when available; falls back to a simple manual serializer
    that handles the nested dicts produced by _config_to_dict.
    """
    if _HAS_YAML:
        header = (
            "# VLA-RAIL Client Configuration\n"
            "# Auto-generated — edit values as needed\n\n"
        )
        return header + _yaml.dump(
            d,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    # ── fallback: manual serializer ──────────────────────────────────────────
    lines = [
        "# VLA-RAIL Client Configuration",
        "# Auto-generated — edit values as needed",
        "",
    ]

    def _emit(obj, indent: int):
        sp = "  " * indent
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict):
                    lines.append(f"{sp}{k}:")
                    _emit(v, indent + 1)
                elif isinstance(v, list):
                    lines.append(f"{sp}{k}:")
                    for item in v:
                        lines.append(f"{sp}  - {_yaml_scalar(item)}")
                else:
                    lines.append(f"{sp}{k}: {_yaml_scalar(v)}")

    def _yaml_scalar(v) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        # Quote strings that could be misread by YAML parsers
        if any(c in s for c in (':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`')):
            return f'"{s}"'
        return s

    _emit(d, 0)
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
#  REST: client control
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_vla_client_created():
    with client_state.lock:
        if client_state.vla_client is not None:
            return client_state.vla_client

    # TODO: Load config from yaml file
    if client_state.config is None:
        client_state.config = get_client_config()
    client_config = client_state.config

    robot_config = getattr(client_config.robots, client_config.robots.type.value, None)
    _sync_robot_action_layout(client_config, robot_config)

    vla_zmq_client = None
    robot = RobotBase(robot_config)
    try:
        vla_zmq_client = ZMQClient(client_config.vla_zmq)
        realtime_data_manager = RealtimeDataManager(client_config.rdm)
        inter_chunk_fuser = InterChunkFuser(config=client_config.inter_chunk)
        intra_chunk_smoother = IntraChunkSmoother(config=client_config.intra_chunk)
        task_language_manager = TaskLanguageManager(config=client_config.language)

        from client.core.vla_client import VLAClientAsync
        vla_client = VLAClientAsync(
            config=client_config,
            realtime_data_manager=realtime_data_manager,
            inter_chunk_fuser=inter_chunk_fuser,
            intra_chunk_smoother=intra_chunk_smoother,
            task_language_manager=task_language_manager,
            vla_zmq_client=vla_zmq_client,
            robot=robot,
        )
    except Exception:
        if vla_zmq_client is not None:
            try:
                vla_zmq_client.close()
            except Exception:
                pass
        raise

    with client_state.lock:
        client_state.vla_client = vla_client
        client_state.robot = robot
    return vla_client


async def _start_client():
    loop = asyncio.get_running_loop()
    client_state._loop = loop

    try:
        await asyncio.to_thread(_ensure_vla_client_created)
        await asyncio.to_thread(_ensure_config_robot_bound)
        vla_client = client_state.vla_client
    except Exception as e:
        err = traceback.format_exc()
        logger.error(f"Client init error:\n{err}")
        with client_state.lock:
            client_state.running = False
            client_state.vla_client = None
            client_state.robot = None
            client_state.paused_thread_state = None
            client_state.starting = False
        await _broadcast_to_web({"type": "error", "data": {"message": f"Failed to initialize client: {e}", "trace": err}})
        return

    with client_state.lock:
        client_state.starting = False
        if client_state.stopping:
            logger.warning("Client start aborted because stop was requested during initialization.")
            try:
                vla_client.close()
            except Exception:
                pass
            client_state.vla_client = None
            client_state.robot = None
            return
        if client_state.running:
            return
        client_state.running = True

    def _run_in_thread():
        try:
            vla_client.start()
            asyncio.run_coroutine_threadsafe(
                _broadcast_to_web({"type": "status", "data": {"running": True, "paused": False, "message": "Client started."}}),
                loop
            )

            while client_state.running:
                time.sleep(1.0)

        except Exception as e:
            err = traceback.format_exc()
            logger.error(f"Client thread error:\n{err}")
            client_state.running = False
            asyncio.run_coroutine_threadsafe(
                _broadcast_to_web({"type": "error", "data": {"message": str(e), "trace": err}}),
                loop
            )
        finally:
            with client_state.lock:
                stopping_flag = bool(getattr(client_state, "stopping", False))
            # If an external stop was requested (via /api/client/stop), the
            # background stopper will perform cleanup. In that case avoid
            # running `_cleanup` here to prevent duplicate attempts.
            if not stopping_flag:
                _cleanup()
            else:
                logger.debug("Worker thread exiting: external stop will run cleanup.")

            with client_state.lock:
                if client_state.worker_thread is threading.current_thread():
                    client_state.worker_thread = None

    t = threading.Thread(target=_run_in_thread, daemon=True, name="vla-client")
    with client_state.lock:
        client_state.worker_thread = t
    t.start()


@app.post("/api/client/start")
async def start_client():
    """Create vla_client if needed, then run it in worker thread (non-blocking)."""
    with client_state.lock:
        if client_state.running:
            return {"status": "ok", "message": "Client already started."}
        if getattr(client_state, "stopping", False):
            return {"status": "ok", "message": "Client is stopping. Please retry shortly."}
        if getattr(client_state, "starting", False):
            return {"status": "ok", "message": "Client is already starting."}
        client_state.starting = True

    asyncio.create_task(_start_client())
    return {"status": "ok", "message": "Client starting…"}


def _thread_state(vla_client) -> dict:
    state = {
        "observe_running": bool(getattr(vla_client, "is_observe_thread_running", False)),
        "inference_running": bool(getattr(vla_client, "is_inference_thread_running", False)),
        "control_running": bool(getattr(vla_client, "is_control_thread_running", False)),
    }
    # print(f"_thread_state detected thread states: {state}")
    return state


def _status_payload(vla_client, message: str, running: bool = True, paused: bool = True) -> dict:
    state = _thread_state(vla_client)
    status = {
        "running": running,
        "paused": paused,
        "message": message,
    }
    status.update(state)
    return status

def _status_abnormal(message: str,
                    running: bool = False,
                    paused: bool = False,
                    observe_running: bool = False,
                    inference_running: bool = False,
                    control_running: bool = False) -> dict:
    return {
        "running": running,
        "paused": paused,
        "observe_running": observe_running,
        "inference_running": inference_running,
        "control_running": control_running,
        "message": message,
    }


def _start_observe(vla_client):
    if hasattr(vla_client, "start_observe"):
        vla_client.start_observe()
    elif hasattr(vla_client, "start_observe_thread"):
        vla_client.start_observe_thread()

    if hasattr(vla_client, "start_visualize"):
        vla_client.start_visualize()


def _stop_observe(vla_client):
    if hasattr(vla_client, "stop_observe"):
        vla_client.stop_observe()
    elif hasattr(vla_client, "is_observe_thread_running"):
        vla_client.is_observe_thread_running = False


def _start_inference(vla_client):
    if hasattr(vla_client, "start_inference"):
        vla_client.start_inference()
    elif hasattr(vla_client, "start_inference_thread"):
        vla_client.start_inference_thread()


def _stop_inference(vla_client):
    if hasattr(vla_client, "stop_inference"):
        vla_client.stop_inference()
    elif hasattr(vla_client, "is_inference_thread_running"):
        vla_client.is_inference_thread_running = False


def _start_control(vla_client):
    if hasattr(vla_client, "start_control"):
        vla_client.start_control()
    elif hasattr(vla_client, "start_control_thread"):
        vla_client.start_control_thread()


def _stop_control(vla_client):
    if hasattr(vla_client, "stop_control"):
        vla_client.stop_control()
    elif hasattr(vla_client, "is_control_thread_running"):
        vla_client.is_control_thread_running = False


def _pause_vla_client(vla_client) -> dict:
    # 获取线程状态
    state = _thread_state(vla_client)
    # print(f"_pause_vla_client with state: {state}")
    if state.get("observe_running", False):
        _stop_observe(vla_client)
    if state.get("inference_running", False):
        _stop_inference(vla_client)
    if state.get("control_running", False):
        _stop_control(vla_client)
    return state


def _resume_vla_client(vla_client, state: Optional[dict] = None):
    # if state is None:
    #     state = {
    #         "observe_running": True,
    #         "inference_running": True,
    #         "control_running": True,
    #     }
    # print(f"_resume_vla_client with state: {state}")
    if hasattr(vla_client, "is_observe_thread_running") and hasattr(vla_client, "is_inference_thread_running") and hasattr(vla_client, "is_control_thread_running"):
        if state.get("observe_running", False):
            _start_observe(vla_client)

        if state.get("inference_running", False):
            _start_inference(vla_client)

        if state.get("control_running", False):
            _start_control(vla_client)
        return

# Background helpers to avoid blocking the asyncio thread
async def _bg_pause_and_broadcast(vla_client):
    try:
        paused_state = await asyncio.to_thread(_pause_vla_client, vla_client)
        with client_state.lock:
            client_state.paused_thread_state = paused_state
            client_state.paused = True
        await _broadcast_to_web({"type": "status", "data": _status_payload(vla_client, "Client paused.", running=True, paused=True)})
    except Exception as e:
        logger.warning(f"_bg_pause_and_broadcast failed: {e}")


async def _bg_resume_and_broadcast(vla_client):
    try:
        with client_state.lock:
            restore_state = client_state.paused_thread_state
            client_state.paused_thread_state = None
        await asyncio.to_thread(_resume_vla_client, vla_client, restore_state)
        with client_state.lock:
            client_state.paused = False
        await _broadcast_to_web({"type": "status", "data": _status_payload(vla_client, "Client resumed.", running=True, paused=False)})
    except Exception as e:
        logger.warning(f"_bg_resume_and_broadcast failed: {e}")


async def _bg_toggle_observe_and_broadcast():
    try:
        await asyncio.to_thread(_ensure_vla_client_created)
        vla_client = client_state.vla_client
        if vla_client == None:
            with client_state.lock:
                client_state.running = False
            result = _status_abnormal(message='VLA Client instance is None.',
                                    running=False,
                                    paused=False,
                                    observe_running=False,
                                    inference_running=False,
                                    control_running=False,
                                    )
            await _broadcast_to_web({"type": "status", "data": result})
            raise HTTPException(400, "Client is none.")
        
        with client_state.lock:
            client_state.running = True
            client_state.paused_thread_state = None
            client_state.paused = False
        # Stop
        if bool(getattr(vla_client, "is_observe_thread_running", False)):
            await asyncio.to_thread(_stop_control,   vla_client)
            await asyncio.to_thread(_stop_inference, vla_client)
            await asyncio.to_thread(_stop_observe,   vla_client)
            message = "Observe stopped."
        # Start
        else:
            await asyncio.to_thread(_ensure_config_robot_bound)
            vla_client = client_state.vla_client
            await asyncio.to_thread(_start_observe, vla_client)
            message = "Observe started."

        payload = _status_payload(vla_client, message, running=True, paused=False)
        await _broadcast_to_web({"type": "status", "data": payload})
    except Exception as e:
        logger.warning(f"_bg_toggle_observe_and_broadcast failed: {e}")


async def _bg_toggle_infer_and_broadcast(vla_client):
    try:
        with client_state.lock:
            client_state.paused_thread_state = None
            client_state.paused = False

        if bool(getattr(vla_client, "is_inference_thread_running", False)):
            await asyncio.to_thread(_stop_control, vla_client)
            await asyncio.to_thread(_stop_inference, vla_client)
            message = "Inference stopped."
        else:
            await asyncio.to_thread(_start_inference, vla_client)
            message = "Inference started."

        payload = _status_payload(vla_client, message, running=True, paused=False)
        await _broadcast_to_web({"type": "status", "data": payload})
    except Exception as e:
        logger.warning(f"_bg_toggle_infer_and_broadcast failed: {e}")


async def _bg_toggle_control_and_broadcast(vla_client):
    try:
        with client_state.lock:
            client_state.paused_thread_state = None
            client_state.paused = False

        if bool(getattr(vla_client, "is_control_thread_running", False)):
            await asyncio.to_thread(_stop_control, vla_client)
            message = "Control stopped."
        else:
            await asyncio.to_thread(_start_control, vla_client)
            message = "Control started."

        payload = _status_payload(vla_client, message, running=True, paused=False)
        await _broadcast_to_web({"type": "status", "data": payload})
    except Exception as e:
        logger.warning(f"_bg_toggle_control_and_broadcast failed: {e}")


@app.post("/api/client/pause")
async def pause_client():
    """Pause observe/inference/control without releasing resources."""
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")

    asyncio.create_task(_bg_pause_and_broadcast(vla_client))
    return {"status": "ok", "message": "Pausing scheduled."}


@app.post("/api/client/resume")
async def resume_client():
    """Resume observe/inference/control to the exact state before pause."""
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")

    asyncio.create_task(_bg_resume_and_broadcast(vla_client))
    return {"status": "ok", "message": "Resume scheduled."}


@app.post("/api/client/observe/start")
async def start_observe_only():
    asyncio.create_task(_bg_toggle_observe_and_broadcast())
    return {"status": "ok", "message": "Observe toggle scheduled."}


@app.post("/api/client/infer/start")
async def start_infer_only():
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")
    if not bool(getattr(vla_client, "is_observe_thread_running", False)):
        raise HTTPException(400, "Observe is not running. Start Observe first.")

    asyncio.create_task(_bg_toggle_infer_and_broadcast(vla_client))
    return {"status": "ok", "message": "Inference toggle scheduled."}


@app.post("/api/client/control/start")
async def start_control_only():
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")
    if not bool(getattr(vla_client, "is_observe_thread_running", False)):
        raise HTTPException(400, "Observe is not running. Start Observe first.")
    if not bool(getattr(vla_client, "is_inference_thread_running", False)):
        raise HTTPException(400, "Inference is not running. Start Infer first.")

    asyncio.create_task(_bg_toggle_control_and_broadcast(vla_client))
    return {"status": "ok", "message": "Control toggle scheduled."}


@app.post("/api/client/stop")
async def stop_client():
    """Stop client quickly; release heavy native resources in background."""
    with client_state.lock:
        is_active = client_state.running or (client_state.vla_client is not None) or getattr(client_state, "starting", False)
        client_state.running = False
        client_state.paused_thread_state = None
        client_state.stopping = bool(is_active)

    if not is_active:
        print(f"Debug: stop_client called but client is not active (running={client_state.running}, starting={getattr(client_state, 'starting', False)})")
        raise HTTPException(400, "Client is not running.")

    asyncio.create_task(_stop_cleanup_background())
    await _broadcast_to_web({"type": "status", "data": {"running": False, "paused": False, "message": "Client stopping."}})
    return {"status": "ok"}

async def _stop_cleanup_background():
    try:
        await asyncio.to_thread(_join_worker_thread, 5.0)
        await asyncio.to_thread(_cleanup)
        await _broadcast_to_web({"type": "status", "data": {"running": False, "paused": False, "message": "Client stopped."}})
    finally:
        with client_state.lock:
            client_state.stopping = False


def _join_worker_thread(timeout_s: float = 5.0):
    with client_state.lock:
        worker = client_state.worker_thread

    if worker is None:
        return "no_worker"

    if worker is threading.current_thread():
        return "no_worker"

    worker.join(timeout=max(0.1, float(timeout_s)))
    if worker.is_alive():
        logger.warning("VLA worker thread is still alive after join timeout.")
        return "still_alive"
    else:
        with client_state.lock:
            if client_state.worker_thread is worker:
                client_state.worker_thread = None
        return "joined_dead"


def _shutdown_stop_if_running():
    """On Ctrl-C shutdown, mimic stop command before final cleanup."""
    with client_state.lock:
        vla_client = client_state.vla_client
        running = bool(client_state.running and vla_client is not None)
        client_state.running = False
        client_state.paused_thread_state = None

    if running and vla_client is not None:
        logger.info("Client is running during shutdown; execute stop sequence first.")
        try:
            _pause_vla_client(vla_client)
        except Exception:
            logger.debug("Failed to pause client during shutdown stop sequence.", exc_info=True)

    _join_worker_thread(timeout_s=5.0)


def _has_alive_vla_threads(vla_client) -> bool:
    if vla_client is None:
        return False

    for name in ("observe_thread", "inference_thread", "data_write_thread"):
        t = getattr(vla_client, name, None)
        if t is not None and hasattr(t, "is_alive") and t.is_alive():
            return True

    for timer_name in ("control_thread_timer", "visualize_thread_timer"):
        timer = getattr(vla_client, timer_name, None)
        if timer is not None and hasattr(timer, "is_alive") and timer.is_alive():
            return True

    return False


def _cleanup(force_release_robot: bool = False, skip_robot_close_if_threads_alive: bool = True):
    global robot_instance

    if not _cleanup_guard.acquire(blocking=False):
        return

    try:
        with client_state.lock:
            vla_client = client_state.vla_client
            robot = client_state.robot
            # client_state.vla_client = None
            # client_state.robot = None
            client_state.running = False
            client_state.paused_thread_state = None
            client_state.stopping = False

        if vla_client is not None:
            try:
                vla_client.stop()
            except Exception:
                pass
        # TODO: robot should be reset.
        threads_alive = _has_alive_vla_threads(vla_client)
        # print(f"Debug: vla_client threads alive={threads_alive}")

        keep_robot_alive = False
        if robot is not None and not force_release_robot:
            module_name = getattr(robot.__class__, "__module__", "")
            keep_robot_alive = (
                module_name.endswith("client.robots.a2d.body_robot")
                or module_name.endswith("client.robots.navi_wa2.body_robot")
            )
            # print(f"Debug: keep_robot_alive={keep_robot_alive}")

        if robot is not None and not keep_robot_alive:
            should_close_robot = not (skip_robot_close_if_threads_alive and threads_alive)
            # print(f"Debug: should_close_robot={should_close_robot}")
            if should_close_robot:
                try:
                    robot.close()
                except Exception:
                    pass
            else:
                logger.warning("Skip robot.close(): VLA worker threads are still alive during shutdown.")
                keep_robot_alive = True

        if keep_robot_alive:
            robot_instance = robot
        elif robot_instance is robot:
            robot_instance = None
            # print(f"Debug: Robot instance was destroyed.")

        # On process shutdown, client_state.robot may already be None while a reused
        # robot instance is still cached globally. Ensure it is released as well.
        if force_release_robot and robot_instance is not None:
            should_close_cached_robot = not (skip_robot_close_if_threads_alive and threads_alive)
            if should_close_cached_robot:
                try:
                    robot_instance.close()
                except Exception:
                    pass
                robot_instance = None
            else:
                logger.warning("Skip cached robot.close(): VLA worker threads are still alive during shutdown.")
    finally:
        _cleanup_guard.release()


@app.get("/api/client/status")
async def client_status():
    stats = await asyncio.to_thread(_collect_stats)
    # print(f"Debug: {stats}")
    return {"status": "ok", "data": stats}


# ─────────────────────────────────────────────────────────────────────────────
#  REST: runtime controls
# ─────────────────────────────────────────────────────────────────────────────
class ManualControlRequest(BaseModel):
    source: str = "manual"
    l_arm: Optional[list[float]] = None
    r_arm: Optional[list[float]] = None
    l_gripper: Optional[list[float]] = None
    r_gripper: Optional[list[float]] = None
    l_hand: Optional[list[float]] = None
    r_hand: Optional[list[float]] = None
    l_hand_as_gripper: Optional[list[float]] = None
    r_hand_as_gripper: Optional[list[float]] = None
    head: Optional[list[float]] = None
    waist: Optional[list[float]] = None
    body: Optional[list[float]] = None
    wheel: Optional[list[float]] = None
    leg: Optional[list[float]] = None


class LanguageSetRequest(BaseModel):
    language: str = ""


class RecordStartRequest(BaseModel):
    save_items: Optional[list[str]] = None


def _require_runtime(command_name: str):
    vla_client = client_state.vla_client
    robot = client_state.robot
    if vla_client is None:
        raise HTTPException(400, f"Client is None. Bad request: {command_name}")
    if robot is None:
        raise HTTPException(400, f"Robot is None. Bad request: {command_name}")
    return vla_client, robot


async def _run_web_control(command: str, req: ManualControlRequest):
    _, robot = _require_runtime(command)
    if robot.current_state is None:
        raise HTTPException(400, 'Current robot state is unavailable. Start observation first.')
    data = {
        name: value for name, value in vars(req).items()
        if value is not None
    }
    try:
        await asyncio.to_thread(robot._control_robot, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    return {"status": "ok", "command": command}


@app.post('/api/client/control/reset')
async def client_control_reset():
    vla_client, robot = _require_runtime('reset')
    try:
        with client_state.lock:
            # state = _thread_state(vla_client)
            # if state.get("observe_running", False) and state.get("inference_running", False) and state.get("control_running", False):
            # print(f"DEBUG: client state running: {client_state.running}")
            if not client_state.paused:
                client_state.paused_thread_state = _pause_vla_client(vla_client)
                client_state.paused = True
        robot.reset_robot(mode='default')
        vla_client.realtime_data_manager.clear()
        vla_client.reset()
        # _resume_vla_client(vla_client, paused_state)
        await _broadcast_to_web({"type": "status", "data": {"running": client_state.running, "paused": client_state.paused, "message": "Robot reset complete, client paused."}})
        return {"status": "ok", "command": 'reset'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post('/api/client/control/arm')
async def client_control_arm(req: ManualControlRequest):
    return await _run_web_control('arm', req)


@app.post('/api/client/control/gripper')
async def client_control_gripper(req: ManualControlRequest):
    return await _run_web_control('gripper', req)


@app.post('/api/client/control/head')
@app.post('/api/client/control/waist')
@app.post('/api/client/control/body')
async def client_control_body(req: ManualControlRequest):
    return await _run_web_control('body', req)


@app.post('/api/client/control/wheel')
async def client_control_wheel(req: ManualControlRequest):
    return await _run_web_control('wheel', req)


@app.post('/api/client/language/set')
async def client_language_set(req: LanguageSetRequest):
    vla_client, _ = _require_runtime('set_language')
    try:
        with client_state.lock:
            client_state.paused_thread_state = _pause_vla_client(vla_client)
        vla_client.task_language_manager.currt_language_instruction = req.language if isinstance(req.language, str) else ''
        with client_state.lock:
            _resume_vla_client(vla_client, client_state.paused_thread_state)
        return {"status": "ok", "command": 'set_language'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))



@app.post('/api/client/record/start')
async def client_record_start(req: RecordStartRequest):
    vla_client, _ = _require_runtime('start_recording')
    try:
        save_items = req.save_items if isinstance(req.save_items, list) else []
        client_state.config.record.switch = True
        client_state.config.record.record_exp_data = ('ExpData' in save_items)
        task_id = getattr(getattr(client_state.config, 'language', None), 'task_id', None)
        if not hasattr(vla_client, 'data_record_manager') or vla_client.data_record_manager is None:
            try:
                from client.core.data_record_manager import DataRecordManager
                vla_client.data_record_manager = DataRecordManager(record_config=client_state.config.record)
                vla_client.data_record_manager.set_task(task_id)
            except Exception as e:
                raise HTTPException(500, f'Failed to initialize recorder: {e}')
        else:
            vla_client.data_record_manager.set_task(task_id)

        updated_camera_shapes = {}
        if not bool(getattr(client_state.config.record, 'resize', False)):
            try:
                updated_camera_shapes = vla_client.update_camera_shape()
            except Exception as e:
                logger.warning(f'Failed to update camera shapes before start_recording: {e}')

        vla_client.data_record_manager.start_recording()
        current_recording_task = str(getattr(vla_client.data_record_manager, 'current_task', '') or '')
        current_recording_dir = ''
        try:
            save_path = str(getattr(vla_client.data_record_manager, 'save_path', '') or '')
            if save_path:
                current_recording_dir = Path(save_path).name
        except Exception:
            current_recording_dir = ''
        return {
            'status': 'ok',
            'command': 'start_recording',
            'recording_task': current_recording_task,
            'recording_task_dir': current_recording_dir,
            'updated_camera_shapes': updated_camera_shapes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post('/api/client/record/stop')
async def client_record_stop():
    vla_client, _ = _require_runtime('stop_recording')
    try:
        if not hasattr(vla_client, 'data_record_manager') or vla_client.data_record_manager is None:
            raise HTTPException(400, 'Recorder is not initialized.')
        client_state.config.record.switch = False
        vla_client.data_record_manager.stop_recording()
        return {'status': 'ok', 'command': 'stop_recording'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket endpoint  ws://host:9000/ws
# ─────────────────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    with client_state.ws_lock:
        client_state.ws_clients.add(ws)

    # Push current client_state immediately on connect
    try:
        stats = await asyncio.to_thread(_collect_stats)
        await ws.send_text(json.dumps({"type": "stats", "data": stats}))
    except (WebSocketDisconnect, asyncio.CancelledError, RuntimeError) as e:
        logger.debug(f"WS initial send failed: {e}")
        return
    except Exception as e:
        logger.debug(f"WS initial send failed: {e}")
        return

    try:
        while True:
            # Keep connection alive; client may send ping
            text = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            try:
                msg = json.loads(text)
                if msg.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        logger.debug(f"WS error: {e}")
    finally:
        with client_state.ws_lock:
            client_state.ws_clients.discard(ws)


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "web_client.server:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        log_level="info",
    )
