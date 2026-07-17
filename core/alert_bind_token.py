"""Одноразовый токен для безопасной привязки группы алертов."""

from __future__ import annotations

import os
import secrets
import string
import time

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

BIND_TOKEN_TTL_SECONDS = int(os.getenv("ALERT_BIND_TOKEN_TTL_SECONDS") or "900")
TOKEN_PREFIX = "alert_bind:token"
USER_PREFIX = "alert_bind:user"

_ALPHABET = string.ascii_uppercase + string.digits
_TOKEN_LEN = 6

# fallback: token -> (user_id, expires_at)
_fallback_tokens: dict[str, tuple[int, float]] = {}
# fallback: user_id -> token
_fallback_user: dict[int, str] = {}


def _normalize_token(token: str | None) -> str:
    return (token or "").strip().upper()


def _generate_token_value() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_TOKEN_LEN))


def _token_key(token: str) -> str:
    return f"{TOKEN_PREFIX}:{token}"


def _user_key(user_id: int) -> str:
    return f"{USER_PREFIX}:{int(user_id)}"


def _fallback_drop_token(token: str) -> None:
    entry = _fallback_tokens.pop(token, None)
    if entry:
        uid = entry[0]
        if _fallback_user.get(uid) == token:
            _fallback_user.pop(uid, None)


def _fallback_purge(now: float) -> None:
    expired = [tok for tok, (_, exp) in _fallback_tokens.items() if exp <= now]
    for tok in expired:
        _fallback_drop_token(tok)


async def issue_bind_token(user_id: int) -> str:
    """Выдаёт новый токен; предыдущий для пользователя аннулируется."""
    uid = int(user_id)
    token = _generate_token_value()
    redis = get_redis()

    if redis is not None:
        try:
            old = await redis.get(_user_key(uid))
            if old:
                await redis.delete(_token_key(old))
            pipe = redis.pipeline()
            pipe.set(_token_key(token), str(uid), ex=BIND_TOKEN_TTL_SECONDS)
            pipe.set(_user_key(uid), token, ex=BIND_TOKEN_TTL_SECONDS)
            await pipe.execute()
            return token
        except Exception as e:
            logger.warning("alert_bind_token_redis_issue_error", error=str(e), user_id=uid)

    now = time.time()
    _fallback_purge(now)
    old = _fallback_user.pop(uid, None)
    if old:
        _fallback_tokens.pop(old, None)
    expires = now + BIND_TOKEN_TTL_SECONDS
    _fallback_tokens[token] = (uid, expires)
    _fallback_user[uid] = token
    return token


async def resolve_bind_token(token: str) -> int | None:
    """Возвращает user_id владельца токена или None."""
    token = _normalize_token(token)
    if not token or len(token) != _TOKEN_LEN:
        return None

    redis = get_redis()
    if redis is not None:
        try:
            raw = await redis.get(_token_key(token))
            return int(raw) if raw else None
        except Exception as e:
            logger.warning("alert_bind_token_redis_resolve_error", error=str(e))

    entry = _fallback_tokens.get(token)
    if not entry:
        return None
    uid, expires = entry
    if time.time() > expires:
        _fallback_drop_token(token)
        return None
    return uid


async def consume_bind_token(token: str, user_id: int) -> bool:
    """Списывает токен, если он принадлежит user_id."""
    token = _normalize_token(token)
    owner = await resolve_bind_token(token)
    if owner is None or int(owner) != int(user_id):
        return False

    redis = get_redis()
    if redis is not None:
        try:
            await redis.delete(_token_key(token))
            await redis.delete(_user_key(int(user_id)))
            return True
        except Exception as e:
            logger.warning("alert_bind_token_redis_consume_error", error=str(e))

    _fallback_drop_token(token)
    return True
