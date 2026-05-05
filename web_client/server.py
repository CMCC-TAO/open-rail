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
import sys
import threading
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

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
from conf.logging_conf import LOGGING_CONFIG
from client.core.zmq_client import ZMQClient
from client.core.trajectory_generator import TrajectoryGenerator
from client.core.realtime_data_manager import RealtimeDataManager
from client.utils.util import load_user_config, apply_user_config

logger = logging.getLogger(__name__)

# ── FastAPI app ──────────────────────────────────────────────────────────────
# lifespan replaces the deprecated @app.on_event("startup"/"shutdown") pattern.
# The context manager is defined inline here; module-level globals (state, etc.)
# are accessible at call-time (not at definition time), so forward-use is safe.
@asynccontextmanager
async def _lifespan(_: FastAPI):
    # ── startup ──
    logging.config.dictConfig(LOGGING_CONFIG)
    state.config = get_client_config()
    if DEFAULT_YAML.exists():
        try:
            _apply_yaml_config(state.config, DEFAULT_YAML)
        except Exception as e:
            logger.warning(f"Failed to apply yaml conf: {e}")
    asyncio.create_task(_stats_push_loop())
    logger.info("VLA Web Client server started on http://localhost:9000")
    yield
    # ── shutdown ──
    if state.running:
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
#  Global state
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

state = ClientState()


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

def _apply_flat_patch(config, patch: dict):
    """Apply a flat {dot.separated.key: value} patch to config."""
    from ml_collections import ConfigDict

    def _set_nested(obj, keys, value):
        current = obj
        for k in keys[:-1]:
            # Try to access the next level
            next_level = None
            # 1. Try dict/key access first (works for both dict and ConfigDict)
            if isinstance(current, dict):
                if k in current:
                    next_level = current[k]
                else:
                    # Auto-create intermediate dict/ConfigDict if missing
                    if isinstance(current, ConfigDict):
                        current[k] = ConfigDict()
                    else:
                        current[k] = {}
                    next_level = current[k]
            else:
                # Fallback for other objects (unlikely in this config structure)
                try:
                    next_level = getattr(current, k)
                except AttributeError:
                    setattr(current, k, {})
                    next_level = getattr(current, k)
            
            current = next_level

        # Set the final leaf value
        leaf_key = keys[-1]
        
        # Enum coercion logic
        current_val = None
        if isinstance(current, dict):
            current_val = current.get(leaf_key)
        else:
            current_val = getattr(current, leaf_key, None)

        if current_val is not None and hasattr(current_val, '__class__'):
            # Check if it's an Enum
            import enum
            if isinstance(current_val, enum.Enum):
                ec = current_val.__class__
                try:
                    value = ec(value)
                except Exception:
                    pass
        
        # Assign value
        if isinstance(current, dict):
            current[leaf_key] = value
        else:
            setattr(current, leaf_key, value)

    for dotkey, value in patch.items():
        keys = dotkey.split('.')
        try:
            _set_nested(config, keys, value)
        except Exception as e:
            logger.warning(f"Failed to patch config key '{dotkey}': {e}")
def _get_robot(config):
    if config.robots.type == RobotType.A2D:
        from client.robots.a2d.body_robot import RobotBody
        return RobotBody(config)
    elif config.robots.type == RobotType.MOCK:
        from client.robots.mock.body_robot import RobotBody
        return RobotBody(config)
    else:
        raise ValueError(f"Unsupported robot type: {config.robots.type}")


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket broadcast
# ─────────────────────────────────────────────────────────────────────────────
async def _broadcast(message: dict):
    """Send JSON to all connected WebSocket clients."""
    if not state.ws_clients:
        return
    data = json.dumps(message)
    dead = set()
    with state.ws_lock:
        clients = set(state.ws_clients)
    for ws in clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    if dead:
        with state.ws_lock:
            state.ws_clients -= dead


async def _stats_push_loop():
    """Background coroutine: push runtime stats to all WS clients every 250 ms."""
    while True:
        await asyncio.sleep(0.25)
        if not state.ws_clients:
            continue
        try:
            stats = _collect_stats()
            await _broadcast({"type": "stats", "data": stats})
        except Exception as e:
            logger.debug(f"stats push error: {e}")


