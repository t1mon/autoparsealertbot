"""Дайджест совпадений: одно сообщение за интервал."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.digest import flush_digest
from database.database import User, get_user_digest_settings, set_user_digest_settings
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import digest_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _digest_text(lang: str, user_id: int) -> str:
    cfg = get_user_digest_settings(user_id)
    status = (
        t("digest_status_on", lang=lang)
        if cfg["enabled"]
        else t("digest_status_off", lang=lang)
    )
    return t(
        "digest_settings_message",
        lang=lang,
        status=status,
        interval=cfg["interval_min"],
    )


async def show_digest_settings(callback: CallbackQuery) -> None:
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    cfg = get_user_digest_settings(callback.from_user.id)
    await edit_or_answer(
        callback,
        _digest_text(lang, callback.from_user.id),
        reply_markup=digest_keyboard(
            lang,
            enabled=cfg["enabled"],
            interval_min=cfg["interval_min"],
        ),
    )


@router.callback_query(F.data.in_({"menu:digest", "back:digest"}))
async def handle_digest_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_digest_settings(callback)


@router.callback_query(F.data == "menu:digest:toggle")
async def handle_digest_toggle(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    cfg = get_user_digest_settings(callback.from_user.id)
    enabling = not cfg["enabled"]
    cfg = set_user_digest_settings(callback.from_user.id, enabled=enabling)
    if not enabling:
        sent = await flush_digest(callback.from_user.id, lang, force=True)
        if sent:
            await callback.answer(t("digest_flushed_on_disable", lang=lang, count=sent))
        else:
            await callback.answer(t("digest_toggled_off", lang=lang))
    else:
        await callback.answer(t("digest_toggled_on", lang=lang))
    await show_digest_settings(callback)


@router.callback_query(F.data.startswith("menu:digest:interval:"))
async def handle_digest_interval(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    try:
        minutes = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer()
        return
    cfg = set_user_digest_settings(
        callback.from_user.id,
        enabled=True,
        interval_min=minutes,
    )
    await callback.answer(
        t("digest_interval_saved", lang=lang, interval=cfg["interval_min"])
    )
    await show_digest_settings(callback)


@router.callback_query(F.data == "menu:digest:flush")
async def handle_digest_flush_now(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    sent = await flush_digest(callback.from_user.id, lang, force=True)
    if sent:
        await callback.answer(t("digest_flush_ok", lang=lang, count=sent), show_alert=True)
    else:
        await callback.answer(t("digest_flush_empty", lang=lang), show_alert=True)
    await show_digest_settings(callback)
