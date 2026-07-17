"""Безопасные лимиты и паузы при массовых вступлениях в каналы."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field

import structlog

from account_manager.subscription import subscription_telegram
from core.config import (
    JOIN_BATCH_LIMIT,
    JOIN_DAILY_LIMIT,
    JOIN_DELAY_MAX,
    JOIN_DELAY_MIN,
    JOIN_ERROR_DELAY_MAX,
    JOIN_ERROR_DELAY_MIN,
    JOIN_NOTIFY_EVERY,
)

logger = structlog.get_logger(__name__)

# Fallback суточного счётчика, если Redis недоступен (ключ = user_id:YYYYMMDD)
_memory_daily: dict[str, int] = {}


@dataclass
class JoinBatchStats:
    joined: int = 0
    already: int = 0
    error: int = 0
    skipped_limit: int = 0
    attempted: int = 0
    stopped: bool = False
    last_channel: str | None = None
    notified_channels: list[str] = field(default_factory=list)


def join_success_delay() -> int:
    lo = max(1, JOIN_DELAY_MIN)
    hi = max(lo, JOIN_DELAY_MAX)
    return random.randint(lo, hi)


def join_error_delay() -> int:
    lo = max(1, JOIN_ERROR_DELAY_MIN)
    hi = max(lo, JOIN_ERROR_DELAY_MAX)
    return random.randint(lo, hi)


def apply_batch_cap(channels: list[str], limit: int | None = None) -> tuple[list[str], int]:
    """Обрезает список до лимита за проход. Возвращает (slice, original_len)."""
    cap = JOIN_BATCH_LIMIT if limit is None else limit
    cap = max(1, cap)
    total = len(channels)
    if total <= cap:
        return channels, total
    return channels[:cap], total


async def _daily_key(user_id: int) -> str:
    day = time.strftime("%Y%m%d", time.gmtime())
    return f"join_daily:{user_id}:{day}"


async def get_daily_joins(user_id: int) -> int:
    key = await _daily_key(user_id)
    try:
        from core.redis_client import get_redis

        redis = get_redis()
        if redis is not None:
            raw = await redis.get(key)
            return int(raw) if raw else 0
    except Exception as e:
        logger.warning("join_daily_redis_get_failed", error=str(e), user_id=user_id)
    return _memory_daily.get(key, 0)


async def remaining_daily_joins(user_id: int) -> int:
    used = await get_daily_joins(user_id)
    return max(0, JOIN_DAILY_LIMIT - used)


async def incr_daily_joins(user_id: int, n: int = 1) -> int:
    """Увеличивает суточный счётчик новых join. Возвращает новое значение."""
    if n <= 0:
        return await get_daily_joins(user_id)
    key = await _daily_key(user_id)
    try:
        from core.redis_client import get_redis

        redis = get_redis()
        if redis is not None:
            val = await redis.incrby(key, n)
            # TTL до конца следующих ~2 суток (чтобы ключ не висел вечно)
            await redis.expire(key, 60 * 60 * 48)
            return int(val)
    except Exception as e:
        logger.warning("join_daily_redis_incr_failed", error=str(e), user_id=user_id)
    _memory_daily[key] = _memory_daily.get(key, 0) + n
    return _memory_daily[key]


async def sleep_interruptible(seconds: int, stop_event: asyncio.Event | None = None) -> bool:
    """Sleep; True если прервано stop_event."""
    if seconds <= 0:
        return bool(stop_event and stop_event.is_set())
    if stop_event is None:
        await asyncio.sleep(seconds)
        return False
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
        return True
    except asyncio.TimeoutError:
        return False


async def join_channels_safely(
    *,
    client,
    channels: list[str],
    user_id: int,
    stop_event: asyncio.Event | None = None,
    on_progress=None,
) -> JoinBatchStats:
    """
    Вступает в каналы с паузами и лимитами.

    on_progress(stats, channel, result, delay) — опциональный колбэк после каждой попытки
    (кроме already без паузы можно не звать часто — зовём всегда).
    """
    stats = JoinBatchStats()
    remaining = await remaining_daily_joins(user_id)
    if remaining <= 0:
        stats.skipped_limit = len(channels)
        logger.warning("join_daily_limit_reached", user_id=user_id, limit=JOIN_DAILY_LIMIT)
        return stats

    work = channels[:remaining]
    stats.skipped_limit = len(channels) - len(work)

    for channel in work:
        if stop_event and stop_event.is_set():
            stats.stopped = True
            break

        stats.attempted += 1
        stats.last_channel = channel
        try:
            join_result = await subscription_telegram(
                client=client, target_username=channel, user_id=int(user_id)
            )
            result = join_result.outcome
        except Exception as e:
            logger.exception("join_channels_safely_error", channel=channel, error=e)
            result = "error"

        if result == "joined":
            stats.joined += 1
            await incr_daily_joins(user_id, 1)
            delay = join_success_delay()
        elif result == "already":
            stats.already += 1
            delay = 0
        else:
            stats.error += 1
            delay = join_error_delay()

        if on_progress is not None:
            try:
                await on_progress(stats, channel, result, delay)
            except Exception as e:
                logger.warning("join_on_progress_failed", error=str(e))

        if delay > 0:
            if await sleep_interruptible(delay, stop_event):
                stats.stopped = True
                break

    return stats


def should_notify_join(joined_count: int) -> bool:
    """Редкие уведомления о новых join (каждые N, плюс первый)."""
    every = JOIN_NOTIFY_EVERY
    if every <= 0:
        return False
    if joined_count == 1:
        return True
    return joined_count % every == 0
