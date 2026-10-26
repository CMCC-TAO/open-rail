"""Shared parsing helpers for teleop configuration values."""

RESET_MODES = {"topic", "joint_command", "none"}


def config_get(config, key, default=None):
    """Read a key from ConfigDict-like objects or plain dictionaries."""

    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def normalize_reset_mode(value) -> str:
    """Canonicalize teleop reset mode names."""

    mode = str(value or "joint_command").strip().lower().replace("-", "_")
    aliases = {
        "disabled": "none",
        "off": "none",
        "joint": "joint_command",
        "command": "joint_command",
        "joint_commands": "joint_command",
    }
    mode = aliases.get(mode, mode)
    if mode not in RESET_MODES:
        raise ValueError(
            f"Unsupported reset_mode {value!r}; expected one of {sorted(RESET_MODES)}"
        )
    return mode
