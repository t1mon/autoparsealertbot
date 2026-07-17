"""Очистка списка каналов (подтверждение). CRUD каналов — в handlers.user.channels."""

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.database import User, delete_all_user_groups, get_tracked_channels_count
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import channels_menu_keyboard
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.callback_query(F.data == "menu:settings:clear_channels")
async def clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    """Совместимость старой кнопки: открыть подменю каналов."""
    from handlers.user.channels import show_channels_menu

    await show_channels_menu(callback, state)


@router.callback_query(F.data == "clear_channels_confirm")
async def confirm_clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = user.language if user.language != "unset" else "ru"
    count = get_tracked_channels_count(callback.from_user.id)

    if count == 0:
        await edit_or_answer(
            callback,
            t("clear_all_channels_empty", lang=lang),
            reply_markup=channels_menu_keyboard(lang=lang),
        )
        return

    deleted = delete_all_user_groups(callback.from_user.id)
    await edit_or_answer(
        callback,
        t("clear_all_channels_success", lang=lang, count=deleted),
        reply_markup=channels_menu_keyboard(lang=lang),
    )
    logger.info("channels_cleared", user_id=callback.from_user.id, deleted=deleted)


@router.callback_query(F.data == "clear_channels_cancel")
async def cancel_clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    from handlers.user.channels import show_channels_menu

    await show_channels_menu(callback, state)
