"""Teleop configuration and runtime status shared by client and Web layers."""

from __future__ import annotations

from conf.client_conf import get_teleop_config_path
from teleop.config import config_get as _cfg_get


def teleop_enabled(config) -> bool:
    """Return the effective teleop switch, including legacy root configs."""

    teleop_cfg = _cfg_get(config, "teleop", None)
    configured = _cfg_get(teleop_cfg, "use_teleop", None)
    if configured is not None:
        return bool(configured)
    return bool(_cfg_get(config, "use_teleop", False))


def teleop_status_snapshot(config, *, bridge=None) -> dict:
    """Build one status payload for the API, Web UI, and runtime clients."""

    robots_cfg = _cfg_get(config, "robots", None)
    robot_type = _cfg_get(robots_cfg, "type", "")
    robot_type = getattr(robot_type, "value", robot_type)
    robot_type = str(robot_type or "")
    config_path = get_teleop_config_path(robot_type)
    supported = config_path is not None
    enabled = teleop_enabled(config) and supported
    bridge_running = bool(bridge is not None and bridge.running)
    status = {
        "enabled": enabled,
        "supported": supported,
        "config_path": config_path,
        "bridge_running": bridge_running,
        "device_connected": False,
        "state": "disabled" if not enabled else "unavailable",
        "message": (
            "Teleop is disabled."
            if not enabled
            else "Teleop bridge is not running. Start the client and verify the Quest3 configuration."
        ),
    }
    if not supported:
        status.update(
            state="unsupported",
            message=f"Quest3 teleop is not supported for robot type {robot_type!r}.",
        )
        return status
    if not enabled:
        return status
    if bridge is None or not bridge.running:
        return status
    try:
        status.update(bridge.status())
    except Exception as exc:
        status.update(state="error", message=f"Failed to read teleop status: {exc}")
    status.update(
        enabled=enabled,
        supported=supported,
        bridge_running=bool(bridge.running),
    )
    return status
