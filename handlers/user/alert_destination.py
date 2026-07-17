"""Настройка куда слать алерты: личка / группа / топик."""

from __future__ import annotations

import html

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.alert_bind_token import BIND_TOKEN_TTL_SECONDS, consume_bind_token, issue_bind_token, resolve_bind_token
from core.alert_delivery import deliver_alert
from database.database import (
    User,
    clear_user_alert_group_bind,
    find_alert_group_owner,
    get_user_alert_destination,
    set_user_alert_group_bind,
    set_user_alert_to_dm,
    set_user_alert_to_group,
)
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import alert_destination_bind_keyboard, alert_destination_keyboard
from locales.locales import t
from system.dispatcher import bot

router = Router(name=__name__)
group_router = Router(name=f"{__name__}_group")
logger = structlog.get_logger(__name__)

_ADMIN_STATUSES = frozenset({"administrator", "creator", "owner"})


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _format_group_status(lang: str, dest: dict) -> str:
    if not dest.get("alert_chat_id"):
        return t("alert_destination_group_unbound", lang=lang)
    chat_id = dest["alert_chat_id"]
    thread = dest.get("alert_thread_id")
    if thread is not None:
        return t(
            "alert_destination_group_bound_topic",
            lang=lang,
            chat_id=chat_id,
            thread_id=thread,
        )
    return t("alert_destination_group_bound", lang=lang, chat_id=chat_id)


def _destination_text(lang: str, user_id: int) -> str:
    dest = get_user_alert_destination(user_id)
    dm = t("alert_destination_on", lang=lang) if dest["alert_to_dm"] else t("alert_destination_off", lang=lang)
    group = (
        t("alert_destination_on", lang=lang) if dest["alert_to_group"] else t("alert_destination_off", lang=lang)
    )
    return t(
        "alert_destination_message",
        lang=lang,
        dm_status=dm,
        group_status=group,
        group_info=_format_group_status(lang, dest),
    )


