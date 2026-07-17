"""Стоп-слова (чёрный список): не алертить, если слово есть в тексте."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.database import (
    User,
    add_stopwords,
    delete_stopword,
    get_stopwords_count,
    list_stopwords,
)
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import (
    back_keyboard,
    stopwords_list_keyboard,
    stopwords_menu_keyboard,
)
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)

PAGE_SIZE = 10


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


def _parse_words(raw: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        word = line.strip()
        if not word or word in seen:
            continue
        seen.add(word)
        result.append(word)
    return result


def _format_import_report(
    lang: str,
    added: list[str],
    skipped: list[str],
    errors: list[tuple[str, str]],
) -> str:
    parts: list[str] = []
    if added:
        preview = "\n".join(f"• {w}" for w in added[:10])
        if len(added) > 10:
            preview += f"\n… (+{len(added) - 10})"
        parts.append(f"✅ {t('stopwords_added_count', lang=lang, count=len(added))}\n{preview}")
    if skipped:
        parts.append(f"⚠️ {t('stopwords_already_added', lang=lang, count=len(skipped))}")
    if errors:
        parts.append(f"❌ {t('stopwords_add_errors', lang=lang)}: {len(errors)}")
    return "\n\n".join(parts) if parts else t("stopwords_empty_input", lang=lang)


async def show_stopwords_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    if state is not None:
        await state.clear()
    user = User.get(User.user_id == event.from_user.id)
    lang = _lang(user)
    count = get_stopwords_count(event.from_user.id)
    await edit_or_answer(
        event,
        t("stopwords_menu_message", lang=lang, count=count),
        reply_markup=stopwords_menu_keyboard(lang=lang),
    )


async def show_stopwords_list(event: Message | CallbackQuery, page: int = 0) -> None:
    user = User.get(User.user_id == event.from_user.id)
    lang = _lang(user)
    items, total, page = list_stopwords(event.from_user.id, page=page, page_size=PAGE_SIZE)
    if total == 0:
        await edit_or_answer(
            event,
            t("stopwords_list_empty", lang=lang),
            reply_markup=back_keyboard(lang=lang, callback_data="back:stopwords"),
        )
        return
    lines = [t("stopwords_list_title", lang=lang, count=total, page=page + 1)]
    for _, text in items:
        short = text if len(text) <= 60 else text[:57] + "…"
        lines.append(f"• <code>{short}</code>")
    await edit_or_answer(
        event,
        "\n".join(lines),
        reply_markup=stopwords_list_keyboard(
            lang=lang,
            items=items,
            page=page,
            total=total,
            page_size=PAGE_SIZE,
        ),
    )


@router.callback_query(F.data.in_({"menu:stopwords", "back:stopwords"}))
async def handle_stopwords_menu(callback: CallbackQuery, state: FSMContext):
    await show_stopwords_menu(callback, state)


@router.callback_query(F.data == "menu:stopwords:add")
async def handle_stopwords_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    await edit_or_answer(
        callback,
        t("stopwords_add_prompt", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:stopwords"),
    )
    await state.set_state(MyStates.entering_stopword)


@router.message(MyStates.entering_stopword, F.document)
async def handle_stopwords_file(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _lang(user)
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

    words = _parse_words(content)
    if not words:
        await message.answer(t("stopwords_empty_input", lang=lang))
        await state.clear()
        return

    added, skipped, errors = add_stopwords(message.from_user.id, words)
    await message.answer(
        _format_import_report(lang, added, skipped, errors),
        reply_markup=stopwords_menu_keyboard(lang=lang),
    )
    await state.clear()


@router.message(MyStates.entering_stopword, F.text)
async def handle_stopwords_text(message: Message, state: FSMContext):
    user = User.get(User.user_id == message.from_user.id)
    lang = _lang(user)
    words = _parse_words(message.text or "")
    if not words:
        await message.answer(t("stopwords_empty_input", lang=lang))
        return

    added, skipped, errors = add_stopwords(message.from_user.id, words)
    await message.answer(
        _format_import_report(lang, added, skipped, errors),
        reply_markup=stopwords_menu_keyboard(lang=lang),
    )
    await state.clear()


@router.callback_query(F.data == "menu:stopwords:list")
async def handle_stopwords_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_stopwords_list(callback, page=0)


@router.callback_query(F.data.startswith("menu:stopwords:page:"))
async def handle_stopwords_page(callback: CallbackQuery):
    try:
        page = int(callback.data.rsplit(":", 1)[-1])
    except ValueError:
        page = 0
    await show_stopwords_list(callback, page=page)


@router.callback_query(F.data.startswith("menu:stopwords:del:"))
async def handle_stopwords_delete(callback: CallbackQuery):
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    parts = callback.data.split(":")
    try:
        sw_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
    except (IndexError, ValueError):
        await callback.answer("Error", show_alert=True)
        return

    text = delete_stopword(callback.from_user.id, sw_id)
    if not text:
        await callback.answer(t("stopwords_missing", lang=lang), show_alert=True)
        return

    await callback.answer(t("stopwords_deleted", lang=lang, word=text[:40]))
    await show_stopwords_list(callback, page=page)
