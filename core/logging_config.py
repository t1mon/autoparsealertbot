"""Centralized structlog configuration (по образцу bedolaga).

Usage::

    from core.logging_config import setup_logging, _resolve_log_level

    file_formatter, console_formatter = setup_logging()
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from core import config as settings


def _resolve_log_level(value: object, default: int = logging.INFO) -> int:
    """Resolve LOG_LEVEL string to stdlib int level (case-safe)."""
    if not isinstance(value, str):
        return default
    name = value.strip().upper()
    if not name:
        return default
    level = getattr(logging, name, None)
    return level if isinstance(level, int) else default


def _create_timezone_timestamper() -> structlog.types.Processor:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo(settings.TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")

    def timestamper(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        dt = datetime.now(tz=tz)
        event_dict["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        return event_dict

    return timestamper


def _clean_logger_name(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    if event_dict.get("logger") == "__main__":
        del event_dict["logger"]
    return event_dict


def _prefix_logger_name(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    logger_name = event_dict.pop("logger", None)
    if logger_name:
        event_dict["event"] = f"[{logger_name}] {event_dict.get('event', '')}"
    return event_dict


def _auto_capture_exc_info(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    exc_info = event_dict.get("exc_info")
    if exc_info is True:
        current = sys.exc_info()
        if current[1] is not None:
            event_dict["exc_info"] = current
        return event_dict

    if exc_info:
        return event_dict

    if method_name in ("error", "critical", "exception"):
        current = sys.exc_info()
        if current[1] is not None:
            event_dict["exc_info"] = current
            return event_dict

    for key in ("error", "exc", "exception", "e", "err"):
        candidate = event_dict.get(key)
        if isinstance(candidate, BaseException) and candidate.__traceback__ is not None:
            event_dict["exc_info"] = (type(candidate), candidate, candidate.__traceback__)
            return event_dict

    return event_dict


def setup_logging() -> tuple[logging.Formatter, logging.Formatter]:
    """Configure structlog and return (file_formatter, console_formatter)."""
    timestamper = _create_timezone_timestamper()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _clean_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        _auto_capture_exc_info,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(_resolve_log_level(settings.LOG_LEVEL)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    file_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _prefix_logger_name,
            structlog.dev.ConsoleRenderer(
                colors=False,
                pad_event_to=0,
                pad_level=False,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ],
    )

    use_colors = settings.LOG_COLORS
    console_renderer_kwargs: dict[str, Any] = {
        "colors": use_colors,
        "pad_event_to": 0,
        "pad_level": False,
    }
    if use_colors:
        console_renderer_kwargs["exception_formatter"] = structlog.dev.RichTracebackFormatter(
            show_locals=False,
            max_frames=20,
            extra_lines=1,
            width=120,
            suppress=["aiogram", "aiohttp"],
        )
    else:
        console_renderer_kwargs["exception_formatter"] = structlog.dev.plain_traceback

    console_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _prefix_logger_name,
            structlog.dev.ConsoleRenderer(**console_renderer_kwargs),
        ],
    )

    _configure_noisy_loggers()
    return file_formatter, console_formatter


def _configure_noisy_loggers() -> None:
    for name, level in {
        "aiohttp.access": logging.ERROR,
        "aiohttp.client": logging.WARNING,
        "aiohttp.internal": logging.WARNING,
        "aiogram": logging.WARNING,
        "telethon": logging.WARNING,
        "uvicorn.access": logging.ERROR,
        "uvicorn.error": logging.WARNING,
        "uvicorn.protocols.websockets.websockets_impl": logging.WARNING,
        "websockets.server": logging.WARNING,
        "websockets": logging.WARNING,
    }.items():
        logging.getLogger(name).setLevel(level)


class LevelFilterHandler(logging.Handler):
    """File handler that only emits records within [min_level, max_level]."""

    def __init__(
        self,
        filename: str,
        min_level: int,
        max_level: int | None = None,
        encoding: str = "utf-8",
    ):
        super().__init__(level=min_level)
        self.min_level = min_level
        self.max_level = max_level if max_level is not None else logging.CRITICAL
        self._file_handler = logging.FileHandler(filename, encoding=encoding)

    def emit(self, record: logging.LogRecord) -> None:
        if self.min_level <= record.levelno <= self.max_level:
            self._file_handler.emit(record)

    def setFormatter(self, fmt: logging.Formatter) -> None:
        super().setFormatter(fmt)
        self._file_handler.setFormatter(fmt)

    def close(self) -> None:
        self._file_handler.close()
        super().close()

    def flush(self) -> None:
        self._file_handler.flush()


def configure_stdlib_logging(
    file_formatter: logging.Formatter,
    console_formatter: logging.Formatter,
) -> None:
    """Wire FileHandler(s) + console into root logger."""
    from pathlib import Path

    log_handlers: list[logging.Handler] = []
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    if settings.LOG_ROTATION_ENABLED:
        bot_handler = logging.FileHandler(log_dir / "bot.log", encoding="utf-8")
        bot_handler.setFormatter(file_formatter)
        log_handlers.append(bot_handler)

        info_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_INFO_FILE),
            min_level=logging.INFO,
            max_level=logging.INFO,
        )
        info_handler.setFormatter(file_formatter)
        log_handlers.append(info_handler)

        warning_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_WARNING_FILE),
            min_level=logging.WARNING,
        )
        warning_handler.setFormatter(file_formatter)
        log_handlers.append(warning_handler)

        error_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_ERROR_FILE),
            min_level=logging.ERROR,
        )
        error_handler.setFormatter(file_formatter)
        log_handlers.append(error_handler)
    else:
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        log_handlers.append(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(console_formatter)
    log_handlers.append(stream_handler)

    logging.basicConfig(
        level=_resolve_log_level(settings.LOG_LEVEL),
        handlers=log_handlers,
        force=True,
    )
