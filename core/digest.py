"""Дайджест алертов: буфер в Redis + периодическая сводка."""

from __future__ import annotations

import html
import json
import os
import time
from typing import Any

import structlog

from core.redis_client import get_redis

logger = structlog.get_logger(__name__)

DIGEST_MAX_ITEMS_IN_MESSAGE = int(os.getenv("DIGEST_MAX_ITEMS") or "15")
DIGEST_FORCE_FLUSH_SIZE = int(os.getenv("DIGEST_FORCE_FLUSH_SIZE") or "40")
BUF_PREFIX = "digest:buf"
LAST_PREFIX = "digest:last"
BUF_TTL_SECONDS = 3 * 24 * 3600

_fallback_buf: dict[str, list[dict[str, Any]]] = {}
_fallback_last: dict[str, float] = {}


def _buf_key(user_id) -> str:
    return f"{BUF_PREFIX}:{user_id}"


def _last_key(user_id) -> str:
    return f"{LAST_PREFIX}:{user_id}"


def normalize_digest_interval(minutes) -> int:
    try:
        value = int(minutes)
    except (TypeError, ValueError):
        return 60
    allowed = (15, 30, 60)
    if value in allowed:
        return value
    # ближайший
    return min(allowed, key=lambda x: abs(x - value))


async def enqueue_digest_item(user_id, item: dict[str, Any]) -> int:
    """Добавляет элемент в буфер. Returns текущий размер буфера."""
    key = _buf_key(user_id)
    payload = json.dumps(item, ensure_ascii=False)
    redis = get_redis()
    if redis is not None:
        try:
            size = await redis.rpush(key, payload)
            await redis.expire(key, BUF_TTL_SECONDS)
            return int(size)
        except Exception as e:
            logger.warning("digest_enqueue_redis_error", error=str(e), user_id=user_id)

    bucket = _fallback_buf.setdefault(str(user_id), [])
    bucket.append(item)
    return len(bucket)


async def _pop_all(user_id) -> list[dict[str, Any]]:
    key = _buf_key(user_id)
    redis = get_redis()
    if redis is not None:
        try:
            raw_items = await redis.lrange(key, 0, -1)
            if raw_items:
                await redis.delete(key)
            result: list[dict[str, Any]] = []
            for raw in raw_items:
                try:
                    result.append(json.loads(raw))
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.warning("digest_pop_redis_error", error=str(e), user_id=user_id)

    bucket = _fallback_buf.pop(str(user_id), [])
    return list(bucket)


async def _get_last_flush(user_id) -> float:
    redis = get_redis()
    if redis is not None:
        try:
            raw = await redis.get(_last_key(user_id))
            return float(raw) if raw else 0.0
        except Exception:
            return 0.0
    return _fallback_last.get(str(user_id), 0.0)


async def _set_last_flush(user_id, ts: float | None = None) -> None:
    value = ts if ts is not None else time.time()
    redis = get_redis()
    if redis is not None:
        try:
            await redis.set(_last_key(user_id), str(value), ex=BUF_TTL_SECONDS)
            return
        except Exception as e:
            logger.warning("digest_last_redis_error", error=str(e), user_id=user_id)
    _fallback_last[str(user_id)] = value


async def buffer_size(user_id) -> int:
    redis = get_redis()
    if redis is not None:
        try:
            return int(await redis.llen(_buf_key(user_id)))
        except Exception:
            pass
    return len(_fallback_buf.get(str(user_id), []))


async def should_flush(user_id, interval_minutes: int, *, force: bool = False) -> bool:
    size = await buffer_size(user_id)
    if size <= 0:
        return False
    if force or size >= DIGEST_FORCE_FLUSH_SIZE:
        return True
    last = await _get_last_flush(user_id)
    if last <= 0:
        # первый элемент — ждём полный интервал от него
        await _set_last_flush(user_id)
        return False
    return (time.time() - last) >= max(60, interval_minutes * 60)


def format_digest_message(lang: str, items: list[dict[str, Any]]) -> str:
    from locales.locales import t

    total = len(items)
    shown = items[:DIGEST_MAX_ITEMS_IN_MESSAGE]
    lines: list[str] = []
    for idx, item in enumerate(shown, start=1):
        keyword = html.escape(str(item.get("keyword") or "—"))
        chat = html.escape(str(item.get("chat_title") or item.get("chat_line") or "—"))
        preview = html.escape(str(item.get("preview") or "")[:120])
        link = item.get("link") or ""
        if link and str(link).startswith("http"):
            head = f'{idx}. <a href="{html.escape(link)}"><b>{keyword}</b></a> · {chat}'
        else:
            head = f"{idx}. <b>{keyword}</b> · {chat}"
        if preview:
            lines.append(f"{head}\n   {preview}")
        else:
            lines.append(head)

    more = total - len(shown)
    more_text = t("digest_and_more", lang=lang, count=more) if more > 0 else ""
    body = "\n\n".join(lines)
    return t(
        "digest_message",
        lang=lang,
        count=total,
        items=body,
        more=more_text,
    )


async def flush_digest(user_id, lang: str, *, force: bool = False) -> int:
    """
    Отправляет накопленный дайджест, если пора.
    Returns: сколько элементов отправлено (0 если нечего / не время).
    """
    from database.database import get_user_digest_settings

    settings = get_user_digest_settings(int(user_id))
    interval = settings["interval_min"]
    if not force and not settings["enabled"]:
        # при выключенном режиме всё же можно force-flush остатка
        return 0

    if not await should_flush(user_id, interval, force=force):
        return 0

    items = await _pop_all(user_id)
    if not items:
        await _set_last_flush(user_id)
        return 0

    text = format_digest_message(lang, items)
    try:
        from core.alert_delivery import deliver_alert

        await deliver_alert(
            int(user_id),
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=None,
        )
        logger.info("digest_flushed", user_id=user_id, count=len(items))
    except Exception as e:
        logger.exception("digest_send_error", user_id=user_id, error=e)
        # вернём в буфер, чтобы не потерять
        for item in items:
            await enqueue_digest_item(user_id, item)
        return 0

    await _set_last_flush(user_id)
    return len(items)


async def digest_worker(user_id, lang: str, stop_event) -> None:
    """Фоновый цикл: раз в минуту проверяет, пора ли слать дайджест."""
    logger.info("digest_worker_started", user_id=user_id)
    try:
        while not stop_event.is_set():
            try:
                from database.database import get_user_digest_settings

                settings = get_user_digest_settings(int(user_id))
                if settings["enabled"]:
                    await flush_digest(user_id, lang)
            except Exception as e:
                logger.exception("digest_worker_tick_error", user_id=user_id, error=e)

            try:
                await asyncio_wait_stop(stop_event, 60)
            except Exception:
                break
    finally:
        # на остановке tracking — сбросить остаток
        try:
            await flush_digest(user_id, lang, force=True)
        except Exception as e:
            logger.exception("digest_final_flush_error", user_id=user_id, error=e)
        logger.info("digest_worker_stopped", user_id=user_id)


async def asyncio_wait_stop(stop_event, timeout: float) -> None:
    import asyncio

    try:
        await asyncio.wait_for(stop_event.wait(), timeout=timeout)
    except TimeoutError:
        return
