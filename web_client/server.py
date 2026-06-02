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
import logging.config
import shutil
import subprocess
import sys
import threading
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from client.core import inter_chunk_fuser

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
from client.utils.util import load_user_config, apply_user_config

logger = logging.getLogger(__name__)

# ── FastAPI app ──────────────────────────────────────────────────────────────
# lifespan replaces the deprecated @app.on_event("startup"/"shutdown") pattern.
# The context manager is defined inline here; module-level globals (client_state, etc.)
# are accessible at call-time (not at definition time), so forward-use is safe.
@asynccontextmanager
async def _lifespan(_: FastAPI):
    # ── startup ──
    setup_logging("client.log")
    client_state.config = get_client_config()
    # print(f"Initial client config: {client_state.config}")
    if DEFAULT_YAML.exists():
        try:
            _apply_yaml_config(client_state.config, DEFAULT_YAML)
        except Exception as e:
            logger.warning(f"Failed to apply yaml conf: {e}")
    # print(f"Final client config: {client_state.config}")
    asyncio.create_task(_stats_push_loop())
    logger.info("VLA Web Client server started on http://localhost:9000")
    yield
    # ── shutdown ──
    if client_state.running:
        _cleanup()

app = FastAPI(title="VLA Web Client", version="1.0.0", lifespan=_lifespan)

STATIC_DIR  = Path(__file__).parent / "static"
VISUAL_DIR  = ROOT / "visual"

# Default config files bundled with the project
DEFAULT_YAML     = ROOT / "conf" / "default_conf.yaml"
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
        self.running = False
        self.lock = threading.Lock()
        self.ws_clients: set[WebSocket] = set()
        self.ws_lock = threading.Lock()
        self._broadcast_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.paused_thread_state: Optional[dict] = None

client_state = ClientState()

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
    """Normalize legacy nested record.info.features.cam.* into dotted cam.* keys."""
    if not isinstance(cfg_dict, dict):
        return cfg_dict

    features = (
        cfg_dict.get("record", {})
        .get("info", {})
        .get("features", {})
    )
    if isinstance(features, dict):
        cam = features.get("cam")
        if isinstance(cam, dict):
            features.pop("cam", None)
            for cam_key, cam_val in cam.items():
                features[f"cam.{cam_key}"] = cam_val
    return cfg_dict


def _apply_flat_patch_old(config, patch: dict):
    """Apply a flat {dot.separated.key: value} patch to config."""
    from ml_collections import ConfigDict

    def _set_nested(obj, keys, value):
        for k in keys[:-1]:
            # Use getattr with a sentinel to avoid falsy-value short-circuit
            _sentinel = object()
            attr = getattr(obj, k, _sentinel)
            obj = obj[k] if attr is _sentinel else attr
        leaf_key = keys[-1]
        current = getattr(obj, leaf_key, None)
        # Enum coercion
        if current is not None and hasattr(current, '__class__') and hasattr(current.__class__, '__bases__'):
            if any('Enum' in str(b) for b in current.__class__.__bases__):
                ec = current.__class__
                try:
                    value = ec(value)
                except Exception:
                    pass
        setattr(obj, leaf_key, value)

    for dotkey, value in patch.items():
        keys = dotkey.split('.')
        try:
            _set_nested(config, keys, value)
        except Exception as e:
            logger.warning(f"Failed to patch config key '{dotkey}': {e}")

def _apply_flat_patch_new(config, patch: dict):
    """Apply flat patch only to existing config leaf keys (no new key creation)."""
    import enum
    from ml_collections import ConfigDict

    if not isinstance(patch, dict) or config is None:
        return

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
# 建议放在 _get_robot 函数定义的上方
robot_instance = None

def _get_robot(config):
    global robot_instance
    if robot_instance is not None:
        logger.info("Robot instance already exists, reusing it.")
        return robot_instance
    if config.robots.type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        robot_instance = RobotBody(config)
    elif config.robots.type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        robot_instance = RobotBody(config)
    else:
        raise ValueError(f"Unsupported robot type: {config.robots.type}")
    return robot_instance


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket broadcast
# ─────────────────────────────────────────────────────────────────────────────
async def _broadcast(message: dict):
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
            stats = _collect_stats()
            await _broadcast({"type": "stats", "data": stats})
        except Exception as e:
            logger.debug(f"stats push error: {e}")


