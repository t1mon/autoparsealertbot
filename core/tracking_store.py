from __future__ import annotations

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

ACTIVE_SET_KEY = "tracking:active"

# Fallback для локальной разработки без Redis
_fallback_active: set[str] = set()


def _user_key(user_id) -> str:
    return str(user_id)


async def mark_active(user_id) -> None:
    key = _user_key(user_id)
    redis = get_redis()
    if redis is not None:
        await redis.sadd(ACTIVE_SET_KEY, key)
        logger.debug("Отслеживание сохранено в Redis", user_id=key)
        return
    logger.warning(
        "Redis недоступен — отслеживание только в памяти процесса",
        user_id=key,
    )
    _fallback_active.add(key)


async def unmark_active(user_id) -> None:
    key = _user_key(user_id)
    redis = get_redis()
    if redis is not None:
        await redis.srem(ACTIVE_SET_KEY, key)
        return
    _fallback_active.discard(key)


async def is_marked(user_id) -> bool:
    key = _user_key(user_id)
    redis = get_redis()
    if redis is not None:
        return bool(await redis.sismember(ACTIVE_SET_KEY, key))
    return key in _fallback_active


async def list_active() -> list[int]:
    redis = get_redis()
    if redis is not None:
        members = await redis.smembers(ACTIVE_SET_KEY)
        result: list[int] = []
        for member in members:
            try:
                result.append(int(member))
            except ValueError:
                logger.warning("Некорректный user_id в Redis", key=ACTIVE_SET_KEY, member=member)
        return result
    return [int(uid) for uid in _fallback_active]
