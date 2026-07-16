import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from account_manager.auth import CheckingAccountsValidity
from account_manager.unsubscribe import unsubscribe
from database.database import dell_group, delete_all_user_groups, get_tracked_channels_count, get_user_accounts, User
from account_manager.parser import is_tracking_marked
from core.config import ADMIN_USER_IDS
from keyboards.user.keyboards import (
    back_keyboard, clear_all_channels_confirm_keyboard,
    resolve_main_keyboard, settings_keyboard,
)
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.callback_query(F.data == "menu:settings:clear_channels")
async def clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    """Запрос подтверждения очистки всего списка отслеживания."""
    await state.clear()

    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    count = get_tracked_channels_count(callback.from_user.id)

    if count == 0:
        await callback.message.edit_text(
            t("clear_all_channels_empty", lang=user.language),
            reply_markup=settings_keyboard(lang=user.language),
        )
        return

    await callback.message.edit_text(
        t("clear_all_channels_confirm", lang=user.language, count=count),
        reply_markup=clear_all_channels_confirm_keyboard(lang=user.language),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "clear_channels_confirm")
async def confirm_clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    count = get_tracked_channels_count(callback.from_user.id)

    if count == 0:
        await callback.message.edit_text(t("clear_all_channels_empty", lang=user.language))
        await callback.answer()
        return

    deleted = delete_all_user_groups(callback.from_user.id)
    await callback.message.edit_text(
        t("clear_all_channels_success", lang=user.language, count=deleted),
    )
    await callback.answer()
    logger.info(f"Пользователь {callback.from_user.id} очистил список отслеживания ({deleted} записей)")


@router.callback_query(F.data == "clear_channels_cancel")
async def cancel_clear_all_tracked_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    await callback.message.edit_text(t("clear_all_channels_cancelled", lang=user.language))
    await callback.answer()


@router.callback_query(F.data == "menu:settings:delete_group")
async def delete_group_from_database(callback: CallbackQuery, state: FSMContext):
    """
    Удаление группы из базы данных
    """
    await state.clear()  # Сбрасываем текущее состояние FSM

    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    await callback.message.edit_text(
        t("delete_group_prompt", lang=user.language),
        reply_markup=back_keyboard(lang=user.language, callback_data="back:settings")
    )
    await state.set_state(MyStates.del_username_groups)


@router.message(MyStates.del_username_groups, F.text)
async def del_user_in_db(message: Message, state: FSMContext) -> None:
    """
    Удаляем группу из отслеживания
    """
    user = User.get(User.user_id == message.from_user.id)
    group_username = message.text.strip()
    await state.clear()  # Завершаем текущее состояние машины состояния
    logger.info(f"Пользователь ввёл ссылку для удаления: {group_username}")

    deletion_result = dell_group(user_id=message.from_user.id, username=group_username)

    main_kb = resolve_main_keyboard(
        user.language,
        tracking_active=await is_tracking_marked(message.from_user.id),
        is_admin=message.from_user.id in ADMIN_USER_IDS,
    )

    if deletion_result:
        await message.answer(
            text=t("group_deleted", lang=user.language, group=group_username),
            reply_markup=main_kb
        )
        logger.info(f"Пользователь {message.from_user.id} удалил группу @{group_username}")
    else:
        await message.answer(
            text=t("group_not_found", lang=user.language, group=group_username),
            reply_markup=main_kb
        )
        logger.warning(f"Попытка удалить несуществующую группу @{group_username} пользователем {message.from_user.id}")

    # Получаем все аккаунты пользователя из его персональной таблицы
    accounts = get_user_accounts(message.from_user.id)

    if not accounts:
        logger.warning(f"⚠️ У пользователя {message.from_user.id} нет подключённых аккаунтов в БД")
        await message.answer(
            t("no_accounts", lang=user.language),
            reply_markup=resolve_main_keyboard(
                user.language,
                tracking_active=await is_tracking_marked(message.from_user.id),
                is_admin=message.from_user.id in ADMIN_USER_IDS,
            ),
        )
        return None
    logger.info(f"📦 Найдено {len(accounts)} аккаунтов в БД для пользователя {message.from_user.id}")

    checker = CheckingAccountsValidity(message=message)  # ✅ Сохраняем активный клиент
    client = await checker.client_connect_string_session(accounts[0]['session_string'])

    await unsubscribe(client, group_username)  # Отписываемся от группы или канала по username

    client.disconnect()
