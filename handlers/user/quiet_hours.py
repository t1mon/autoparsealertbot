"""Тихие часы: не слать алерты ночью."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.quiet_hours import format_quiet_range
from database.database import User, get_user_quiet_hours, set_user_quiet_hours
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import quiet_hours_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _quiet_hours_text(lang: str, user_id: int) -> str:
    cfg = get_user_quiet_hours(user_id)
    status = (
        t("quiet_hours_status_on", lang=lang)
        if cfg["enabled"]
        else t("quiet_hours_status_off", lang=lang)
    )
    window = format_quiet_range(cfg["start"], cfg["end"], lang=lang)
    return t(
        "quiet_hours_message",
        lang=lang,
        status=status,
        window=window,
    )


async def show_quiet_hours(callback: CallbackQuery) -> None:
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    cfg = get_user_quiet_hours(callback.from_user.id)
    await edit_or_answer(
        callback,
        _quiet_hours_text(lang, callback.from_user.id),
        reply_markup=quiet_hours_keyboard(
            lang,
            enabled=cfg["enabled"],
            start=cfg["start"],
            end=cfg["end"],
        ),
    )


@router.callback_query(F.data.in_({"menu:quiet_hours", "back:quiet_hours"}))
async def handle_quiet_hours_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_quiet_hours(callback)


@router.callback_query(F.data == "menu:quiet_hours:toggle")
async def handle_quiet_hours_toggle(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    cfg = get_user_quiet_hours(callback.from_user.id)
    cfg = set_user_quiet_hours(callback.from_user.id, enabled=not cfg["enabled"])
    await callback.answer(
        t(
            "quiet_hours_toggled_on" if cfg["enabled"] else "quiet_hours_toggled_off",
            lang=lang,
        )
    )
    await show_quiet_hours(callback)


@router.callback_query(F.data.startswith("menu:quiet_hours:preset:"))
async def handle_quiet_hours_preset(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    try:
        _, _, _, start_s, end_s = callback.data.split(":", 4)
        start, end = int(start_s), int(end_s)
    except (ValueError, TypeError):
        await callback.answer()
        return

    cfg = set_user_quiet_hours(
        callback.from_user.id,
        enabled=True,
        start=start,
        end=end,
    )
    await callback.answer(
        t(
            "quiet_hours_preset_saved",
            lang=lang,
            window=format_quiet_range(cfg["start"], cfg["end"], lang=lang),
        )
    )
    await show_quiet_hours(callback)