def _collect_stats() -> dict:
    """Gather runtime stats from the running vla_client."""
    base = {
        "running": state.running,
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
    }
    with state.lock:
        vc = state.vla_client
    if vc is None:
        return base

    try:
        base["infer_count"]     = int(vc.rdm.infer_count)
        base["avg_infer_time"]  = float(vc.rdm.avg_infer_time)
        base["avg_traj_time"]   = float(vc.rdm.avg_traj_time)
        base["language"]        = str(vc.language)
        base["current_state"]   = [round(float(x), 2) for x in vc.info_current_state]
        base["current_action"]  = [round(float(x), 2) for x in vc.info_current_action]
        base["info_obs"]        = {k: str(v) for k, v in vc.info_obs.items()}
        base["info_act"]        = {k: str(v) for k, v in vc.info_act.items()}
        base["debug_info"]      = str(vc.debug_info)
        # base["config_snapshot"] = {
        #     "fps":              cfg.observer.fps,
        #     "sleep_time":       cfg.sleep_time,
        #     "inter_chunk_mode": cfg.inter_chunk_mode,
        #     "intra_chunk_mode": cfg.intra_chunk_mode,
        #     "gripper_offset":   cfg.gripper_offset,
        #     "preprocess":       cfg.preprocess,
        #     "robots_type":      cfg.robots.type.value if hasattr(cfg.robots.type, 'value') else str(cfg.robots.type),
        #     "record":           cfg.record.switch,
        #     "thre_prob_progress": cfg.thre_prob_progress,
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


# ─────────────────────────────────────────────────────────────────────────────
#  REST: config
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/conf_dir")
async def get_conf_dir():
    """Return the absolute path of the project conf/ directory."""
    conf_dir = ROOT / "conf"
    return {"status": "ok", "path": str(conf_dir)}


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
    p = Path(req.path)
    if not p.is_absolute():
        p = ROOT / p
    # Guard against path-traversal: resolved path must stay inside ROOT
    try:
        p = p.resolve()
        p.relative_to(ROOT.resolve())
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
    if state.config is None:
        cfg = get_client_config()
        state.config = cfg
    return {"status": "ok", "config": _config_to_dict(state.config)}


class ConfigPatchRequest(BaseModel):
    patch: dict   # flat dot-key → value  OR  nested dict


@app.post("/api/config/patch")
async def patch_config(req: ConfigPatchRequest):
    """Apply a partial update to in-memory config (does NOT restart client)."""
    if state.running:
        raise HTTPException(400, "Stop the client before modifying config.")
    if state.config is None:
        state.config = get_client_config()

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
    _apply_flat_patch(state.config, flat)
    return {"status": "ok", "config": _config_to_dict(state.config)}


class ConfigFileRequest(BaseModel):
    path: str


@app.post("/api/config/load_file")
async def load_config_file(req: ConfigFileRequest):
    """Load a yaml conf file and apply it (like --default_conf.yaml)."""
    if state.running:
        raise HTTPException(400, "Stop the client before loading a new config.")
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
    _apply_yaml_config(state.config, p)
    # user_cfg = load_user_config(str(p))
    # if user_cfg is None:
    #     raise HTTPException(400, f"Failed to load config from: {p}")
    # base_cfg = get_client_config()
    # state.config = apply_user_config(base_cfg, user_cfg)
    return {"status": "ok", "config": _config_to_dict(state.config)}