def _is_vla_client_paused(vla_client) -> bool:
    """Return explicit pause state triggered by /api/client/pause."""
    with client_state.lock:
        return bool(client_state.running and (client_state.paused_thread_state is not None))


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
        "avg_traj_time": 0.0,
        "language": "",
        "current_state": [],
        "current_action": [],
        "info_obs": {},
        "info_act": {},
        "debug_info": "",
        "config_snapshot": {},
        "cpu_usage": None,
        "gpu_usage": None,
        "mem_usage": None,
        "bandwidth_m": None,
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
        base["infer_count"]     = int(vla_client.rdm.infer_count)
        base["avg_infer_time"]  = float(vla_client.rdm.avg_infer_time)
        base["avg_traj_time"]   = float(vla_client.rdm.avg_traj_time)
        base["language"]        = str(vla_client.language)
        base["current_state"]   = [round(float(x), 4) for x in vla_client.info_current_state]
        base["current_action"]  = [round(float(x), 4) for x in vla_client.info_current_action]
        base["info_obs"]        = {k: str(v) for k, v in vla_client.info_obs.items()}
        base["info_act"]        = {k: str(v) for k, v in vla_client.info_act.items()}
        try:
            base["current_prob_progress"] = float(vla_client.info_act.get("current_prob_progress", 0.0))
        except Exception:
            base["current_prob_progress"] = 0.0
        base["debug_info"]      = str(vla_client.debug_info)
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
        base["debug_info"] = f"stats error: {e}"
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
@app.get("/api/conf_dir")
async def get_conf_dir():
    """Return the absolute path of the project conf/ directory."""
    conf_dir = ROOT / "conf"
    return {"status": "ok", "path": str(conf_dir)}