def _bind_instructions_text(lang: str, token: str) -> str:
    ttl_min = max(1, BIND_TOKEN_TTL_SECONDS // 60)
    return t(
        "alert_destination_bind_instructions",
        lang=lang,
        token=token,
        command=f"/bind_alerts {token}",
        ttl_min=ttl_min,
    )


def _parse_bind_token_from_message(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split()
    if not parts:
        return None
    cmd = parts[0].split("@", 1)[0].lower()
    if cmd != "/bind_alerts":
        return None
    if len(parts) < 2:
        return None
    return parts[1].strip()


async def _is_group_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=int(chat_id), user_id=int(user_id))
        status = getattr(member, "status", None)
        if hasattr(status, "value"):
            status = status.value
        return str(status).lower() in _ADMIN_STATUSES
    except Exception as e:
        logger.warning("alert_bind_admin_check_failed", chat_id=chat_id, user_id=user_id, error=str(e))
        return False


async def show_alert_destination(event, user_id: int | None = None) -> None:
    uid = user_id or event.from_user.id
    user = User.get(User.user_id == uid)
    lang = _lang(user)
    dest = get_user_alert_destination(uid)
    await edit_or_answer(
        event,
        _destination_text(lang, uid),
        reply_markup=alert_destination_keyboard(
            lang=lang,
            alert_to_dm=dest["alert_to_dm"],
            alert_to_group=dest["alert_to_group"],
            group_bound=bool(dest.get("alert_chat_id")),
        ),
    )


async def _apply_group_bind(user_id: int, chat_id: int, thread_id: int | None, *, lang: str) -> str:
    set_user_alert_group_bind(user_id, chat_id=chat_id, thread_id=thread_id)
    await deliver_alert(
        user_id,
        text=t("alert_destination_test_message", lang=lang),
        notify_group_failure=True,
    )
    return _format_group_status(lang, get_user_alert_destination(user_id))


async def _complete_group_bind(
    user_id: int,
    chat_id: int,
    thread_id: int | None,
    *,
    lang: str,
    token: str,
    reply_message: Message,
) -> bool:
    owner = find_alert_group_owner(chat_id, thread_id)
    if owner is not None and int(owner) != int(user_id):
        await reply_message.answer(t("alert_destination_bind_chat_taken", lang=lang), parse_mode="HTML")
        return False

    if not await _is_group_admin(chat_id, user_id):
        await reply_message.answer(t("alert_destination_bind_not_admin", lang=lang), parse_mode="HTML")
        return False

    if not await consume_bind_token(token, user_id):
        await reply_message.answer(t("alert_destination_bind_bad_token", lang=lang), parse_mode="HTML")
        return False

    status = await _apply_group_bind(user_id, chat_id, thread_id, lang=lang)
    await reply_message.answer(
        t("alert_destination_bind_success_short", lang=lang, group_info=html.escape(status)),
        parse_mode="HTML",
    )
    return True


@router.callback_query(F.data.in_({"menu:alert_destination", "back:alert_destination"}))
async def handle_alert_destination_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_alert_destination(callback)


@router.callback_query(F.data == "menu:alert_destination:toggle_dm")
async def handle_toggle_dm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    dest = get_user_alert_destination(callback.from_user.id)
    new_val = not dest["alert_to_dm"]
    if not new_val and not dest["alert_to_group"]:
        await callback.answer(t("alert_destination_need_one_channel", lang=lang), show_alert=True)
        return
    set_user_alert_to_dm(callback.from_user.id, new_val)
    await callback.answer()
    await show_alert_destination(callback)


@router.callback_query(F.data == "menu:alert_destination:toggle_group")
async def handle_toggle_group(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    dest = get_user_alert_destination(callback.from_user.id)
    new_val = not dest["alert_to_group"]
    if not new_val and not dest["alert_to_dm"]:
        await callback.answer(t("alert_destination_need_one_channel", lang=lang), show_alert=True)
        return
    set_user_alert_to_group(callback.from_user.id, new_val)
    await callback.answer()
    await show_alert_destination(callback)


@router.callback_query(F.data == "menu:alert_destination:unbind")
async def handle_unbind(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    clear_user_alert_group_bind(callback.from_user.id)
    await callback.answer(t("alert_destination_unbound", lang=lang))
    await show_alert_destination(callback)


@router.callback_query(F.data == "menu:alert_destination:bind")
async def handle_bind_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    token = await issue_bind_token(callback.from_user.id)
    await edit_or_answer(
        callback,
        _bind_instructions_text(lang, token),
        reply_markup=alert_destination_bind_keyboard(lang=lang),
    )


@router.callback_query(F.data == "menu:alert_destination:bind_ready")
async def handle_bind_ready(callback: CallbackQuery, state: FSMContext):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    token = await issue_bind_token(callback.from_user.id)
    await callback.answer()
    await edit_or_answer(
        callback,
        _bind_instructions_text(lang, token),
        reply_markup=alert_destination_bind_keyboard(lang=lang),
    )


@group_router.message(Command("bind_alerts"))
async def handle_bind_alerts_command(message: Message, state: FSMContext):
    await state.clear()
    if message.chat.type not in ("group", "supergroup"):
        return

    user = User.get_or_none(User.user_id == message.from_user.id)
    if not user:
        return

    lang = _lang(user)
    token = _parse_bind_token_from_message(message.text)
    thread_id = message.message_thread_id if getattr(message, "is_topic_message", False) else None

    if not token:
        await message.answer(t("alert_destination_bind_token_required", lang=lang), parse_mode="HTML")
        return

    owner_id = await resolve_bind_token(token)
    if owner_id is None or int(owner_id) != int(message.from_user.id):
        await message.answer(t("alert_destination_bind_bad_token", lang=lang), parse_mode="HTML")
        return

    await _complete_group_bind(
        message.from_user.id,
        message.chat.id,
        thread_id,
        lang=lang,
        token=token,
        reply_message=message,
    )
