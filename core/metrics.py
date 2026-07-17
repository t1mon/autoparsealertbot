"""Лёгкие метрики: совпадения и FloodWait по часу (Redis + fallback)."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

_fallback: dict[str, int] = {}
# user_id_str → unix ts старта tracking в этом процессе
tracking_started_at: dict[str, float] = {}


def _hour_bucket() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H")


def _metric_key(kind: str, hour: str | None = None) -> str:
    return f"metrics:{kind}:{hour or _hour_bucket()}"


async def incr_metric(kind: str, amount: int = 1) -> None:
    key = _metric_key(kind)
    redis = get_redis()
    if redis is not None:
        try:
            await redis.incrby(key, amount)
            await redis.expire(key, 48 * 3600)
            return
        except Exception as e:
            logger.debug("metrics_redis_incr_error", kind=kind, error=str(e))
    _fallback[key] = _fallback.get(key, 0) + amount


async def record_match() -> None:
    await incr_metric("matches")


async def record_floodwait() -> None:
    await incr_metric("floodwaits")


async def get_metric_count(kind: str, hour: str | None = None) -> int:
    key = _metric_key(kind, hour)
    redis = get_redis()
    if redis is not None:
        try:
            raw = await redis.get(key)
            return int(raw) if raw is not None else 0
        except Exception as e:
            logger.debug("metrics_redis_get_error", kind=kind, error=str(e))
    return int(_fallback.get(key, 0))


def mark_tracking_started(user_id) -> None:
    tracking_started_at[str(user_id)] = time.time()


def clear_tracking_started(user_id) -> None:
    tracking_started_at.pop(str(user_id), None)


def tracking_uptime_seconds(user_id) -> int | None:
    started = tracking_started_at.get(str(user_id))
    if started is None:
        return None
    return max(0, int(time.time() - started))


def format_uptime(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds}с"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}м"
    hours = minutes // 60
    rem = minutes % 60
    return f"{hours}ч {rem}м"
