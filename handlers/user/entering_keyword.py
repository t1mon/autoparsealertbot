"""Ключевые слова: подменю, добавление (текст/.txt), список, удаление, экспорт."""

from __future__ import annotations

import html
import os
from datetime import datetime

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, Message

from core.keyword_match import MatchDetail, find_all_matching_keyword_details
from core.stopwords import find_stopword
from database.database import (
    User,
    create_keywords_model,
    get_keywords_count,
    get_user_match_mode,
    get_user_stopwords,
    set_user_match_mode,
)
from handlers.user.get_dada import create_excel_file
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import (
    after_setup_keyboard,
    back_keyboard,
    keywords_list_keyboard,
    keywords_menu_keyboard,
    match_mode_keyboard,
)
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)

KEYWORDS_PAGE_SIZE = 10


def _user_lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _ensure_keywords_model(user_id: int):
    model = create_keywords_model(user_id=user_id)
    if not model.table_exists():
        model.create_table()
    return model


def _parse_keywords_text(raw: str) -> list[str]:
    """Строки и запятые; пустые отбрасываем; порядок сохраняем, дубли в одном вводе схлопываем."""
    seen: set[str] = set()
    result: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        kw = line.strip()
        if not kw or kw in seen:
            continue
        seen.add(kw)
        result.append(kw)
    return result


def _import_keywords(user_id: int, keywords_list: list[str]) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    model = _ensure_keywords_model(user_id)
    added: list[str] = []
    skipped: list[str] = []
    errors: list[tuple[str, str]] = []

    for keyword in keywords_list:
        try:
            model.create(user_keyword=keyword)
            added.append(keyword)
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                skipped.append(keyword)
            else:
                errors.append((keyword, str(e)))
                logger.error("keyword_add_error", keyword=keyword, error=e)
    return added, skipped, errors


def _format_import_report(
    lang: str,
    added: list[str],
    skipped: list[str],
    errors: list[tuple[str, str]],
) -> str:
    parts: list[str] = []

    if added:
        preview = added[:10]
        text = "\n".join(f"• {kw}" for kw in preview)
        if len(added) > 10:
            text += f"\n...\n{t('keywords_and_more', lang=lang, count=len(added) - 10)}"
        parts.append(f"✅ {t('keywords_added_count', lang=lang, count=len(added))}\n{text}")

    if skipped:
        preview = skipped[:5]
        text = "\n".join(f"• {kw}" for kw in preview)
        if len(skipped) > 5:
            text += f"\n...\n{t('keywords_and_more', lang=lang, count=len(skipped) - 5)}"
        parts.append(f"⚠️ {t('keywords_already_added', lang=lang, count=len(skipped))}:\n{text}")

    if errors:
        text = "\n".join(f"• {kw}: {err}" for kw, err in errors[:3])
        if len(errors) > 3:
            text += f"\n...\n{t('keywords_and_more_errors', lang=lang, count=len(errors) - 3)}"
        parts.append(f"❌ {t('keywords_add_errors', lang=lang)}:\n{text}")

    parts.append(
        f"📊 {t('keywords_summary', lang=lang)}\n"
        f"• {t('keywords_added', lang=lang)}: {len(added)}\n"
        f"• {t('keywords_skipped', lang=lang)}: {len(skipped)}\n"
        f"• {t('keywords_errors', lang=lang)}: {len(errors)}"
    )
    return "\n\n".join(parts)


async def show_keywords_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    if state is not None:
        await state.clear()
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    count = get_keywords_count(user_id=event.from_user.id)
    mode = get_user_match_mode(event.from_user.id)
    mode_label = t(f"match_mode_{mode}_name", lang=lang)
    await edit_or_answer(
        event,
        t("keywords_menu_message", lang=lang, count=count, match_mode=mode_label),
        reply_markup=keywords_menu_keyboard(lang=lang),
    )


