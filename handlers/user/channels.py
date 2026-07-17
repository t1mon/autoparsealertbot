"""Каналы/группы для парсинга: подменю, add text/.txt, список, toggle, экспорт."""

from __future__ import annotations

import asyncio
import html as html_mod
import os
from datetime import datetime

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, Message

from core.membership_status import (
    MEMBERSHIP_OK,
    membership_badge,
    membership_reason_label,
    membership_status_label,
)
from core.telegram_utils import chat_ref_label, normalize_telegram_chat_ref
from database.database import (
    Groups,
    User,
    apply_membership_report,
    delete_group_by_id,
    get_channels_counts,
    get_user_channel_usernames,
    list_user_channels,
    set_group_parse_enabled,
)
from handlers.user.get_dada import create_excel_file
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import (
    after_setup_keyboard,
    back_keyboard,
    channels_check_subs_keyboard,
    channels_join_cancel_confirm_keyboard,
    channels_join_progress_keyboard,
    channels_list_keyboard,
    channels_menu_keyboard,
    clear_all_channels_confirm_keyboard,
)
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)

CHANNELS_PAGE_SIZE = 8


def _user_lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


async def show_channels_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    if state is not None:
        await state.clear()
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    enabled, total = get_channels_counts(event.from_user.id)
    await edit_or_answer(
        event,
        t("channels_menu_message", lang=lang, enabled=enabled, total=total),
        reply_markup=channels_menu_keyboard(lang=lang),
    )


