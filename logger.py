from __future__ import annotations

import logging
import os


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def resolve_log_level(level: str | int | None = None) -> int:
    if isinstance(level, int):
        return level

    raw_level = (
        level
        or os.environ.get("FEED_API_LOG_LEVEL")
        or os.environ.get("FEED_LOG_LEVEL")
        or os.environ.get("LOG_LEVEL")
        or DEFAULT_LOG_LEVEL
    )
    normalized = str(raw_level).strip().upper()
    return logging.getLevelNamesMapping().get(normalized, logging.INFO)


def configure_logging(level: str | int | None = None) -> None:
    root_logger = logging.getLogger()
    resolved_level = resolve_log_level(level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        root_logger.addHandler(handler)

    root_logger.setLevel(resolved_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def format_duration(seconds: float) -> str:
    return f"{seconds * 1000:.2f} ms"


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "configure_logging",
    "format_duration",
    "get_logger",
    "resolve_log_level",
]
