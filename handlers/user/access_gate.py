"""Сообщения для пользователей без доступа (закрытая бета)."""

from __future__ import annotations

import time

import structlog
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.config import DEVELOPER_CONTACT_URL, DEVELOPER_USERNAME
from locales.locales import t

from system.filters import IsAccessRestricted

router = Router(name="access_gate")
router.message.filter(IsAccessRestricted())
router.callback_query.filter(IsAccessRestricted())
logger = structlog.get_logger(__name__)

# user_id → last short-reply timestamp
_recent_replies: dict[int, float] = {}
_SHORT_REPLY_COOLDOWN_SEC = 3600


def _pick_lang(message: Message | CallbackQuery) -> str:
    user = message.from_user if isinstance(message, Message) else message.from_user
    code = (getattr(user, "language_code", None) or "ru").lower()
    return "en" if code.startswith("en") else "ru"


def access_denied_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("access_contact_developer_button", lang=lang),
                    url=DEVELOPER_CONTACT_URL,
                )
            ]
        ]
    )


def _full_access_text(lang: str) -> str:
    return t(
        "access_denied_full",
        lang=lang,
        developer=f"@{DEVELOPER_USERNAME}",
    )


@router.message(CommandStart())
async def restricted_start(message: Message) -> None:
    lang = _pick_lang(message)
    logger.info(
        "access_denied_start",
        user_id=message.from_user.id,
        username=message.from_user.username,
    )
    if message.chat.type in ("group", "supergroup"):
        me = await message.bot.get_me()
        username = me.username or "bot"
        await message.answer(
            t("access_denied_group", lang=lang, bot_username=username),
            reply_markup=access_denied_keyboard(lang),
            parse_mode="HTML",
        )
        return
    await message.answer(
        _full_access_text(lang),
        reply_markup=access_denied_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query()
async def restricted_callback(callback: CallbackQuery) -> None:
    lang = _pick_lang(callback)
    await callback.answer(t("access_denied_short", lang=lang), show_alert=True)


@router.message(F.text)
async def restricted_text_message(message: Message) -> None:
    if message.chat.type in ("group", "supergroup"):
        return
    lang = _pick_lang(message)
    uid = message.from_user.id
    now = time.time()
    last = _recent_replies.get(uid, 0)
    if now - last < _SHORT_REPLY_COOLDOWN_SEC:
        return
    _recent_replies[uid] = now
    if len(_recent_replies) > 5000:
        cutoff = now - _SHORT_REPLY_COOLDOWN_SEC
        for key, ts in list(_recent_replies.items()):
            if ts < cutoff:
                _recent_replies.pop(key, None)
    logger.info("access_denied_message", user_id=uid, username=message.from_user.username)
    await message.answer(
        t("access_denied_short", lang=lang, developer=f"@{DEVELOPER_USERNAME}"),
        reply_markup=access_denied_keyboard(lang),
        parse_mode="HTML",
    )


@router.message()
async def restricted_other_message(message: Message) -> None:
    """Файлы, стикеры и прочее — короткий ответ."""
    if message.chat.type in ("group", "supergroup"):
        return
    await restricted_text_message(message)
