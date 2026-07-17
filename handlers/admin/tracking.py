"""Админка: кто в tracking, принудительный stop."""

from __future__ import annotations

import html

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from account_manager.parser import active_clients, stop_flags, stop_tracking
from core.mock_message import MockMessage
from core.metrics import format_uptime, get_metric_count, tracking_uptime_seconds
from core import tracking_store
from database.database import User, get_channels_counts, get_keywords_count
from handlers.user.menu_helpers import edit_or_answer
from keyboards.admin.keyboards import admin_tracking_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User | None) -> str:
    if not user or user.language == "unset":
        return "ru"
    return user.language


def _user_label(user_id: int) -> str:
    user = User.get_or_none(User.user_id == user_id)
    if not user:
        return str(user_id)
    parts = [str(user_id)]
    if user.username:
        parts.append(f"@{user.username}")
    elif user.first_name:
        parts.append(user.first_name)
    return " ".join(parts)


async def _build_tracking_text(lang: str) -> str:
    active_ids = sorted(await tracking_store.list_active())
    matches = await get_metric_count("matches")
    floods = await get_metric_count("floodwaits")

    if not active_ids:
        return t(
            "admin_tracking_empty",
            lang=lang,
            matches=matches,
            floods=floods,
        )

    lines: list[str] = []
    for uid in active_ids:
        kw = get_keywords_count(uid)
        enabled, total = get_channels_counts(uid)
        local = "▶" if str(uid) in stop_flags else "○"
        client_ok = "online" if str(uid) in active_clients else "—"
        uptime = format_uptime(tracking_uptime_seconds(uid))
        label = html.escape(_user_label(uid))
        lines.append(
            t(
                "admin_tracking_row",
                lang=lang,
                user=label,
                keywords=kw,
                channels_enabled=enabled,
                channels_total=total,
                local=local,
                client=client_ok,
                uptime=uptime,
            )
        )

    return t(
        "admin_tracking_message",
        lang=lang,
        count=len(active_ids),
        matches=matches,
        floods=floods,
        rows="\n\n".join(lines),
    )


async def show_admin_tracking(callback: CallbackQuery) -> None:
    user = User.get_or_none(User.user_id == callback.from_user.id)
    lang = _lang(user)
    active_ids = sorted(await tracking_store.list_active())
    text = await _build_tracking_text(lang)
    await edit_or_answer(
        callback,
        text,
        reply_markup=admin_tracking_keyboard(lang=lang, user_ids=active_ids),
    )


@router.callback_query(F.data.in_({"menu:admin:tracking", "back:admin_tracking"}))
async def handle_admin_tracking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_admin_tracking(callback)


@router.callback_query(F.data == "menu:admin:tracking:refresh")
async def handle_admin_tracking_refresh(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get_or_none(User.user_id == callback.from_user.id)
    lang = _lang(user)
    await callback.answer(t("admin_tracking_refreshed", lang=lang))
    await show_admin_tracking(callback)


@router.callback_query(F.data.startswith("menu:admin:tracking:stop:"))
async def handle_admin_force_stop(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    admin = User.get_or_none(User.user_id == callback.from_user.id)
    lang = _lang(admin)
    try:
        target_id = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        await callback.answer(t("admin_tracking_stop_invalid", lang=lang), show_alert=True)
        return

    logger.info(
        "admin_force_stop_tracking",
        admin_id=callback.from_user.id,
        target_id=target_id,
    )
    mock = MockMessage(user_id=target_id)
    try:
        await stop_tracking(user_id=target_id, message=mock)
        await callback.answer(
            t("admin_tracking_stopped", lang=lang, user_id=target_id),
            show_alert=True,
        )
    except Exception as e:
        logger.exception("admin_force_stop_error", error=e, target_id=target_id)
        await callback.answer(
            t("admin_tracking_stop_error", lang=lang, error=str(e)[:80]),
            show_alert=True,
        )
    await show_admin_tracking(callback)
