"""Действия под алертом: игнор канала 24ч."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery

from core.channel_mute import mute_channel
from database.database import User
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _user_lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


@router.callback_query(F.data.startswith("alert:mute:"))
async def handle_mute_channel_24h(callback: CallbackQuery):
    user = User.get_or_none(User.user_id == callback.from_user.id)
    lang = _user_lang(user) if user else "ru"

    try:
        chat_id = int(callback.data.rsplit(":", 1)[-1])
    except (TypeError, ValueError):
        await callback.answer(t("alert_mute_invalid", lang=lang), show_alert=True)
        return

    ttl = await mute_channel(callback.from_user.id, chat_id)
    hours = max(1, ttl // 3600)
    logger.info(
        "channel_muted",
        user_id=callback.from_user.id,
        chat_id=chat_id,
        ttl_seconds=ttl,
    )
    await callback.answer(
        t("alert_mute_ok", lang=lang, hours=hours, chat_id=chat_id),
        show_alert=True,
    )