async def show_channels_list(event: Message | CallbackQuery, page: int = 0) -> None:
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    items, total, page = list_user_channels(
        event.from_user.id, page=page, page_size=CHANNELS_PAGE_SIZE
    )

    if total == 0:
        await edit_or_answer(
            event,
            t("no_tracking_links_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
        return

    enabled_total, _ = get_channels_counts(event.from_user.id)
    lines = [
        t(
            "channels_list_title",
            lang=lang,
            enabled=enabled_total,
            total=total,
            page=page + 1,
        )
    ]
    for item in items:
        lines.append(_channel_list_line(item, lang))

    await edit_or_answer(
        event,
        "\n".join(lines),
        reply_markup=channels_list_keyboard(
            lang=lang,
            items=items,
            page=page,
            total=total,
            page_size=CHANNELS_PAGE_SIZE,
        ),
    )


async def _save_tracking_usernames(message: Message, raw_values: list[str], user: User) -> None:
    added_count = 0
    skipped_count = 0
    errors_count = 0

    for raw_username in raw_values:
        username = normalize_telegram_chat_ref(raw_username)
        if not username:
            errors_count += 1
            logger.warning("invalid_channel_skipped", raw=raw_username)
            continue

        try:
            Groups.create(
                user_id=message.from_user.id,
                username=username,
                parse_enabled=True,
            )
            added_count += 1
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                skipped_count += 1
            else:
                errors_count += 1
                logger.error("channel_add_error", username=username, error=e)

    lang = _user_lang(user)
    await message.answer(
        t(
            "groups_upload_summary",
            lang=lang,
            added=added_count,
            skipped=skipped_count,
            errors=errors_count,
        ),
        reply_markup=after_setup_keyboard(
            lang, message.from_user.id, channels_menu_keyboard(lang=lang)
        ),
    )


@router.callback_query(F.data.in_({"menu:channels", "back:channels"}))
async def handle_channels_menu(callback: CallbackQuery, state: FSMContext):
    from account_manager.join_tasks import detach_join_ui, is_join_running

    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    if is_join_running(callback.from_user.id):
        detach_join_ui(callback.from_user.id)
        await callback.answer(t("channels_join_background_hint", lang=lang))
    await show_channels_menu(callback, state)


def _format_channel_lines(refs: list[str], *, limit: int = 25) -> str:
    from core.telegram_utils import chat_ref_label

    shown = refs[:limit]
    lines = [f"• <code>{html_mod.escape(chat_ref_label(r))}</code>" for r in shown]
    if len(refs) > limit:
        lines.append(f"… +{len(refs) - limit}")
    return "\n".join(lines) if lines else "—"


def _format_channels_with_reasons(
    refs: list[str],
    reasons: dict[str, str],
    lang: str,
    *,
    limit: int = 25,
) -> str:
    shown = refs[:limit]
    lines: list[str] = []
    for ref in shown:
        label = html_mod.escape(chat_ref_label(ref))
        reason = reasons.get(ref)
        if reason:
            hint = html_mod.escape(membership_reason_label(lang, reason))
            lines.append(f"• <code>{label}</code> — <i>{hint}</i>")
        else:
            lines.append(f"• <code>{label}</code>")
    if len(refs) > limit:
        lines.append(f"… +{len(refs) - limit}")
    return "\n".join(lines) if lines else "—"


def _channel_list_line(item: dict, lang: str) -> str:
    mark = "✅" if item["parse_enabled"] else "⏸"
    badge = membership_badge(item.get("membership_status"))
    username = html_mod.escape(item["username"] or "")
    line = f"{mark}"
    if badge:
        line += f" {badge}"
    line += f" <code>{username}</code>"
    status = item.get("membership_status") or ""
    if status and status != MEMBERSHIP_OK:
        hint = membership_status_label(lang, status)
        if hint:
            line += f" <i>({html_mod.escape(hint)})</i>"
    return line


@router.callback_query(F.data == "menu:channels:check_subs")
async def handle_channels_check_subs(callback: CallbackQuery, state: FSMContext):
    """Проверка: активный аккаунт подписан на включённые каналы?"""
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    user_id = callback.from_user.id

    from account_manager.auth import CheckingAccountsValidity
    from account_manager.chat_targets import check_channels_membership
    from database.database import get_active_account

    account = get_active_account(user_id)
    if not account:
        await callback.answer(t("channels_check_no_account", lang=lang), show_alert=True)
        return

    channels, _ = get_user_channel_usernames(user_id=user_id, only_enabled=True)
    if not channels:
        await callback.answer(t("channels_check_no_enabled", lang=lang), show_alert=True)
        return

    await callback.answer(t("channels_check_progress", lang=lang))
    await edit_or_answer(
        callback,
        t("channels_check_progress_msg", lang=lang, count=len(channels)),
        reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
    )

    client = None
    try:
        checker = CheckingAccountsValidity(message=callback.message, user_id=user_id)
        client = await checker.client_connect_string_session(account["session_string"])
        if not client:
            await edit_or_answer(
                callback,
                t("channels_check_connect_fail", lang=lang),
                reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
            )
            return

        report = await check_channels_membership(client, channels)
        ok = report["ok"]
        missing = report["missing"]
        errors = report["errors"]
        reasons = report.get("reasons") or {}
        phone = (account.get("phone_number") or "?").strip() or "?"

        apply_membership_report(
            user_id,
            ok=ok,
            missing=missing,
            errors=errors,
            reasons=reasons,
        )

        error_reasons = {ref: reasons.get(ref, "check_failed") for ref in errors}
        text = t(
            "channels_check_report",
            lang=lang,
            phone=phone,
            ok_count=len(ok),
            missing_count=len(missing),
            error_count=len(errors),
            missing_list=_format_channels_with_reasons(missing, reasons, lang),
            error_list=_format_channels_with_reasons(errors, error_reasons, lang),
        )
        await edit_or_answer(
            callback,
            text,
            reply_markup=channels_check_subs_keyboard(
                lang=lang,
                can_join=bool(missing),
            ),
        )
        # stash missing in FSM for join action
        if missing:
            await state.update_data(channels_missing=missing)
    except Exception as e:
        logger.exception("channels_check_subs_error", error=e)
        await edit_or_answer(
            callback,
            t("channels_check_error", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


def _join_progress_text(
    lang: str,
    *,
    done: int,
    total: int,
    channel: str,
    joined: int,
    already: int,
    errors: int,
    delay: int = 0,
) -> str:
    if delay > 0:
        status = t("channels_join_status_pause", lang=lang, delay=delay)
    else:
        status = t("channels_join_status_working", lang=lang)
    return t(
        "channels_join_progress_live",
        lang=lang,
        done=done,
        total=total,
        channel=html_mod.escape(chat_ref_label(channel)),
        joined=joined,
        already=already,
        errors=errors,
        status=status,
    )


async def _finish_join_ui(
    *,
    bot,
    entry,
    lang: str,
    text: str,
    reply_markup,
) -> None:
    from account_manager.join_tasks import safe_edit_join_message

    if entry.ui_attached:
        edited = await safe_edit_join_message(entry, bot, text, reply_markup)
        if not edited:
            await bot.send_message(entry.chat_id, text, reply_markup=reply_markup, parse_mode="HTML")
    elif entry.chat_id is not None:
        await bot.send_message(entry.chat_id, text, reply_markup=reply_markup, parse_mode="HTML")


async def _channels_join_worker(
    *,
    bot,
    user_id: int,
    lang: str,
    work: list[str],
    original_len: int,
    session_string: str,
    stop_event: asyncio.Event,
    entry,
    state: FSMContext,
    task: asyncio.Task,
) -> None:
    from account_manager.auth import CheckingAccountsValidity
    from account_manager.join_tasks import clear_join_task, safe_edit_join_message
    from account_manager.join_throttle import join_channels_safely
    from core.config import JOIN_BATCH_LIMIT

    total = entry.total
    client = None
    batch = None
    progress_kb = channels_join_progress_keyboard(lang=lang)
    menu_kb = channels_menu_keyboard(lang=lang)

    async def on_progress(stats, channel, result, delay):
        text = _join_progress_text(
            lang,
            done=stats.attempted,
            total=total,
            channel=channel,
            joined=stats.joined,
            already=stats.already,
            errors=stats.error,
            delay=delay,
        )
        await safe_edit_join_message(entry, bot, text, progress_kb)

    try:
        checker = CheckingAccountsValidity(message=None, user_id=user_id)
        client = await checker.client_connect_string_session(session_string)
        if not client:
            await _finish_join_ui(
                bot=bot,
                entry=entry,
                lang=lang,
                text=t("channels_check_connect_fail", lang=lang),
                reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
            )
            return

        if work:
            await safe_edit_join_message(
                entry,
                bot,
                _join_progress_text(
                    lang,
                    done=0,
                    total=total,
                    channel=work[0],
                    joined=0,
                    already=0,
                    errors=0,
                ),
                progress_kb,
            )

        batch = await join_channels_safely(
            client=client,
            channels=work,
            user_id=user_id,
            stop_event=stop_event,
            on_progress=on_progress,
        )

        note = ""
        if original_len > len(work):
            note = t(
                "too_many_channels",
                lang=lang,
                total=original_len,
                limit=JOIN_BATCH_LIMIT,
            )

        if batch.stopped:
            remaining = work[batch.attempted:]
            await state.update_data(channels_missing=remaining)
            body = t(
                "channels_join_stopped",
                lang=lang,
                joined=batch.joined,
                already=batch.already,
                errors=batch.error,
                remaining=len(remaining),
            )
        else:
            await state.update_data(channels_missing=[])
            body = t(
                "channels_join_done",
                lang=lang,
                joined=batch.joined,
                already=batch.already,
                errors=batch.error,
                skipped=batch.skipped_limit,
            )

        if note:
            body = f"{body}\n\n{note}"

        await _finish_join_ui(bot=bot, entry=entry, lang=lang, text=body, reply_markup=menu_kb)
    except asyncio.CancelledError:
        logger.info("channels_join_worker_cancelled", user_id=user_id)
        raise
    except Exception as e:
        logger.exception("channels_join_missing_error", error=e)
        await _finish_join_ui(
            bot=bot,
            entry=entry,
            lang=lang,
            text=t("channels_check_error", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        clear_join_task(user_id, task)


@router.callback_query(F.data == "menu:channels:join_missing")
async def handle_channels_join_missing(callback: CallbackQuery, state: FSMContext):
    """Подписать активный аккаунт на каналы из последней проверки."""
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    user_id = callback.from_user.id
    data = await state.get_data()
    missing = data.get("channels_missing") or []
    if not missing:
        await callback.answer(t("channels_join_nothing", lang=lang), show_alert=True)
        return

    from account_manager.join_tasks import is_join_running, register_join_task
    from account_manager.join_throttle import apply_batch_cap, remaining_daily_joins
    from core.config import JOIN_BATCH_LIMIT, JOIN_DAILY_LIMIT
    from database.database import get_active_account

    if is_join_running(user_id):
        await callback.answer(t("channels_join_already_running", lang=lang), show_alert=True)
        return

    account = get_active_account(user_id)
    if not account:
        await callback.answer(t("channels_check_no_account", lang=lang), show_alert=True)
        return

    daily_left = await remaining_daily_joins(user_id)
    if daily_left <= 0:
        await edit_or_answer(
            callback,
            t("join_daily_limit", lang=lang, limit=JOIN_DAILY_LIMIT),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
        return

    work, original_len = apply_batch_cap(list(missing))
    progress_count = min(len(work), daily_left)
    progress_kb = channels_join_progress_keyboard(lang=lang)
    progress_msg = await edit_or_answer(
        callback,
        t("channels_join_progress", lang=lang, count=progress_count),
        reply_markup=progress_kb,
    )

    stop_event = asyncio.Event()

    async def _runner():
        from account_manager.join_tasks import get_join_task

        entry = get_join_task(user_id)
        if entry is None:
            return
        await _channels_join_worker(
            bot=callback.bot,
            user_id=user_id,
            lang=lang,
            work=work,
            original_len=original_len,
            session_string=account["session_string"],
            stop_event=stop_event,
            entry=entry,
            state=state,
            task=asyncio.current_task(),
        )

    join_task = asyncio.create_task(_runner())
    register_join_task(
        user_id,
        join_task,
        chat_id=progress_msg.chat.id,
        message_id=progress_msg.message_id,
        total=progress_count,
        lang=lang,
        stop_event=stop_event,
    )


@router.callback_query(F.data == "menu:channels:join_cancel")
async def handle_channels_join_cancel_prompt(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    from account_manager.join_tasks import get_join_task

    entry = get_join_task(callback.from_user.id)
    if entry is None:
        await callback.answer(t("channels_join_nothing", lang=lang), show_alert=True)
        return

    await callback.answer()
    await edit_or_answer(
        callback,
        t("channels_join_cancel_confirm", lang=lang),
        reply_markup=channels_join_cancel_confirm_keyboard(lang=lang),
    )


@router.callback_query(F.data == "menu:channels:join_cancel:yes")
async def handle_channels_join_cancel_yes(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    from account_manager.join_tasks import get_join_task, request_join_cancel

    entry = get_join_task(callback.from_user.id)
    if entry is None:
        await callback.answer(t("channels_join_nothing", lang=lang), show_alert=True)
        return

    request_join_cancel(callback.from_user.id)
    entry.ui_attached = True
    await callback.answer()
    await edit_or_answer(
        callback,
        t("channels_join_cancelling_msg", lang=lang),
        reply_markup=channels_join_progress_keyboard(lang=lang),
    )


@router.callback_query(F.data == "menu:channels:join_cancel:no")
async def handle_channels_join_cancel_no(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    from account_manager.join_tasks import get_join_task

    entry = get_join_task(callback.from_user.id)
    if entry is None:
        await callback.answer(t("channels_join_nothing", lang=lang), show_alert=True)
        return

    entry.ui_attached = True
    await callback.answer()
    await edit_or_answer(
        callback,
        t("channels_join_progress", lang=lang, count=entry.total),
        reply_markup=channels_join_progress_keyboard(lang=lang),
    )


@router.callback_query(F.data.in_({"menu:channels:add", "menu:settings:update_list"}))
async def handle_channels_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    logger.info("channels_add_menu", user_id=callback.from_user.id)
    await edit_or_answer(
        callback,
        t("update_list", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
    )
    await state.set_state(MyStates.waiting_username_group)


@router.message(MyStates.waiting_username_group, F.document)
async def handle_channels_file(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _user_lang(user)
    document = message.document
    filename = (document.file_name or "").lower()

    if not filename.endswith(".txt"):
        await message.answer(t("only_txt_files_supported", lang=lang))
        return

    file = await message.bot.get_file(document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    try:
        content = file_bytes.read().decode("utf-8")
    except UnicodeDecodeError:
        file_bytes.seek(0)
        content = file_bytes.read().decode("utf-8", errors="ignore")

    usernames = [line.strip() for line in content.replace(",", "\n").splitlines() if line.strip()]
    if not usernames:
        await message.answer(t("empty_file_no_usernames", lang=lang))
        await state.clear()
        return

    await _save_tracking_usernames(message, usernames, user)
    await state.clear()


@router.message(MyStates.waiting_username_group, F.text)
async def handle_channels_text(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    raw_values = [
        item.strip()
        for item in (message.text or "").replace(",", "\n").splitlines()
        if item.strip()
    ]
    if not raw_values:
        await message.answer(t("empty_file_no_usernames", lang=_user_lang(user)))
        return

    await _save_tracking_usernames(message, raw_values, user)
    await state.clear()


@router.callback_query(F.data.in_({"menu:channels:list", "menu:settings:links"}))
async def handle_channels_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_channels_list(callback, page=0)


@router.callback_query(F.data.startswith("menu:channels:page:"))
async def handle_channels_page(callback: CallbackQuery):
    try:
        page = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        page = 0
    await show_channels_list(callback, page=page)


@router.callback_query(F.data.startswith("menu:channels:toggle:"))
async def handle_channels_toggle(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    parts = callback.data.split(":")
    # menu:channels:toggle:{id}:{page}
    try:
        group_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
    except (IndexError, ValueError):
        await callback.answer("Error", show_alert=True)
        return

    row = Groups.get_or_none(Groups.id == group_id, Groups.user_id == callback.from_user.id)
    if not row:
        await callback.answer(t("channel_missing", lang=lang), show_alert=True)
        await show_channels_list(callback, page=page)
        return

    new_value = not bool(row.parse_enabled)
    set_group_parse_enabled(callback.from_user.id, group_id, new_value)
    await callback.answer(
        t("channel_enabled" if new_value else "channel_disabled", lang=lang, channel=row.username),
    )
    await show_channels_list(callback, page=page)


@router.callback_query(F.data.startswith("menu:channels:del:"))
async def handle_channels_delete(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    parts = callback.data.split(":")
    try:
        group_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
    except (IndexError, ValueError):
        await callback.answer("Error", show_alert=True)
        return

    username = delete_group_by_id(callback.from_user.id, group_id)
    if not username:
        await callback.answer(t("channel_missing", lang=lang), show_alert=True)
    else:
        await callback.answer(t("channel_deleted", lang=lang, channel=username))
    await show_channels_list(callback, page=page)


@router.callback_query(F.data == "menu:channels:export:txt")
async def handle_channels_export_txt(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    usernames, total = get_user_channel_usernames(callback.from_user.id, only_enabled=False)

    if not usernames:
        await callback.message.answer(
            t("no_tracking_links_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
        return

    content = "\n".join(usernames) + "\n"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"channels_{callback.from_user.id}_{timestamp}.txt"
    await callback.message.answer_document(
        document=BufferedInputFile(content.encode("utf-8"), filename=filename),
        caption=t("tracking_links_export_caption", lang=lang, count=total),
        reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
    )


@router.callback_query(F.data == "menu:channels:export:xlsx")
async def handle_channels_export_xlsx(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)

    rows = list(
        Groups.select()
        .where(Groups.user_id == callback.from_user.id)
        .order_by(Groups.date_added.desc())
    )
    if not rows:
        await callback.message.answer(
            t("no_tracking_links_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
        return

    data = [
        (
            idx,
            row.username,
            t("channel_status_on", lang=lang) if row.parse_enabled else t("channel_status_off", lang=lang),
        )
        for idx, row in enumerate(rows, start=1)
    ]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"channels_{callback.from_user.id}_{timestamp}.xlsx"
    headers = [
        t("excel_header_number", lang=lang),
        t("excel_header_username", lang=lang),
        t("excel_header_parse_status", lang=lang),
    ]

    try:
        filepath = create_excel_file(
            data=data,
            headers=headers,
            filename=filename,
            sheet_name="Channels",
        )
        await callback.message.answer_document(
            document=FSInputFile(filepath),
            caption=t("tracking_links_export_caption", lang=lang, count=len(data)),
            reply_markup=back_keyboard(lang=lang, callback_data="back:channels"),
        )
        os.remove(filepath)
    except Exception as e:
        logger.exception("channels_export_xlsx_error", error=e)
        await callback.message.answer(t("export_error", lang=lang))


@router.callback_query(F.data == "menu:channels:clear")
async def handle_channels_clear_ask(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    enabled, total = get_channels_counts(callback.from_user.id)
    if total == 0:
        await edit_or_answer(
            callback,
            t("clear_all_channels_empty", lang=lang),
            reply_markup=channels_menu_keyboard(lang=lang),
        )
        return
    await edit_or_answer(
        callback,
        t("clear_all_channels_confirm", lang=lang, count=total),
        reply_markup=clear_all_channels_confirm_keyboard(lang=lang),
    )
