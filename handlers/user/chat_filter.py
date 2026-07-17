"""Фильтр алертов: все / только каналы / только группы."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.chat_filter import normalize_chat_filter
from database.database import User, get_user_chat_filter, set_user_chat_filter
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import chat_filter_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _filter_text(lang: str, mode: str) -> str:
    return t(
        "chat_filter_message",
        lang=lang,
        current=t(f"chat_filter_{mode}_name", lang=lang),
    )


@router.callback_query(F.data.in_({"menu:chat_filter", "back:chat_filter"}))
async def handle_chat_filter_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    mode = get_user_chat_filter(callback.from_user.id)
    await edit_or_answer(
        callback,
        _filter_text(lang, mode),
        reply_markup=chat_filter_keyboard(lang=lang, current=mode),
    )


@router.callback_query(F.data.startswith("menu:chat_filter:"))
async def handle_chat_filter_set(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    mode = normalize_chat_filter(callback.data.rsplit(":", 1)[-1])
    mode = set_user_chat_filter(callback.from_user.id, mode)
    await callback.answer(
        t("chat_filter_saved", lang=lang, mode=t(f"chat_filter_{mode}_name", lang=lang))
    )
    await edit_or_answer(
        callback,
        _filter_text(lang, mode),
        reply_markup=chat_filter_keyboard(lang=lang, current=mode),
    )
