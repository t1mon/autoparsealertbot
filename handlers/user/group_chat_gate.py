"""В группах/топиках — только bind/leads; остальное перенаправляем в личку."""

from __future__ import annotations

import time

import structlog
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.database import User
from locales.locales import t
from system.filters import IsAllowedUser, IsGroupChat

router = Router(name="group_chat_gate")
router.message.filter(IsGroupChat(), IsAllowedUser())
router.callback_query.filter(IsGroupChat(), IsAllowedUser())
logger = structlog.get_logger(__name__)

_GROUP_COMMANDS = frozenset({"bind_alerts", "leads", "leads_help"})
_recent_replies: dict[int, float] = {}
_REPLY_COOLDOWN_SEC = 60


def _pick_lang(message: Message | CallbackQuery) -> str:
    user = message.from_user
    db_user = User.get_or_none(User.user_id == user.id)
    if db_user and db_user.language and db_user.language != "unset":
        return db_user.language
    code = (getattr(user, "language_code", None) or "ru").lower()
    return "en" if code.startswith("en") else "ru"


async def _bot_username(message: Message | CallbackQuery) -> str:
    me = await message.bot.get_me()
    return me.username or "bot"


def _open_bot_keyboard(lang: str, username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("group_chat_open_bot_button", lang=lang),
                    url=f"https://t.me/{username}",
                )
            ]
        ]
    )


def _is_allowed_group_command(text: str | None) -> bool:
    if not text or not text.startswith("/"):
        return False
    cmd = text.strip().split()[0].lstrip("/").split("@", 1)[0].lower()
    return cmd in _GROUP_COMMANDS


@router.message(CommandStart())
async def group_start(message: Message) -> None:
    lang = _pick_lang(message)
    username = await _bot_username(message)
    await message.answer(
        t("group_chat_use_private", lang=lang, bot_username=username),
        reply_markup=_open_bot_keyboard(lang, username),
        parse_mode="HTML",
    )


@router.message(F.text.startswith("/"))
async def group_other_command(message: Message) -> None:
    # /leads и /bind_alerts обрабатывают свои роутеры выше по цепочке
    if _is_allowed_group_command(message.text):
        return
    lang = _pick_lang(message)
    username = await _bot_username(message)
    await message.answer(
        t("group_chat_command_private", lang=lang, bot_username=username),
        reply_markup=_open_bot_keyboard(lang, username),
        parse_mode="HTML",
    )


@router.callback_query()
async def group_callback(callback: CallbackQuery) -> None:
    lang = _pick_lang(callback)
    await callback.answer(t("group_chat_callback_private", lang=lang), show_alert=True)


@router.message(F.text)
async def group_text(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        return
    if _is_allowed_group_command(message.text):
        return
    uid = message.from_user.id
    now = time.time()
    if now - _recent_replies.get(uid, 0) < _REPLY_COOLDOWN_SEC:
        return
    _recent_replies[uid] = now
    lang = _pick_lang(message)
    username = await _bot_username(message)
    await message.answer(
        t("group_chat_use_private_short", lang=lang, bot_username=username),
        reply_markup=_open_bot_keyboard(lang, username),
        parse_mode="HTML",
    )
