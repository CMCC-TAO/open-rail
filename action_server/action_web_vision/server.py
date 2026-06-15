"""
Action Web Vision Server — 纯转发 Web 可视化服务

架构变更（v2）：
    不再创建独立的 RobotBody（DDS 域冲突），而是从 action_dispatcher
    进程的 ObsDataBridge (ws://127.0.0.1:9001) 接收观测数据，
    再转发给浏览器客户端。

数据流：
    action_dispatcher (ObsDataBridge:9001)
        ↓ camera binary + joint_data JSON
    server.py (FastAPI:9000)
        ↓ 转发
    浏览器 WebSocket 客户端

    action_dispatcher (VisualizeServer:8765)
        ↓ action_raw / action_fitted
    浏览器 WebSocket 客户端（直连）

访问：http://localhost:9000 或 http://0.0.0.0:9000
"""

import asyncio
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

# ── project root on sys.path ────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"

# ── Resource monitoring (lightweight, no psutil required) ───────────────────
_LAST_CPU_STAT = None
_LAST_NET_STAT = None
_RESOURCE_CACHE = {"ts": 0.0, "data": {}}


def _read_linux_cpu_usage() -> Optional[float]:
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
        return max(0.0, min(100.0, (1.0 - idle_delta / total_delta) * 100.0))
    except Exception:
        return None


def _read_linux_mem_usage() -> Optional[float]:
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
        return max(0.0, min(100.0, (1.0 - mem_available / mem_total) * 100.0))
    except Exception:
        return None


def _read_gpu_usage() -> Optional[float]:
    try:
        nvidia_smi = subprocess.run(
            ["which", "nvidia-smi"], capture_output=True, text=True, timeout=1.0
        )
        if nvidia_smi.returncode != 0:
            return None
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=1.0,
        )
        if proc.returncode != 0:
            return None
        vals = []
        for line in proc.stdout.splitlines():
            line = line.strip().replace("%", "")
            if line:
                try:
                    vals.append(float(line))
                except Exception:
                    continue
        if vals:
            return max(0.0, min(100.0, sum(vals) / len(vals)))
        return None
    except Exception:
        return None


def _read_bandwidth_m() -> Optional[float]:
    global _LAST_NET_STAT
    now = time.time()
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
            total += float(parts[0]) + float(parts[8])
    except Exception:
        return None

    if _LAST_NET_STAT is None:
        _LAST_NET_STAT = (now, total)
        return None
    prev_ts, prev_total = _LAST_NET_STAT
    _LAST_NET_STAT = (now, total)
    dt = now - prev_ts
    if dt <= 0:
        return None
    delta = max(0.0, total - prev_total)
    return delta / dt / (1024.0 * 1024.0)


def _collect_resource_stats() -> dict:
    now = time.time()
    if now - _RESOURCE_CACHE["ts"] < 1.0:
        return _RESOURCE_CACHE["data"]
    cpu = _read_linux_cpu_usage()
    mem = _read_linux_mem_usage()
    gpu = _read_gpu_usage()
    bw = _read_bandwidth_m()
    data = {
        "cpu_usage": round(cpu, 1) if cpu is not None else None,
        "gpu_usage": round(gpu, 1) if gpu is not None else None,
        "mem_usage": round(mem, 1) if mem is not None else None,
        "bandwidth_m": round(bw, 2) if bw is not None else None,
    }
    _RESOURCE_CACHE["ts"] = now
    _RESOURCE_CACHE["data"] = data
    return data


# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(title="Action Web Vision", version="2.0.0")

# Static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Expose visual/ libs (Chart.js + plugins) — reuse from project root
VISUAL_DIR = ROOT / "visual"
if VISUAL_DIR.exists():
    app.mount("/visual", StaticFiles(directory=str(VISUAL_DIR)), name="visual")

# Global state
ws_clients: set[WebSocket] = set()
ws_lock = asyncio.Lock()

# ── Internal bridge client ──────────────────────────────────────────────────
_bridge_ws = None  # websockets.WebSocketClientProtocol
_bridge_connected = False


async def _connect_bridge():
    """连接到 ObsDataBridge (ws://127.0.0.1:9001)"""
    global _bridge_ws, _bridge_connected
    import websockets

    while True:
        try:
            _bridge_ws = await websockets.connect(
                "ws://127.0.0.1:9001",
                max_size=2 ** 23,
                ping_interval=10,
                ping_timeout=5,
            )
            _bridge_connected = True
            print("[WebVision] Connected to ObsDataBridge (9001)")
            return
        except Exception as e:
            print(f"[WebVision] Bridge connect failed: {e}, retrying in 2s...")
            await asyncio.sleep(2.0)


async def _bridge_reader():
    """从 ObsDataBridge 读取数据并转发给所有浏览器客户端"""
    global _bridge_ws, _bridge_connected

    while True:
        if _bridge_ws is None or not _bridge_connected:
            await _connect_bridge()
            continue

        try:
            message = await _bridge_ws.recv()
        except Exception as e:
            print(f"[WebVision] Bridge read error: {e}")
            _bridge_connected = False
            _bridge_ws = None
            await asyncio.sleep(1.0)
            continue

        if not ws_clients:
            continue

        # 转发给所有浏览器客户端
        dead = set()
        async with ws_lock:
            for ws in list(ws_clients):
                try:
                    if isinstance(message, bytes):
                        await ws.send_bytes(message)
                    else:
                        await ws.send_text(message)
                except Exception:
                    dead.add(ws)
        if dead:
            async with ws_lock:
                ws_clients.difference_update(dead)


# ── Lifecycle ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print("[WebVision] Starting Action Web Vision Server v2...")
    asyncio.create_task(_bridge_reader())
    asyncio.create_task(_stats_loop())
    print("[WebVision] Server ready on http://0.0.0.0:9000")


@app.on_event("shutdown")
async def shutdown():
    global _bridge_ws, _bridge_connected
    _bridge_connected = False
    if _bridge_ws:
        try:
            await _bridge_ws.close()
        except Exception:
            pass
        _bridge_ws = None


async def _stats_loop():
    """每秒推送资源监控数据"""
    while True:
        await asyncio.sleep(1.0)
        if not ws_clients:
            continue
        stats = _collect_resource_stats()
        msg = json.dumps({"type": "stats", "data": stats})
        dead = set()
        async with ws_lock:
            for ws in list(ws_clients):
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.add(ws)
        if dead:
            async with ws_lock:
                ws_clients.difference_update(dead)


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/favicon.ico")
async def favicon():
    icon_path = STATIC_DIR / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    return FileResponse(str(STATIC_DIR / "index.html"), status_code=404)


# ── WebSocket endpoint (browser clients) ────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    async with ws_lock:
        ws_clients.add(ws)
    print(f"[WebVision] WS client connected, total: {len(ws_clients)}")

    try:
        while True:
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
        print(f"[WebVision] WS error: {e}")
    finally:
        async with ws_lock:
            ws_clients.discard(ws)
        print(f"[WebVision] WS client disconnected, total: {len(ws_clients)}")


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "action_server.action_web_vision.server:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        log_level="info",
    )
