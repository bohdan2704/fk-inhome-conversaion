from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = Path(__file__).resolve().parent / "logs"
DEFAULT_LOG_PREFIX = "convert-api"
DEFAULT_LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CONSOLE_HANDLER_NAME = "convert_api_console"
FILE_HANDLER_NAME = "convert_api_daily_file"


class DailyFileHandler(logging.Handler):
    def __init__(
        self,
        *,
        log_dir: str | Path | None = None,
        prefix: str = DEFAULT_LOG_PREFIX,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self.log_dir = Path(log_dir or os.environ.get("FEED_LOG_DIR") or DEFAULT_LOG_DIR)
        self.prefix = prefix
        self.encoding = encoding
        self._current_date = ""
        self._file_handler: logging.FileHandler | None = None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.acquire()
            self._ensure_handler(datetime.fromtimestamp(record.created))
            if self._file_handler is not None:
                self._file_handler.emit(record)
        finally:
            self.release()

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        super().setFormatter(fmt)
        if self._file_handler is not None:
            self._file_handler.setFormatter(fmt)

    def setLevel(self, level: int | str) -> None:
        super().setLevel(level)
        if self._file_handler is not None:
            self._file_handler.setLevel(level)

    def flush(self) -> None:
        if self._file_handler is not None:
            self._file_handler.flush()

    def close(self) -> None:
        try:
            self.acquire()
            if self._file_handler is not None:
                self._file_handler.close()
                self._file_handler = None
        finally:
            self.release()
            super().close()

    def _ensure_handler(self, current_dt: datetime) -> None:
        current_date = current_dt.strftime("%Y-%m-%d")
        if self._file_handler is not None and current_date == self._current_date:
            return

        self.log_dir.mkdir(parents=True, exist_ok=True)
        new_handler = logging.FileHandler(
            self.log_dir / f"{self.prefix}-{current_date}.log",
            encoding=self.encoding,
        )
        new_handler.setLevel(self.level or logging.NOTSET)
        if self.formatter is not None:
            new_handler.setFormatter(self.formatter)

        old_handler = self._file_handler
        self._file_handler = new_handler
        self._current_date = current_date
        if old_handler is not None:
            old_handler.close()


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
    formatter = logging.Formatter(
        DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    console_handler = _ensure_stream_handler(root_logger, formatter)
    file_handler = _ensure_daily_file_handler(root_logger, formatter)

    root_logger.setLevel(resolved_level)
    console_handler.setLevel(resolved_level)
    file_handler.setLevel(resolved_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def format_duration(seconds: float) -> str:
    return f"{seconds * 1000:.2f} ms"


def _ensure_stream_handler(
    root_logger: logging.Logger,
    formatter: logging.Formatter,
) -> logging.Handler:
    handler = _find_named_handler(root_logger, CONSOLE_HANDLER_NAME)
    if handler is None:
        handler = logging.StreamHandler()
        handler.set_name(CONSOLE_HANDLER_NAME)
        root_logger.addHandler(handler)
    handler.setFormatter(formatter)
    return handler


def _ensure_daily_file_handler(
    root_logger: logging.Logger,
    formatter: logging.Formatter,
) -> DailyFileHandler:
    handler = _find_named_handler(root_logger, FILE_HANDLER_NAME)
    if handler is None:
        handler = DailyFileHandler()
        handler.set_name(FILE_HANDLER_NAME)
        root_logger.addHandler(handler)
    handler.setFormatter(formatter)
    return handler  # type: ignore[return-value]


def _find_named_handler(
    root_logger: logging.Logger,
    handler_name: str,
) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if handler.get_name() == handler_name:
            return handler
    return None


__all__ = [
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_LOG_DIR",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_LOG_PREFIX",
    "DailyFileHandler",
    "configure_logging",
    "format_duration",
    "get_logger",
    "resolve_log_level",
]
