"""Helpers for Inline menu navigation."""

from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from account_manager.parser import is_tracking_marked
from core.config import ADMIN_USER_IDS
from database.database import User
from keyboards.user.keyboards import get_lang_keyboard, resolve_main_keyboard
from locales.locales import t


def get_user_lang(user_id: int) -> str:
    try:
        user = User.get(User.user_id == user_id)
        return user.language if user.language != "unset" else "ru"
    except Exception:
        return "ru"


def generate_welcome_message(user_language: str, user_tg_id: int) -> str:
    from database.database import (
        get_keywords_count,
        get_session_count,
        get_tracked_channels_count,
        getting_number_records_database,
    )

    version = "0.0.9"
    return t(
        "welcome_message_template",
        lang=user_language,
        version=version,
        groups_count=getting_number_records_database(),
        count=get_session_count(user_id=user_tg_id),
        get_groups=get_tracked_channels_count(user_id=user_tg_id),
        keywords_count=get_keywords_count(user_id=user_tg_id),
    )


async def edit_or_answer(
    event: Message | CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
) -> Message:
    """Edit message for callbacks; otherwise send a new message."""
    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass
        try:
            return await event.message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except Exception:
            return await event.message.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
    return await event.answer(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


async def get_main_reply_markup(user_id: int, lang: str, is_admin: bool):
    return resolve_main_keyboard(
        lang,
        tracking_active=await is_tracking_marked(user_id),
        is_admin=is_admin,
    )


async def show_main_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Show welcome + main Inline keyboard. Works for Message and CallbackQuery."""
    if state is not None:
        await state.clear()

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass

    tg_user = event.from_user
    user_id = tg_user.id

    try:
        user = User.get(User.user_id == user_id)
    except User.DoesNotExist:
        await edit_or_answer(
            event,
            "👋 Привет! Пожалуйста, выберите язык / Please choose your language:",
            reply_markup=get_lang_keyboard(),
            parse_mode=None,
        )
        return

    if user.language == "unset":
        await edit_or_answer(
            event,
            "👋 Привет! Пожалуйста, выберите язык / Please choose your language:",
            reply_markup=get_lang_keyboard(),
            parse_mode=None,
        )
        return

    is_admin = user_id in ADMIN_USER_IDS
    markup = await get_main_reply_markup(user_id, user.language, is_admin)
    text = generate_welcome_message(user.language, user_id)

    if isinstance(event, Message):
        await event.answer(reply_markup=ReplyKeyboardRemove())
        await event.answer(text=text, reply_markup=markup, parse_mode="HTML")
    else:
        await edit_or_answer(event, text, reply_markup=markup, parse_mode="HTML")
