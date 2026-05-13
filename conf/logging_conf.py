"""Logging configuration for VLA inference system.

This module provides centralized logging configuration with both console and file
handlers, supporting different log levels and formats for development and production.
"""

import logging
import logging.config
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

# Create logs directory relative to project root
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_RETENTION_DAYS = 7


def _build_log_path(log_filename: str) -> str:
    """Build log path with timestamp format: stem_YYYYMMDD_HHMM.suffix."""
    path = Path(log_filename)
    stem = path.stem or "app"
    suffix = path.suffix or ".log"
    timestamp = datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    return str(LOG_DIR / f"{stem}{suffix}.{timestamp}")


def _cleanup_old_logs(log_filename: str, retention_days: int = LOG_RETENTION_DAYS) -> None:
    """Delete log files older than retention_days for the specified log prefix."""
    path = Path(log_filename)
    stem = path.stem or "app"
    suffix = path.suffix or ".log"
    prefix = f"{stem}{suffix}."
    cutoff = datetime.now() - timedelta(days=retention_days)

    for log_file in LOG_DIR.glob(f"{prefix}*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink(missing_ok=True)
        except Exception:
            # Best-effort cleanup: ignore deletion/stat errors.
            continue


def get_logging_config(log_filename: str = "app.log") -> dict:
    """Return logging config with a runtime-selected log filename."""
    log_path = _build_log_path(log_filename)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
            },
            "verbose": {
                "format": "%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "formatter": "verbose",
                "filename": log_path,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    }


def setup_logging(log_filename: str = "app.log", logger_name: str | None = None) -> logging.Logger:
    """Setup logging and return logger instance."""
    _cleanup_old_logs(log_filename, LOG_RETENTION_DAYS)
    logging.config.dictConfig(get_logging_config(log_filename))
    return logging.getLogger(logger_name)


# Backward-compatible default config
LOGGING_CONFIG = deepcopy(get_logging_config("app.log"))
