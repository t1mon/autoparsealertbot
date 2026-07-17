"""Выбор пресета шаблона алерта: полный / компактный / минимальный."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from core.alert_template import normalize_alert_template
from database.database import User, get_user_alert_template, set_user_alert_template
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import alert_template_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _template_text(lang: str, template: str) -> str:
    return t(
        "alert_template_message",
        lang=lang,
        current=t(f"alert_template_{template}_name", lang=lang),
    )


@router.callback_query(F.data.in_({"menu:alert_template", "back:alert_template"}))
async def handle_alert_template_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    template = get_user_alert_template(callback.from_user.id)
    await edit_or_answer(
        callback,
        _template_text(lang, template),
        reply_markup=alert_template_keyboard(lang=lang, current=template),
    )


@router.callback_query(F.data.startswith("menu:alert_template:"))
async def handle_alert_template_set(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    template = normalize_alert_template(callback.data.rsplit(":", 1)[-1])
    template = set_user_alert_template(callback.from_user.id, template)
    await callback.answer(
        t(
            "alert_template_saved",
            lang=lang,
            mode=t(f"alert_template_{template}_name", lang=lang),
        )
    )
    await edit_or_answer(
        callback,
        _template_text(lang, template),
        reply_markup=alert_template_keyboard(lang=lang, current=template),
    )
