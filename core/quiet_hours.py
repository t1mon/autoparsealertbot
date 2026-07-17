"""Тихие часы: не слать алерты в заданный интервал (TIMEZONE)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import structlog

from core.config import TIMEZONE

logger = structlog.get_logger(__name__)


def _app_tz() -> ZoneInfo:
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        return ZoneInfo("UTC")


def normalize_hour(value) -> int:
    try:
        hour = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(23, hour))


def is_in_quiet_window(hour: int, start: int, end: int) -> bool:
    """
    hour в [0, 23]. Интервал [start, end) по локальным часам.
    Если start == end — окно пустое (не тихо).
    Если start < end — внутри суток (например 1–7).
    Если start > end — через полночь (например 23–8).
    """
    start = normalize_hour(start)
    end = normalize_hour(end)
    hour = normalize_hour(hour)
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def current_local_hour(now: datetime | None = None) -> int:
    dt = now or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_app_tz()).hour


def format_quiet_range(start: int, end: int, lang: str = "ru") -> str:
    start = normalize_hour(start)
    end = normalize_hour(end)
    tz_name = datetime.now(_app_tz()).tzname() or TIMEZONE
    return f"{start:02d}:00–{end:02d}:00 ({tz_name})"