def _list_page_data(user_id: int, page: int) -> tuple[list[tuple[int, str]], int, int]:
    model = _ensure_keywords_model(user_id)
    total = model.select().count()
    max_page = max(0, (total - 1) // KEYWORDS_PAGE_SIZE) if total else 0
    page = max(0, min(page, max_page))
    rows = list(
        model.select()
        .order_by(model.id)
        .offset(page * KEYWORDS_PAGE_SIZE)
        .limit(KEYWORDS_PAGE_SIZE)
    )
    items = [(row.id, row.user_keyword) for row in rows]
    return items, total, page


async def show_keywords_list(event: Message | CallbackQuery, page: int = 0) -> None:
    user = User.get(User.user_id == event.from_user.id)
    lang = _user_lang(user)
    items, total, page = _list_page_data(event.from_user.id, page)

    if total == 0:
        await edit_or_answer(
            event,
            t("no_keywords_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
        )
        return

    lines = [t("keywords_list_title", lang=lang, count=total, page=page + 1)]
    for kw_id, text in items:
        short = text if len(text) <= 60 else text[:57] + "…"
        lines.append(f"• <code>{short}</code>")

    await edit_or_answer(
        event,
        "\n".join(lines),
        reply_markup=keywords_list_keyboard(
            lang=lang,
            items=items,
            page=page,
            total=total,
            page_size=KEYWORDS_PAGE_SIZE,
        ),
    )


@router.callback_query(F.data.in_({"menu:keywords", "back:keywords"}))
async def handle_keywords_menu(callback: CallbackQuery, state: FSMContext):
    await show_keywords_menu(callback, state)


@router.callback_query(F.data == "menu:match_mode")
async def handle_match_mode_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    mode = get_user_match_mode(callback.from_user.id)
    await edit_or_answer(
        callback,
        t("match_mode_message", lang=lang, current=t(f"match_mode_{mode}_name", lang=lang)),
        reply_markup=match_mode_keyboard(lang=lang, current=mode),
    )


@router.callback_query(F.data.startswith("menu:match_mode:"))
async def handle_match_mode_set(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    mode = callback.data.rsplit(":", 1)[-1]
    mode = set_user_match_mode(callback.from_user.id, mode)
    await callback.answer(t("match_mode_saved", lang=lang, mode=t(f"match_mode_{mode}_name", lang=lang)))
    await edit_or_answer(
        callback,
        t("match_mode_message", lang=lang, current=t(f"match_mode_{mode}_name", lang=lang)),
        reply_markup=match_mode_keyboard(lang=lang, current=mode),
    )


def _format_check_why(detail: MatchDetail, lang: str) -> str:
    mode_name = t(f"match_mode_{detail.mode}_name", lang=lang)
    tokens = ", ".join(detail.hit_tokens) if detail.hit_tokens else detail.keyword
    if detail.reason == "exact":
        return t("alert_why_exact", lang=lang, mode=mode_name)
    if detail.reason == "loose":
        return t("alert_why_loose", lang=lang, mode=mode_name, tokens=tokens)
    return t("alert_why_tokens", lang=lang, mode=mode_name, tokens=tokens)


@router.callback_query(F.data == "menu:keywords:check")
async def handle_match_check_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    count = get_keywords_count(callback.from_user.id)
    if count <= 0:
        await callback.answer(t("match_check_no_keywords", lang=lang), show_alert=True)
        return
    mode = get_user_match_mode(callback.from_user.id)
    await edit_or_answer(
        callback,
        t(
            "match_check_prompt",
            lang=lang,
            count=count,
            mode=t(f"match_mode_{mode}_name", lang=lang),
        ),
        reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
    )
    await state.set_state(MyStates.waiting_for_match_check)


@router.message(MyStates.waiting_for_match_check, F.text)
async def handle_match_check_text(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _user_lang(user)
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("match_check_empty", lang=lang))
        return

    model = _ensure_keywords_model(message.from_user.id)
    keywords = [kw.user_keyword for kw in model.select() if kw.user_keyword]
    mode = get_user_match_mode(message.from_user.id)
    matches = find_all_matching_keyword_details(text, keywords, mode=mode)
    stop_hit = find_stopword(text, get_user_stopwords(message.from_user.id))

    preview = text if len(text) <= 400 else text[:400] + "…"
    if not matches:
        body = t(
            "match_check_none",
            lang=lang,
            mode=t(f"match_mode_{mode}_name", lang=lang),
            checked=len(keywords),
            preview=html.escape(preview),
        )
    else:
        rows = []
        for i, detail in enumerate(matches[:30], 1):
            why = _format_check_why(detail, lang)
            rows.append(
                t(
                    "match_check_row",
                    lang=lang,
                    n=i,
                    keyword=html.escape(detail.keyword),
                    why=html.escape(why),
                )
            )
        more = ""
        if len(matches) > 30:
            more = t("match_check_more", lang=lang, count=len(matches) - 30)
        body = t(
            "match_check_hits",
            lang=lang,
            mode=t(f"match_mode_{mode}_name", lang=lang),
            checked=len(keywords),
            hit_count=len(matches),
            rows="\n".join(rows),
            more=more,
            preview=html.escape(preview),
        )

    if stop_hit:
        body += "\n\n" + t(
            "match_check_stopword",
            lang=lang,
            stopword=html.escape(stop_hit),
        )

    body += "\n\n" + t("match_check_again_hint", lang=lang)

    await message.answer(
        body,
        parse_mode="HTML",
        reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
    )


@router.message(MyStates.waiting_for_match_check)
async def handle_match_check_non_text(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _user_lang(user)
    await message.answer(t("match_check_need_text", lang=lang))


@router.callback_query(F.data.in_({"menu:settings:enter_keyword", "menu:keywords:add"}))
async def handle_enter_keyword_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    logger.info("keywords_add_menu", user_id=callback.from_user.id)
    await edit_or_answer(
        callback,
        t("enter_keyword", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
    )
    await state.set_state(MyStates.entering_keyword)


@router.message(MyStates.entering_keyword, F.document)
async def handle_keywords_file(message: Message, state: FSMContext):
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

    keywords_list = _parse_keywords_text(content)
    if not keywords_list:
        await message.answer(
            t("no_keywords_entered", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
        )
        await state.clear()
        return

    added, skipped, errors = _import_keywords(message.from_user.id, keywords_list)
    await message.answer(
        _format_import_report(lang, added, skipped, errors),
        reply_markup=after_setup_keyboard(
            lang, message.from_user.id, keywords_menu_keyboard(lang=lang)
        ),
    )
    logger.info(
        "keywords_import_file",
        user_id=message.from_user.id,
        added=len(added),
        skipped=len(skipped),
        errors=len(errors),
    )
    await state.clear()


@router.message(MyStates.entering_keyword, F.text)
async def handle_keywords_submission(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _user_lang(user)
    keywords_list = _parse_keywords_text(message.text or "")

    if not keywords_list:
        await message.answer(t("no_keywords_entered", lang=lang))
        return

    added, skipped, errors = _import_keywords(message.from_user.id, keywords_list)
    await message.answer(
        _format_import_report(lang, added, skipped, errors),
        reply_markup=after_setup_keyboard(
            lang, message.from_user.id, keywords_menu_keyboard(lang=lang)
        ),
    )
    logger.info(
        "keywords_import_text",
        user_id=message.from_user.id,
        added=len(added),
        skipped=len(skipped),
        errors=len(errors),
    )
    await state.clear()


@router.callback_query(F.data.in_({"menu:keywords:list", "menu:settings:keywords"}))
async def handle_keywords_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_keywords_list(callback, page=0)


@router.callback_query(F.data.startswith("menu:keywords:page:"))
async def handle_keywords_page(callback: CallbackQuery):
    try:
        page = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        page = 0
    await show_keywords_list(callback, page=page)


@router.callback_query(F.data.startswith("menu:keywords:del:"))
async def handle_keywords_delete(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    parts = callback.data.split(":")
    # menu:keywords:del:{id}:{page}
    try:
        kw_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
    except (IndexError, ValueError):
        await callback.answer("Error", show_alert=True)
        return

    model = _ensure_keywords_model(callback.from_user.id)
    row = model.get_or_none(model.id == kw_id)
    if not row:
        await callback.answer(t("keyword_delete_missing", lang=lang), show_alert=True)
        await show_keywords_list(callback, page=page)
        return

    text = row.user_keyword
    row.delete_instance()
    await callback.answer(t("keyword_deleted", lang=lang, keyword=text[:40]), show_alert=False)
    await show_keywords_list(callback, page=page)


@router.callback_query(F.data == "menu:keywords:export:txt")
async def handle_keywords_export_txt(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    model = _ensure_keywords_model(callback.from_user.id)
    keywords = list(model.select().order_by(model.id))

    if not keywords:
        await callback.message.answer(
            t("no_keywords_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
        )
        return

    content = "\n".join(k.user_keyword for k in keywords) + "\n"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keywords_{callback.from_user.id}_{timestamp}.txt"
    document = BufferedInputFile(content.encode("utf-8"), filename=filename)
    await callback.message.answer_document(
        document=document,
        caption=t("keywords_export_caption", lang=lang, count=len(keywords)),
        reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
    )


@router.callback_query(F.data == "menu:keywords:export:xlsx")
async def handle_keywords_export_xlsx(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _user_lang(user)
    model = _ensure_keywords_model(callback.from_user.id)
    keywords = list(model.select().order_by(model.id))

    if not keywords:
        await callback.message.answer(
            t("no_keywords_found", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
        )
        return

    data = [(idx, kw.user_keyword) for idx, kw in enumerate(keywords, start=1)]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keywords_{callback.from_user.id}_{timestamp}.xlsx"
    headers = [t("excel_header_number", lang=lang), t("excel_header_keyword", lang=lang)]

    try:
        filepath = create_excel_file(
            data=data,
            headers=headers,
            filename=filename,
            sheet_name="Keywords",
        )
        await callback.message.answer_document(
            document=FSInputFile(filepath),
            caption=t("keywords_export_caption", lang=lang, count=len(data)),
            reply_markup=back_keyboard(lang=lang, callback_data="back:keywords"),
        )
        os.remove(filepath)
    except Exception as e:
        logger.exception("keywords_export_xlsx_error", error=e)
        await callback.message.answer(t("export_error", lang=lang))
