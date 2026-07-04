"""Logging configuration for VLA inference system.

This module provides centralized logging configuration with both console and file
handlers, supporting different log levels and formats for development and production.
"""

import logging
import logging.config
import shutil
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import re
import os
import psutil
import subprocess


def _is_ntfs_mount_accurate2(path):
    """
    检查指定路径是否挂载在 NTFS 文件系统上
    """
    # 一次性获取所有分区信息
    partitions = psutil.disk_partitions(all=False)
    if not partitions:
        return False
    # 获取绝对路径
    abs_path = os.path.abspath(path)
    is_windows = os.name == 'nt'
    # 查找匹配的挂载点（无需排序，直接遍历并记录最长匹配）
    best_mount = None
    best_mount_len = -1
    for partition in partitions:
        mountpoint = partition.mountpoint
        # 检查路径是否以挂载点开头
        if is_windows:
            is_match = abs_path.upper().startswith(mountpoint.upper())
        else:
            is_match = abs_path.startswith(mountpoint)
        
        if is_match and len(mountpoint) > best_mount_len:
            best_mount_len = len(mountpoint)
            best_mount = partition
    if best_mount is None:
        return False
    # 检查文件系统类型
    fstype = best_mount.fstype.lower()
    # 直接确认 NTFS
    if fstype in ('ntfs', 'ntfs3'):
        return True
    # 处理 fuseblk (通常是 NTFS-3G)
    if fstype == 'fuseblk':
        device = best_mount.device
        try:
            # 使用 lsblk 获取文件系统类型（仅输出必要字段）
            result = subprocess.run(
                ['lsblk', '-n', '-o', 'FSTYPE', device],  # -n 不显示标题，-o 只输出 FSTYPE
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                fs_type = result.stdout.strip()
                return fs_type.lower() == 'ntfs'
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            pass
    
    return False


# Create logs directory relative to project root
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_RETENTION_DAYS = 7
IS_LOG_DISK_TYPE_NTFS = _is_ntfs_mount_accurate2(LOG_DIR)
_LOG_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})--\d{2}:\d{2}:\d{2}$") if not IS_LOG_DISK_TYPE_NTFS else re.compile(r"(\d{4}-\d{2}-\d{2})--\d{2}-\d{2}-\d{2}$")
_LOG_TIMESTAMP_FORMAT = "%Y-%m-%d--%H:%M:%S" if not IS_LOG_DISK_TYPE_NTFS else "%Y-%m-%d--%H-%M-%S"


def _extract_log_day(log_file: Path) -> str:
    """Extract log day in YYYY-MM-DD from filename suffix or fallback to mtime."""
    name = log_file.name
    m = _LOG_DATE_RE.search(name)
    if m:
        return m.group(1)
    return datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d")


def _iter_log_files(prefix: str):
    """Yield matching log files from logs root and day subfolders."""
    for p in LOG_DIR.rglob(f"{prefix}*"):
        if p.is_file():
            yield p


def _organize_historical_logs(log_filename: str) -> None:
    """Move yesterday-and-older logs into per-day folders under logs/."""
    path = Path(log_filename)
    stem = path.stem or "app"
    suffix = path.suffix or ".log"
    prefix = f"{stem}{suffix}."

    today = datetime.now().strftime("%Y-%m-%d")
    for log_file in list(_iter_log_files(prefix)):
        try:
            day = _extract_log_day(log_file)
            if day >= today:
                continue
            day_dir = LOG_DIR / day
            day_dir.mkdir(parents=True, exist_ok=True)
            target = day_dir / log_file.name
            if target.resolve() == log_file.resolve():
                continue
            if target.exists():
                target.unlink(missing_ok=True)
            log_file.rename(target)
        except Exception:
            continue


def _build_log_path(log_filename: str) -> str:
    """Build log path with timestamp format: stem_YYYYMMDD_HHMM.suffix."""
    path = Path(log_filename)
    stem = path.stem or "app"
    suffix = path.suffix or ".log"
    # timestamp = datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    timestamp = datetime.now().strftime(_LOG_TIMESTAMP_FORMAT)
    return str(LOG_DIR / f"{stem}{suffix}.{timestamp}")


def _cleanup_old_logs(log_filename: str, retention_days: int = LOG_RETENTION_DAYS) -> None:
    """Delete whole day folders older than retention_days."""
    _ = log_filename
    cutoff_day = (datetime.now() - timedelta(days=retention_days)).date()

    for day_dir in LOG_DIR.iterdir():
        if not day_dir.is_dir():
            continue
        try:
            folder_day = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        except Exception:
            continue

        if folder_day < cutoff_day:
            try:
                shutil.rmtree(day_dir)
            except Exception:
                continue


def get_logging_config(log_filename: str = "app.log") -> dict:
    """Return logging config with a runtime-selected log filename."""
    log_path = _build_log_path(log_filename)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s-[%(levelname)s]-%(name)s-%(message)s"
            },
            "verbose": {
                # "format": "%(asctime)s-[%(levelname)s]-%(name)s-%(filename)s:%(lineno)d-%(message)s"
                "format": "%(asctime)s-[%(levelname)s]-%(name)s.%(funcName)s:%(lineno)d-%(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
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
        "loggers": {
            "client.core.vla_client": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.vla_client_sync": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.realtime_data_manager": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.task_language_manager": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.visualize_server": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.inter_chunk_fuser": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.intra_chunk_smoother": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.core.save_lerobot": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.utils.util": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "client.robots.mock.body_robot": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "web_client.server": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "websockets": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "websockets.server": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "websockets.server.protocol": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
            "scripts.show_lerobot_data.show_data_qt": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "DispatchZMQClient": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "__main__": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
    }


def setup_logging(log_filename: str = "app.log", logger_name: str | None = None) -> logging.Logger:
    """Setup logging and return logger instance."""
    _organize_historical_logs(log_filename)
    _cleanup_old_logs(log_filename, LOG_RETENTION_DAYS)
    logging.config.dictConfig(get_logging_config(log_filename))
    return logging.getLogger(logger_name)


# Backward-compatible default config
LOGGING_CONFIG = deepcopy(get_logging_config("app.log"))
