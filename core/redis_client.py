"""Redis client with connect/ping lifecycle (по образцу bedolaga CacheService)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from core.config import REDIS_URL

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = structlog.get_logger(__name__)

_redis: Redis | None = None
_connected: bool = False


def get_redis() -> Redis | None:
    """Return connected Redis client, or None if unavailable."""
    if not _connected:
        return None
    return _redis


async def connect_redis() -> bool:
    """Connect and ping Redis. Returns True on success."""
    global _redis, _connected

    if not REDIS_URL:
        logger.warning(
            "REDIS_URL не задан — отслеживание и FSM не переживут перезапуск. "
            "Для Docker: REDIS_URL=redis://redis:6379/0"
        )
        _connected = False
        return False

    try:
        from redis.asyncio import Redis

        if _redis is not None:
            try:
                await _redis.aclose()
            except Exception:
                pass
            _redis = None

        _redis = Redis.from_url(REDIS_URL, decode_responses=True)
        await _redis.ping()
        _connected = True
        logger.info("Подключение к Redis установлено", url=REDIS_URL)
        return True
    except Exception as e:
        logger.warning("Не удалось подключиться к Redis", error=e, url=REDIS_URL)
        _connected = False
        if _redis is not None:
            try:
                await _redis.aclose()
            except Exception:
                pass
            _redis = None
        return False


async def close_redis() -> None:
    global _redis, _connected
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception as e:
            logger.warning("Ошибка закрытия Redis", error=e)
        _redis = None
    _connected = False


def is_redis_connected() -> bool:
    return _connected


async def ping_redis() -> bool:
    """Живой ping; при ошибке помечает клиент как отключённый."""
    global _connected
    redis = get_redis()
    if redis is None:
        return False
    try:
        await redis.ping()
        return True
    except Exception as e:
        logger.warning("Redis ping failed", error=e)
        _connected = False
        return False