@app.post("/api/config/save_file")
async def save_config_file(req: ConfigFileRequest):
    """Save current in-memory config to a file.

    Supported formats (determined by file extension):
      .yaml / .yml  →  YAML  (via _dict_to_user_conf_yaml)
      .py           →  Python get_user_config() module (via _dict_to_user_conf_py)
    """
    if state.config is None:
        raise HTTPException(400, "No config loaded.")
    save_path = Path(req.path)
    if not save_path.is_absolute():
        save_path = ROOT / save_path
    # Guard against path-traversal: resolved path must stay inside ROOT
    try:
        save_path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        raise HTTPException(400, "Path is outside the allowed project directory.")
    cfg_dict = _config_to_dict(state.config)
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
        _apply_flat_patch(config, patch)
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
    _apply_flat_patch(config, flat)
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
@app.post("/api/client/start")
async def start_client():
    """Initialise and start the VLA client (non-blocking)."""
    # Lock prevents concurrent requests from both passing the running guard
    with state.lock:
        if state.running:
            raise HTTPException(400, "Client is already running.")
        # Set eagerly inside the lock so a second concurrent request is rejected
        # before the worker thread is even created.
        state.running = True

    # get_running_loop() is the correct API inside a running coroutine (Python 3.10+)
    loop = asyncio.get_running_loop()
    state._loop = loop

    def _run_in_thread():
        try:
            logging.config.dictConfig(LOGGING_CONFIG)
            cfg = state.config if state.config is not None else get_client_config()
            state.config = cfg

            # Apply action_layout from robot config
            robot_cfg = getattr(cfg.robots, cfg.robots.type.value, None)
            if robot_cfg is not None and hasattr(robot_cfg, 'action_layout'):
                cfg.rdm.action_layout = robot_cfg.action_layout
                cfg.traj.action_layout = robot_cfg.action_layout

            vla_zmq_client = ZMQClient(cfg.vla_zmq)
            robot = _get_robot(cfg)
            rdm = RealtimeDataManager(cfg.rdm)
            traj_gen = TrajectoryGenerator(config=cfg.traj)

            if cfg.inter_chunk_mode == 'sync':
                from client.core.vla_client_sync import VLAClientSync
                vc = VLAClientSync(config=cfg, rdm=rdm, traj_generator=traj_gen,
                                   vla_zmq_client=vla_zmq_client, robot=robot)
            else:
                from client.core.vla_client import VLAClientAsync
                vc = VLAClientAsync(config=cfg, rdm=rdm, traj_generator=traj_gen,
                                    vla_zmq_client=vla_zmq_client, robot=robot)

            state.vla_client = vc
            state.robot = robot

            # Broadcast "started" immediately before entering the blocking vc.run()
            asyncio.run_coroutine_threadsafe(
                _broadcast({"type": "status", "data": {"running": True, "message": "Client started."}}),
                loop
            )

            vc.run()

            # Keep alive until externally stopped
            while state.running:
                time.sleep(0.1)

        except Exception as e:
            err = traceback.format_exc()
            logger.error(f"Client thread error:\n{err}")
            state.running = False
            asyncio.run_coroutine_threadsafe(
                _broadcast({"type": "error", "data": {"message": str(e), "trace": err}}),
                loop
            )
        finally:
            _cleanup()

    t = threading.Thread(target=_run_in_thread, daemon=True, name="vla-client")
    t.start()
    return {"status": "ok", "message": "Client starting…"}


@app.post("/api/client/stop")
async def stop_client():
    """Stop the running VLA client."""
    if not state.running:
        raise HTTPException(400, "Client is not running.")
    state.running = False
    _cleanup()
    await _broadcast({"type": "status", "data": {"running": False, "message": "Client stopped."}})
    return {"status": "ok"}


def _cleanup():
    vc = state.vla_client
    robot = state.robot
    if vc is not None:
        try:
            vc.close()
        except Exception:
            pass
    if robot is not None:
        try:
            robot.close()
        except Exception:
            pass
    state.vla_client = None
    state.robot = None
    state.running = False


@app.get("/api/client/status")
async def client_status():
    return {"status": "ok", "data": _collect_stats()}


# ─────────────────────────────────────────────────────────────────────────────
#  REST: runtime commands (replaces Enter-key menu in run_client.py)
# ─────────────────────────────────────────────────────────────────────────────
class CommandRequest(BaseModel):
    command: str          # reset / set_language / save_data / discard_data / gripper / head / waist
    params: dict = {}


@app.post("/api/client/command")
async def client_command(req: CommandRequest):
    vc = state.vla_client
    robot = state.robot
    if vc is None or not state.running:
        raise HTTPException(400, "Client is not running.")

    cmd = req.command
    params = req.params

    try:
        if cmd == "reset":
            vc.is_running_action = False
            robot.reset_robot(mode='default')
            vc.inference_first()
            vc.is_running_action = True

        elif cmd == "set_language":
            lang = params.get("language", "")
            vc.language = lang
            vc.is_running_action = False
            robot.reset_robot(mode='default')
            vc.inference_first()
            vc.is_running_action = True

        elif cmd == "save_data":
            if state.config.record.switch:
                vc.dataset_write.save_writed_data()

        elif cmd == "discard_data":
            if state.config.record.switch:
                vc.dataset_write.abandon_record_data()

        elif cmd == "gripper":
            pos = params.get("pos", [0.0, 0.0])
            robot.execute_action({'gripper': pos})

        elif cmd == "head":
            pos = params.get("pos", [0.0, 0.436])
            robot.execute_action({'head': pos})

        elif cmd == "waist":
            pos = params.get("pos", [0.297, 20.0])
            robot.execute_action({'waist': pos})

        elif cmd == "pause":
            vc.is_running_action = False

        elif cmd == "resume":
            vc.inference_first()
            vc.is_running_action = True

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
    with state.ws_lock:
        state.ws_clients.add(ws)

    # Push current state immediately on connect
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
        with state.ws_lock:
            state.ws_clients.discard(ws)


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
