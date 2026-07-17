"""Helpers for Inline menu navigation."""

from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from account_manager.parser import is_tracking_marked
from core.config import ADMIN_USER_IDS
from database.database import (
    User,
    get_active_account,
    get_channels_counts,
    get_keywords_count,
    get_session_count,
)
from keyboards.user.keyboards import get_lang_keyboard, resolve_main_keyboard
from locales.locales import t


def get_user_lang(user_id: int) -> str:
    try:
        user = User.get(User.user_id == user_id)
        return user.language if user.language != "unset" else "ru"
    except Exception:
        return "ru"


def _account_label(user_id: int, lang: str) -> str:
    account = get_active_account(user_id)
    if not account:
        return t("account_not_connected", lang=lang)
    phone = (account.get("phone_number") or "").strip()
    return phone or t("account_connected_unknown", lang=lang)


def is_parsing_ready(user_id: int) -> bool:
    """Аккаунт + ключи + хотя бы один включённый канал."""
    if get_session_count(user_id=user_id) <= 0:
        return False
    if get_keywords_count(user_id=user_id) <= 0:
        return False
    enabled, _ = get_channels_counts(user_id)
    return enabled > 0


def format_readiness_gaps(user_id: int, lang: str) -> str:
    """Текст, чего не хватает для запуска."""
    lines: list[str] = []
    if get_session_count(user_id=user_id) <= 0:
        lines.append(t("ready_gap_account", lang=lang))
    if get_keywords_count(user_id=user_id) <= 0:
        lines.append(t("ready_gap_keywords", lang=lang))
    enabled, total = get_channels_counts(user_id)
    if enabled <= 0:
        if total <= 0:
            lines.append(t("ready_gap_channels_none", lang=lang))
        else:
            lines.append(t("ready_gap_channels_disabled", lang=lang))
    return "\n".join(f"• {line}" for line in lines)


def get_wizard_step(user_id: int) -> str:
    """Текущий шаг онбординга: account | keywords | channels | ready."""
    if get_session_count(user_id=user_id) <= 0:
        return "account"
    if get_keywords_count(user_id=user_id) <= 0:
        return "keywords"
    enabled, _ = get_channels_counts(user_id)
    if enabled <= 0:
        return "channels"
    return "ready"


def next_step_hint(user_id: int, lang: str, *, tracking_active: bool = False) -> str:
    """Одна конкретная подсказка «что сделать сейчас»."""
    step = get_wizard_step(user_id)
    if step == "ready":
        if tracking_active:
            return t("next_step_tracking_on", lang=lang)
        return t("next_step_ready_start", lang=lang)
    return t(f"next_step_{step}", lang=lang)


async def get_parsing_snapshot(user_id: int) -> dict:
    """Counts + readiness flags for main status / cabinet checklist."""
    accounts_count = get_session_count(user_id=user_id)
    keywords_count = get_keywords_count(user_id=user_id)
    channels_enabled, channels_total = get_channels_counts(user_id)
    tracking_active = await is_tracking_marked(user_id)
    ready = accounts_count > 0 and keywords_count > 0 and channels_enabled > 0
    return {
        "accounts_count": accounts_count,
        "keywords_count": keywords_count,
        "channels_count": channels_total,
        "channels_enabled": channels_enabled,
        "channels_total": channels_total,
        "tracking_active": tracking_active,
        "has_account": accounts_count > 0,
        "has_keywords": keywords_count > 0,
        "has_channels": channels_enabled > 0,
        "ready": ready,
        "account_label": _account_label(user_id, get_user_lang(user_id)),
        "wizard_step": get_wizard_step(user_id),
    }


def _check_mark(ok: bool) -> str:
    return "✅" if ok else "☐"


