"""Просмотр и выгрузка сохранённых совпадений (leads)."""

from __future__ import annotations

import html

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from core.leads_export import build_leads_xlsx_path, remove_export_file
from database.database import User, get_leads_count, list_leads
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import (
    back_keyboard,
    leads_list_keyboard,
    leads_menu_keyboard,
)
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)

LEADS_PAGE_SIZE = 5


def _user_lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _lead_preview(lead) -> str:
    author = lead.author_name or (f"@{lead.author_username}" if lead.author_username else "—")
    text = (lead.message_text or "").replace("\n", " ")
    if len(text) > 80:
        text = text[:77] + "…"
    when = lead.matched_at.strftime("%d.%m %H:%M") if lead.matched_at else "—"
    return f"<b>{html.escape(str(lead.matched_keyword))}</b> · {html.escape(str(author))}\n{when} · {html.escape(text)}"


async def show_leads_menu(event, state: FSMContext | None = None) -> None:
    if state is not None:
        await state.clear()
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    count = get_leads_count(event.from_user.id)
    await edit_or_answer(
        event,
        t("leads_menu_message", lang=lang, count=count),
        reply_markup=leads_menu_keyboard(lang=lang),
    )


async def show_leads_list(event, page: int = 0) -> None:
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    rows, total, page = list_leads(event.from_user.id, page=page, page_size=LEADS_PAGE_SIZE)

    if total == 0:
        await edit_or_answer(
            event,
            t("leads_empty", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:leads"),
        )
        return

    lines = [t("leads_list_title", lang=lang, count=total, page=page + 1), ""]
    for lead in rows:
        lines.append(_lead_preview(lead))
        lines.append("")

    await edit_or_answer(
        event,
        "\n".join(lines).strip(),
        reply_markup=leads_list_keyboard(
            lang=lang,
            items=[(lead.id, lead.matched_keyword) for lead in rows],
            page=page,
            total=total,
            page_size=LEADS_PAGE_SIZE,
        ),
    )


@router.callback_query(F.data.in_({"menu:leads", "back:leads"}))
async def handle_leads_menu(callback: CallbackQuery, state: FSMContext):
    await show_leads_menu(callback, state)


@router.callback_query(F.data == "menu:leads:list")
async def handle_leads_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_leads_list(callback, page=0)


@router.callback_query(F.data.startswith("menu:leads:page:"))
async def handle_leads_page(callback: CallbackQuery):
    try:
        page = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        page = 0
    await show_leads_list(callback, page=page)


@router.callback_query(F.data.startswith("menu:leads:view:"))
async def handle_leads_view(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    parts = callback.data.split(":")
    try:
        lead_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
    except (IndexError, ValueError):
        await callback.answer("Error", show_alert=True)
        return

    from database.database import Lead

    lead = Lead.get_or_none(Lead.id == lead_id, Lead.owner_user_id == callback.from_user.id)
    if not lead:
        await callback.answer(t("leads_missing", lang=lang), show_alert=True)
        await show_leads_list(callback, page=page)
        return

    author_bits = []
    if lead.author_name:
        author_bits.append(html.escape(lead.author_name))
    if lead.author_username:
        author_bits.append(f"(@{html.escape(lead.author_username)})")
    if lead.author_tg_id:
        author_bits.append(f"id {lead.author_tg_id}")
    author = " ".join(author_bits) if author_bits else "—"

    chat = lead.chat_title or "—"
    if lead.chat_username:
        chat = f"{html.escape(chat)} (@{html.escape(lead.chat_username)})"
    else:
        chat = html.escape(str(chat))

    when = lead.matched_at.strftime("%d.%m.%Y %H:%M") if lead.matched_at else "—"
    link = lead.message_link or "—"

    text = t(
        "leads_card",
        lang=lang,
        keyword=html.escape(lead.matched_keyword),
        author=author,
        chat=chat,
        when=when,
        link=link,
        message_text=html.escape((lead.message_text or "")[:3500]),
    )
    await edit_or_answer(
        callback,
        text,
        reply_markup=back_keyboard(lang=lang, callback_data=f"menu:leads:page:{page}"),
    )


@router.callback_query(F.data == "menu:leads:export:xlsx")
async def handle_leads_export(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)

    try:
        result = build_leads_xlsx_path(callback.from_user.id, lang)
    except Exception as e:
        logger.exception("leads_export_error", error=e)
        await callback.message.answer(t("export_error", lang=lang))
        return

    if not result:
        await callback.message.answer(
            t("leads_empty", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:leads"),
        )
        return

    filepath, count = result
    try:
        await callback.message.answer_document(
            document=FSInputFile(filepath),
            caption=t("leads_export_caption", lang=lang, count=count),
            reply_markup=back_keyboard(lang=lang, callback_data="back:leads"),
        )
    except Exception as e:
        logger.exception("leads_export_error", error=e)
        await callback.message.answer(t("export_error", lang=lang))
    finally:
        remove_export_file(filepath)