@app.get("/api/recording/files")
async def get_recording_files():
    """List files under data/recoding by default (fallback: data/recording)."""
    recoding_dir = ROOT / "data" / "recoding"
    fallback_dir = ROOT / "data" / "recording"
    base_dir = recoding_dir if (recoding_dir.exists() or not fallback_dir.exists()) else fallback_dir

    if not base_dir.exists():
        return {"status": "ok", "base_dir": str(base_dir.relative_to(ROOT)), "files": []}

    files = []
    try:
        for p in base_dir.rglob("*"):
            if not p.is_file():
                continue
            st = p.stat()
            files.append({
                "path": str(p.relative_to(base_dir)),
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
        files.sort(key=lambda x: x["mtime"], reverse=True)
    except Exception as e:
        raise HTTPException(500, f"Failed to list recording files: {e}")

    return {"status": "ok", "base_dir": str(base_dir.relative_to(ROOT)), "files": files}


@app.get("/api/default_lang_file")
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


@app.post("/api/lang_file/load")
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


@app.get("/api/config")
async def get_config():
    """Return current config as a nested dict."""
    if client_state.config is None:
        cfg = get_client_config()
        client_state.config = cfg
    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    return {"status": "ok", "config": cfg_dict}


class ConfigPatchRequest(BaseModel):
    patch: dict   # flat dot-key → value  OR  nested dict


class VisualCameraConfigRequest(BaseModel):
    open_head: Optional[bool] = None
    open_wrist_left: Optional[bool] = None
    open_wrist_right: Optional[bool] = None


@app.post("/api/visual/camera_cfg")
async def set_visual_camera_cfg(req: VisualCameraConfigRequest):
    """Update runtime camera open config for visual websocket server (effective immediately)."""
    payload = req.dict(exclude_none=True)
    if not payload:
        return {"status": "ok", "applied": False}

    vla_client = client_state.vla_client
    ws_server = getattr(vla_client, "visualization_server", None) if vla_client is not None else None
    if ws_server is None:
        return {"status": "ok", "applied": False}

    ws_server.update_camera_open_config(payload)
    return {"status": "ok", "applied": True, "camera_cfg": payload}


@app.post("/api/config/patch")
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
    with client_state.lock:
        _apply_flat_patch_new(client_state.config, flat)

    # Runtime side-effects for keys that need explicit push
    if client_state.running and client_state.vla_client is not None:
        try:
            if any(k.startswith("visual.camera.") for k in flat.keys()):
                cam_cfg = getattr(getattr(client_state.config, "visual", None), "camera", None)
                ws_server = getattr(client_state.vla_client, "visualization_server", None)
                if ws_server is not None and cam_cfg is not None:
                    ws_server.update_camera_open_config(cam_cfg)
        except Exception as e:
            logger.warning(f"Runtime camera config sync failed: {e}")

    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    return {"status": "ok", "config": cfg_dict}


class ConfigFileRequest(BaseModel):
    path: str


@app.post("/api/config/load_file")
async def load_config_file(req: ConfigFileRequest):
    """Load a yaml conf file and apply it. Effective immediately when possible."""
    if client_state.config is None:
        client_state.config = get_client_config()
    # Guard against path-traversal
    p = Path(req.path)
    # --- 调试开始 ---
    # print(f"DEBUG: Logger name is: {logger.name}")
    # print(f"DEBUG: Logger effective level is: {logger.getEffectiveLevel()}")
    # print(f"DEBUG: Logging module root level is: {logging.root.getEffectiveLevel()}")
    # logger.info(f"Loading config from file: {p}")
    if not p.is_absolute():
        p = ROOT / "conf" / p
    try:
        p.resolve().relative_to(ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")

    with client_state.lock:
        _apply_yaml_config(client_state.config, p)

    # Runtime side-effects for configs requiring explicit push
    if client_state.running and client_state.vla_client is not None:
        try:
            cam_cfg = getattr(getattr(client_state.config, "visual", None), "camera", None)
            ws_server = getattr(client_state.vla_client, "visualization_server", None)
            if ws_server is not None and cam_cfg is not None:
                ws_server.update_camera_open_config(cam_cfg)
        except Exception as e:
            logger.warning(f"Runtime camera config sync after load failed: {e}")

    # user_cfg = load_user_config(str(p))
    # if user_cfg is None:
    #     raise HTTPException(400, f"Failed to load config from: {p}")
    # base_cfg = get_client_config()
    # client_state.config = apply_user_config(base_cfg, user_cfg)
    cfg_dict = _normalize_record_features_cam(_config_to_dict(client_state.config))
    return {"status": "ok", "config": cfg_dict}


@app.post("/api/config/save_file")
async def save_config_file(req: ConfigFileRequest):
    """Save current in-memory config to a file.

    Supported formats (determined by file extension):
      .yaml / .yml  →  YAML  (via _dict_to_user_conf_yaml)
      .py           →  Python get_user_config() module (via _dict_to_user_conf_py)
    """
    if client_state.config is None:
        raise HTTPException(400, "No config loaded.")
    save_path = Path(req.path)
    if not save_path.is_absolute():
        save_path = ROOT / save_path
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
    # cam_head = config.record.info.features.get('cam.head')
    # print(f"config before flat patch: {config.record.info.features.keys()}")
    # print(f"config before flat patch: {cam_head}")
    _apply_flat_patch_new(config, flat)
    # print(f"config after flat patch: {config}")
    # print(f"config after flat patch: {config.record.info.features.keys()}")
    # print(f"config after flat patch: {cam_head}")
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

    Uses PyYAML when available; falls back to a simple manual serialiser
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

    # ── fallback: manual serialiser ──────────────────────────────────────────
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

    cfg = client_state.config if client_state.config is not None else get_client_config()
    # print(f"Using config: {cfg}")
    client_state.config = cfg

    robot_cfg = getattr(cfg.robots, cfg.robots.type.value, None)
    if robot_cfg is not None and hasattr(robot_cfg, 'action_layout'):
        cfg.rdm.action_layout = robot_cfg.action_layout
        cfg.intra_chunk.action_layout = robot_cfg.action_layout

    vla_zmq_client = ZMQClient(cfg.vla_zmq)
    robot = _get_robot(cfg)
    rdm = RealtimeDataManager(cfg.rdm)
    inter_chunk_fuser = InterChunkFuser(config=cfg.inter_chunk)
    intra_chunk_smoother = IntraChunkSmoother(config=cfg.intra_chunk)

    if cfg.inter_chunk.inter_chunk_mode == 'sync':
        from client.core.vla_client_sync import VLAClientSync
        vla_client = VLAClientSync(config=cfg, rdm=rdm, intra_chunk_smoother=intra_chunk_smoother,
                           vla_zmq_client=vla_zmq_client, robot=robot)
    else:
        from client.core.vla_client import VLAClientAsync
        vla_client = VLAClientAsync(
            config=cfg,
            rdm=rdm,
            inter_chunk_fuser=inter_chunk_fuser,
            intra_chunk_smoother=intra_chunk_smoother,
            vla_zmq_client=vla_zmq_client,
            robot=robot)

    with client_state.lock:
        client_state.vla_client = vla_client
        client_state.robot = robot
    return vla_client


@app.post("/api/client/start")
async def start_client():
    """Create vla_client if needed, then run it in worker thread (non-blocking)."""
    loop = asyncio.get_running_loop()
    client_state._loop = loop

    vla_client = await asyncio.to_thread(_ensure_vla_client_created)

    with client_state.lock:
        if client_state.running:
            return {"status": "ok", "message": "Client already started."}
        client_state.running = True

    def _run_in_thread():
        try:
            asyncio.run_coroutine_threadsafe(
                _broadcast({"type": "status", "data": {"running": True, "message": "Client started."}}),
                loop
            )

            vla_client.run()

            while client_state.running:
                time.sleep(0.1)

        except Exception as e:
            err = traceback.format_exc()
            logger.error(f"Client thread error:\n{err}")
            client_state.running = False
            asyncio.run_coroutine_threadsafe(
                _broadcast({"type": "error", "data": {"message": str(e), "trace": err}}),
                loop
            )
        finally:
            _cleanup()

    t = threading.Thread(target=_run_in_thread, daemon=True, name="vla-client")
    t.start()
    return {"status": "ok", "message": "Client starting…"}


def _thread_state(vla_client) -> dict:
    state = {
        "observe_running": bool(getattr(vla_client, "is_observe_thread_running", False)),
        "inference_running": bool(getattr(vla_client, "is_inference_thread_running", False)),
        "control_running": bool(getattr(vla_client, "is_control_thread_running", False)),
    }
    # print(f"_thread_state detected thread states: {state}")
    return state


def _status_payload(vla_client, message: str, running: bool = True) -> dict:
    state = _thread_state(vla_client)
    paused = _is_vla_client_paused(vla_client)
    return {
        "running": running,
        "paused": paused,
        "observe_running": state["observe_running"],
        "inference_running": state["inference_running"],
        "control_running": state["control_running"],
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

@app.post("/api/client/pause")
async def pause_client():
    """Pause observe/inference/control without releasing resources."""
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")

    paused_state = _pause_vla_client(vla_client)
    with client_state.lock:
        client_state.paused_thread_state = paused_state

    await _broadcast({"type": "status", "data": _status_payload(vla_client, "Client paused.", running=True)})
    return {"status": "ok"}


@app.post("/api/client/resume")
async def resume_client():
    """Resume observe/inference/control to the exact state before pause."""
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")

    with client_state.lock:
        restore_state = client_state.paused_thread_state

    _resume_vla_client(vla_client, restore_state)

    with client_state.lock:
        client_state.paused_thread_state = None

    await _broadcast({"type": "status", "data": _status_payload(vla_client, "Client resumed.", running=True)})
    return {"status": "ok"}


@app.post("/api/client/observe/start")
async def start_observe_only():
    vla_client = await asyncio.to_thread(_ensure_vla_client_created)

    with client_state.lock:
        client_state.running = True
        client_state.paused_thread_state = None

    if bool(getattr(vla_client, "is_observe_thread_running", False)):
        _stop_control(vla_client)
        _stop_inference(vla_client)
        _stop_observe(vla_client)
        message = "Observe stopped."
    else:
        _start_observe(vla_client)
        message = "Observe started."

    payload = _status_payload(vla_client, message, running=True)
    await _broadcast({"type": "status", "data": payload})
    return {"status": "ok", "data": payload}


@app.post("/api/client/infer/start")
async def start_infer_only():
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")
    if not bool(getattr(vla_client, "is_observe_thread_running", False)):
        raise HTTPException(400, "Observe is not running. Start Observe first.")

    with client_state.lock:
        client_state.paused_thread_state = None

    if bool(getattr(vla_client, "is_inference_thread_running", False)):
        _stop_control(vla_client)
        _stop_inference(vla_client)
        message = "Inference stopped."
    else:
        _start_inference(vla_client)
        message = "Inference started."

    payload = _status_payload(vla_client, message, running=True)
    await _broadcast({"type": "status", "data": payload})
    return {"status": "ok", "data": payload}


@app.post("/api/client/control/start")
async def start_control_only():
    vla_client = client_state.vla_client
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")
    if not bool(getattr(vla_client, "is_observe_thread_running", False)):
        raise HTTPException(400, "Observe is not running. Start Observe first.")
    if not bool(getattr(vla_client, "is_inference_thread_running", False)):
        raise HTTPException(400, "Inference is not running. Start Infer first.")

    with client_state.lock:
        client_state.paused_thread_state = None

    if bool(getattr(vla_client, "is_control_thread_running", False)):
        _stop_control(vla_client)
        message = "Control stopped."
    else:
        _start_control(vla_client)
        message = "Control started."

    payload = _status_payload(vla_client, message, running=True)
    await _broadcast({"type": "status", "data": payload})
    return {"status": "ok", "data": payload}


@app.post("/api/client/stop")
async def stop_client():
    """Fully stop client threads and release all resources."""
    with client_state.lock:
        is_active = client_state.running or (client_state.vla_client is not None)
        client_state.running = False
    if not is_active:
        raise HTTPException(400, "Client is not running.")

    await asyncio.to_thread(_cleanup)
    await _broadcast({"type": "status", "data": {"running": False, "paused": False, "message": "Client stopped."}})
    return {"status": "ok"}


def _cleanup():
    global robot_instance

    with client_state.lock:
        vla_client = client_state.vla_client
        robot = client_state.robot
        client_state.vla_client = None
        client_state.robot = None
        client_state.running = False
        client_state.paused_thread_state = None

    if vla_client is not None:
        try:
            vla_client.close()
        except Exception:
            pass

    if robot is not None:
        try:
            robot.close()
        except Exception:
            pass

    if robot_instance is robot:
        robot_instance = None


@app.get("/api/client/status")
async def client_status():
    return {"status": "ok", "data": _collect_stats()}


# ─────────────────────────────────────────────────────────────────────────────
#  REST: runtime commands (replaces Enter-key menu in run_client.py)
# ─────────────────────────────────────────────────────────────────────────────
class CommandRequest(BaseModel):
    command: str          # reset / resume / set_language / start_recording / stop_recording / arm / gripper / head / waist / wheel
    params: dict = {}


@app.post("/api/client/command")
async def client_command(req: CommandRequest):
    vla_client = client_state.vla_client
    robot = client_state.robot
    if vla_client is None or not client_state.running:
        raise HTTPException(400, "Client is not running.")

    cmd = req.command
    params = req.params

    try:
        if cmd == "reset":
            # Pause first before resetting robot to initial position
            _pause_vla_client(vla_client)
            robot.reset_robot(mode='default')
            _resume_vla_client(vla_client)
            await _broadcast({"type": "status", "data": {"running": client_state.running, "paused": False, "message": "Robot reset complete, client resumed."}})

        elif cmd == "resume":
            _resume_vla_client(vla_client)
            await _broadcast({"type": "status", "data": {"running": True, "paused": False, "message": "Client resumed."}})

        elif cmd == "set_language":
            lang = params.get("language", "")
            vla_client.language = lang
            _pause_vla_client(vla_client)
            robot.reset_robot(mode='default')
            _resume_vla_client(vla_client)

        elif cmd == "start_recording":
            save_items = params.get("save_items", [])
            if not isinstance(save_items, list):
                save_items = []
            client_state.config.record.switch = True
            client_state.config.record_exp_data = ('ExpData' in save_items)
            task_id = getattr(getattr(client_state.config, "language", None), "task_id", None)
            if not hasattr(vla_client, "dataset_write") or vla_client.dataset_write is None:
                try:
                    from client.core.save_lerobot import LeRobotDatasetWriter
                    vla_client.dataset_write = LeRobotDatasetWriter(
                        record_config=client_state.config.record,
                        task=task_id,
                    )
                except Exception as e:
                    raise HTTPException(500, f"Failed to initialize recorder: {e}")
            else:
                vla_client.dataset_write.set_task(task_id)
            vla_client.dataset_write.start_recording()

        elif cmd == "stop_recording":
            if not hasattr(vla_client, "dataset_write") or vla_client.dataset_write is None:
                raise HTTPException(400, "Recorder is not initialized.")
            vla_client.dataset_write.stop_recording()
            client_state.config.record.switch = False

        elif cmd == "arm":
            pos = params.get("pos", [0.0] * 14)
            robot.execute_action({'arm': pos})

        elif cmd == "gripper":
            pos = params.get("pos", [0.0, 0.0])
            robot.execute_action({'gripper': pos})

        elif cmd == "head":
            pos = params.get("pos", [0.0, 0.436, 0.0])
            robot.execute_action({'head': pos})

        elif cmd == "waist":
            pos = params.get("pos", [0.0, 0.297, 0.0])
            robot.execute_action({'waist': pos})

        elif cmd == "wheel":
            pos = params.get("pos", [0.0, 0.0])
            robot.execute_action({'wheel': pos})

        else:
            raise HTTPException(400, f"Unknown command: {cmd}")

        return {"status": "ok", "command": cmd}

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
    await ws.send_text(json.dumps({"type": "stats", "data": _collect_stats()}))

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
