"""Дедуп алертов: Redis SET NX + TTL, fallback в память процесса."""

from __future__ import annotations

import os
import time

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

ALERT_DEDUP_TTL_SECONDS = int(os.getenv("ALERT_DEDUP_TTL_SECONDS") or str(7 * 24 * 3600))
KEY_PREFIX = "alert:dedup"

# Fallback без Redis: key → expires_at
_fallback: dict[str, float] = {}
_FALLBACK_MAX = 50_000


def _dedup_key(user_id, chat_id: int, message_id: int) -> str:
    return f"{KEY_PREFIX}:{user_id}:{chat_id}:{message_id}"


def _fallback_purge(now: float) -> None:
    if len(_fallback) < _FALLBACK_MAX:
        expired = [k for k, exp in _fallback.items() if exp <= now]
        for k in expired[:1000]:
            _fallback.pop(k, None)
        return
    # жёсткая очистка при переполнении
    for k, exp in list(_fallback.items()):
        if exp <= now:
            _fallback.pop(k, None)
    if len(_fallback) >= _FALLBACK_MAX:
        oldest = sorted(_fallback.items(), key=lambda x: x[1])[: _FALLBACK_MAX // 5]
        for k, _ in oldest:
            _fallback.pop(k, None)


async def claim_alert(user_id, chat_id: int, message_id: int) -> bool:
    """
    Атомарно «захватывает» алерт.

    Returns:
        True — первый раз, можно слать.
        False — уже видели (дубликат), пропускаем.
    """
    key = _dedup_key(user_id, int(chat_id), int(message_id))
    redis = get_redis()
    if redis is not None:
        try:
            ok = await redis.set(key, "1", nx=True, ex=ALERT_DEDUP_TTL_SECONDS)
            return bool(ok)
        except Exception as e:
            logger.warning("alert_dedup_redis_error", error=str(e), key=key)

    now = time.time()
    _fallback_purge(now)
    if key in _fallback and _fallback[key] > now:
        return False
    _fallback[key] = now + ALERT_DEDUP_TTL_SECONDS
    return True


async def was_seen(user_id, chat_id: int, message_id: int) -> bool:
    """True, если алерт уже помечен (без claim)."""
    key = _dedup_key(user_id, int(chat_id), int(message_id))
    redis = get_redis()
    if redis is not None:
        try:
            return bool(await redis.exists(key))
        except Exception as e:
            logger.warning("alert_dedup_exists_error", error=str(e), key=key)

    now = time.time()
    exp = _fallback.get(key)
    return bool(exp and exp > now)
