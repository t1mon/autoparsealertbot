"""Временный игнор канала для алертов (Redis + fallback)."""

from __future__ import annotations

import os
import time

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

CHANNEL_MUTE_TTL_SECONDS = int(os.getenv("CHANNEL_MUTE_TTL_SECONDS") or str(24 * 3600))
KEY_PREFIX = "alert:mute"

_fallback: dict[str, float] = {}


def _mute_key(user_id, chat_id: int) -> str:
    return f"{KEY_PREFIX}:{user_id}:{int(chat_id)}"


async def mute_channel(user_id, chat_id: int, *, ttl_seconds: int | None = None) -> int:
    """
    Глушит алерты из chat_id для пользователя на ttl секунд.
    Returns: TTL в секундах.
    """
    ttl = int(ttl_seconds or CHANNEL_MUTE_TTL_SECONDS)
    key = _mute_key(user_id, chat_id)
    redis = get_redis()
    if redis is not None:
        try:
            await redis.set(key, "1", ex=ttl)
            return ttl
        except Exception as e:
            logger.warning("channel_mute_redis_error", error=str(e), key=key)

    _fallback[key] = time.time() + ttl
    return ttl


async def is_channel_muted(user_id, chat_id: int) -> bool:
    key = _mute_key(user_id, chat_id)
    redis = get_redis()
    if redis is not None:
        try:
            return bool(await redis.exists(key))
        except Exception as e:
            logger.warning("channel_mute_exists_error", error=str(e), key=key)

    exp = _fallback.get(key)
    if not exp:
        return False
    if exp <= time.time():
        _fallback.pop(key, None)
        return False
    return True


async def unmute_channel(user_id, chat_id: int) -> None:
    key = _mute_key(user_id, chat_id)
    redis = get_redis()
    if redis is not None:
        try:
            await redis.delete(key)
        except Exception as e:
            logger.warning("channel_unmute_redis_error", error=str(e), key=key)
    _fallback.pop(key, None)
