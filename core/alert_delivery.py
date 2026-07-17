"""Доставка алертов и дайджеста: личка, группа, топик."""

from __future__ import annotations

from typing import Any

import structlog
from aiogram.types import InlineKeyboardMarkup

from database.database import User, get_user_alert_destination

logger = structlog.get_logger(__name__)


async def deliver_alert(
    user_id: int,
    *,
    text: str,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
    reply_markup: InlineKeyboardMarkup | None = None,
    notify_group_failure: bool = True,
) -> dict[str, bool]:
    """
    Отправляет сообщение по настройкам alert_to_dm / alert_to_group.
    Возвращает {"dm": bool, "group": bool}.
    """
    from system.dispatcher import bot

    dest = get_user_alert_destination(int(user_id))
    results = {"dm": False, "group": False}
    send_kwargs: dict[str, Any] = {
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if reply_markup is not None:
        send_kwargs["reply_markup"] = reply_markup

    if dest["alert_to_dm"]:
        try:
            await bot.send_message(chat_id=int(user_id), **send_kwargs)
            results["dm"] = True
        except Exception as e:
            logger.warning("alert_dm_delivery_failed", user_id=user_id, error=str(e))

    if dest["alert_to_group"] and dest.get("alert_chat_id"):
        group_kwargs = dict(send_kwargs)
        group_kwargs["chat_id"] = int(dest["alert_chat_id"])
        thread_id = dest.get("alert_thread_id")
        if thread_id is not None:
            group_kwargs["message_thread_id"] = int(thread_id)
        try:
            await bot.send_message(**group_kwargs)
            results["group"] = True
        except Exception as e:
            logger.warning(
                "alert_group_delivery_failed",
                user_id=user_id,
                chat_id=dest.get("alert_chat_id"),
                error=str(e),
            )
            if notify_group_failure:
                await _notify_group_failure(int(user_id), str(e), dm_ok=results["dm"])

    elif dest["alert_to_group"] and not dest.get("alert_chat_id"):
        if notify_group_failure:
            await _notify_group_failure(int(user_id), "not_bound", dm_ok=results["dm"])

    return results


async def _notify_group_failure(user_id: int, error: str, *, dm_ok: bool) -> None:
    from locales.locales import t
    from system.dispatcher import bot

    user = User.get_or_none(User.user_id == user_id)
    lang = "ru"
    if user and user.language and user.language != "unset":
        lang = user.language

    if error == "not_bound":
        key = "alert_destination_group_not_bound"
    elif dm_ok:
        key = "alert_group_delivery_failed"
    else:
        key = "alert_group_delivery_failed_only"

    try:
        await bot.send_message(
            chat_id=int(user_id),
            text=t(key, lang=lang, error=error[:200] if error != "not_bound" else ""),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("alert_group_failure_notify_error", user_id=user_id, error=str(e))