async def generate_welcome_message(user_language: str, user_tg_id: int) -> str:
    snap = await get_parsing_snapshot(user_tg_id)
    tracking_status = (
        t("tracking_status_running", lang=user_language)
        if snap["tracking_active"]
        else t("tracking_status_stopped", lang=user_language)
    )
    howto_block = ""
    if not snap["ready"]:
        howto_block = t("howto_3_steps_short", lang=user_language) + "\n\n"
    return t(
        "welcome_message_template",
        lang=user_language,
        tracking_status=tracking_status,
        account_label=snap["account_label"],
        keywords_count=snap["keywords_count"],
        channels_enabled=snap["channels_enabled"],
        channels_total=snap["channels_total"],
        howto_block=howto_block,
        next_hint=next_step_hint(
            user_tg_id,
            user_language,
            tracking_active=snap["tracking_active"],
        ),
    )


async def generate_cabinet_message(user_language: str, user_tg_id: int) -> str:
    from database.database import get_user_match_mode

    snap = await get_parsing_snapshot(user_tg_id)
    mode = get_user_match_mode(user_tg_id)
    return t(
        "cabinet_message_template",
        lang=user_language,
        check_account=_check_mark(snap["has_account"]),
        check_keywords=_check_mark(snap["has_keywords"]),
        check_channels=_check_mark(snap["has_channels"]),
        account_label=snap["account_label"],
        keywords_count=snap["keywords_count"],
        channels_enabled=snap["channels_enabled"],
        channels_total=snap["channels_total"],
        match_mode=t(f"match_mode_{mode}_name", lang=user_language),
        hint=next_step_hint(
            user_tg_id,
            user_language,
            tracking_active=snap["tracking_active"],
        ),
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


async def remove_reply_keyboard(message: Message) -> None:
    """Снимает старую Reply-клавиатуру (если была) и сразу удаляет служебное сообщение."""
    try:
        stub = await message.answer(".", reply_markup=ReplyKeyboardRemove())
        try:
            await stub.delete()
        except Exception:
            pass
    except Exception:
        pass


async def get_main_reply_markup(user_id: int, lang: str, is_admin: bool):
    snap = await get_parsing_snapshot(user_id)
    return resolve_main_keyboard(
        lang,
        tracking_active=snap["tracking_active"],
        ready=snap["ready"],
        is_admin=is_admin,
    )


async def show_main_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Show status + main Inline keyboard. Works for Message and CallbackQuery."""
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
    text = await generate_welcome_message(user.language, user_id)
    await edit_or_answer(event, text, reply_markup=markup, parse_mode="HTML")


async def generate_wizard_message(lang: str, user_id: int) -> str:
    snap = await get_parsing_snapshot(user_id)
    step = get_wizard_step(user_id)
    return t(
        "wizard_message_template",
        lang=lang,
        check_account=_check_mark(snap["has_account"]),
        check_keywords=_check_mark(snap["has_keywords"]),
        check_channels=_check_mark(snap["has_channels"]),
        account_label=snap["account_label"],
        keywords_count=snap["keywords_count"],
        channels_enabled=snap["channels_enabled"],
        channels_total=snap["channels_total"],
        step_hint=t(f"wizard_hint_{step}", lang=lang),
    )


async def show_wizard(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Мастер первого запуска: аккаунт → ключи → каналы → старт."""
    if state is not None:
        await state.clear()

    from keyboards.user.keyboards import wizard_keyboard

    user_id = event.from_user.id
    lang = get_user_lang(user_id)
    step = get_wizard_step(user_id)
    text = await generate_wizard_message(lang, user_id)
    await edit_or_answer(event, text, reply_markup=wizard_keyboard(lang=lang, step=step))


async def show_main_or_wizard(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Новым / неготовым — wizard, остальным — главный статус."""
    user_id = event.from_user.id
    if not is_parsing_ready(user_id):
        await show_wizard(event, state)
    else:
        await show_main_menu(event, state)


async def show_cabinet(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    """Экран «Мой парсинг»: чеклист готовности + быстрые переходы."""
    if state is not None:
        await state.clear()

    from keyboards.user.keyboards import cabinet_keyboard

    user_id = event.from_user.id
    lang = get_user_lang(user_id)
    text = await generate_cabinet_message(lang, user_id)
    await edit_or_answer(event, text, reply_markup=cabinet_keyboard(lang=lang, ready=is_parsing_ready(user_id)))
