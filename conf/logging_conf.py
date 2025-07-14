import logging
import logging.config
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
        },
        "verbose": {
            "format": "%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s:%(lineno)d - %(message)s"
            # "format": "%(asctime)s - [%(levelname)s] - %(name)s - line:%(lineno)d - %(message)s"
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
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "verbose",
            "filename": str(LOG_DIR / "app.log"),
            "when": "midnight",
            "backupCount": 7,
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}
