"""Команды /leads в привязанной группе (только владелец)."""

from __future__ import annotations

from datetime import date

import structlog
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from core.leads_export import build_leads_xlsx_path, remove_export_file
from database.database import User, get_user_alert_destination
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _parse_leads_args(text: str | None) -> tuple[date | None, date | None]:
    if not text:
        return None, None
    parts = text.strip().split()
    if not parts:
        return None, None
    cmd = parts[0].split("@", 1)[0].lower()
    if cmd != "/leads":
        return None, None
    args = parts[1:]
    if not args:
        return None, None
    if len(args) == 1:
        return date.fromisoformat(args[0]), date.fromisoformat(args[0])
    if len(args) >= 2:
        return date.fromisoformat(args[0]), date.fromisoformat(args[1])
    return None, None


def _is_bound_group_message(message: Message, dest: dict) -> bool:
    if message.chat.type not in ("group", "supergroup"):
        return False
    if not dest.get("alert_chat_id") or int(message.chat.id) != int(dest["alert_chat_id"]):
        return False
    bound_thread = dest.get("alert_thread_id")
    if bound_thread is None:
        return True
    msg_thread = message.message_thread_id if getattr(message, "is_topic_message", False) else None
    return msg_thread is not None and int(msg_thread) == int(bound_thread)


async def _reply_access_error(message: Message, user: User, dest: dict) -> bool:
    """
    Проверяет доступ к /leads в группе.
    Returns True если можно продолжать, False если отправлено сообщение об ошибке.
    """
    lang = _lang(user)

    if not dest.get("alert_to_group"):
        await message.answer(t("leads_group_disabled", lang=lang), parse_mode="HTML")
        return False

    if not dest.get("alert_chat_id"):
        await message.answer(t("leads_group_not_bound", lang=lang), parse_mode="HTML")
        return False

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(t("leads_group_not_bound", lang=lang), parse_mode="HTML")
        return False

    if int(message.chat.id) != int(dest["alert_chat_id"]):
        await message.answer(
            t(
                "leads_group_wrong_chat",
                lang=lang,
                chat_id=dest["alert_chat_id"],
            ),
            parse_mode="HTML",
        )
        return False

    bound_thread = dest.get("alert_thread_id")
    if bound_thread is not None:
        msg_thread = message.message_thread_id if getattr(message, "is_topic_message", False) else None
        if msg_thread is None or int(msg_thread) != int(bound_thread):
            await message.answer(
                t("leads_group_wrong_topic", lang=lang, thread_id=bound_thread),
                parse_mode="HTML",
            )
            return False

    return True


@router.message(Command("leads_help"))
async def handle_leads_help(message: Message):
    user = User.get_or_none(User.user_id == message.from_user.id)
    if not user:
        return

    dest = get_user_alert_destination(message.from_user.id)
    if not await _reply_access_error(message, user, dest):
        return

    lang = _lang(user)
    await message.answer(t("leads_group_help", lang=lang), parse_mode="HTML")


@router.message(Command("leads"))
async def handle_leads_command(message: Message):
    user = User.get_or_none(User.user_id == message.from_user.id)
    if not user:
        return

    dest = get_user_alert_destination(message.from_user.id)
    if not await _reply_access_error(message, user, dest):
        return

    lang = _lang(user)

    try:
        date_from, date_to = _parse_leads_args(message.text)
    except ValueError:
        await message.answer(t("leads_group_bad_dates", lang=lang), parse_mode="HTML")
        return

    try:
        result = build_leads_xlsx_path(
            message.from_user.id,
            lang,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as e:
        logger.exception("leads_group_export_error", error=e)
        await message.answer(t("export_error", lang=lang), parse_mode="HTML")
        return

    if not result:
        await message.answer(t("leads_empty", lang=lang), parse_mode="HTML")
        return

    filepath, count = result
    try:
        if date_from and date_to and date_from != date_to:
            caption = t(
                "leads_group_export_range_caption",
                lang=lang,
                count=count,
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
            )
        elif date_from:
            caption = t("leads_group_export_day_caption", lang=lang, count=count, date=date_from.isoformat())
        else:
            caption = t("leads_export_caption", lang=lang, count=count)

        await message.answer_document(
            document=FSInputFile(filepath),
            caption=caption,
            parse_mode="HTML",
        )
    finally:
        remove_export_file(filepath)
