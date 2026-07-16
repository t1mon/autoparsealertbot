import os
import random
import shutil
from pathlib import Path

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from telethon.sessions import StringSession

from account_manager.auth import CheckingAccountsValidity, get_account_info
from database.database import User, getting_free_account, AccountFree
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import back_keyboard, connect_keyboard_account
from locales.locales import t
from states.states import MyStates
from database.database import write_account_to_user_table

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.callback_query(F.data == "menu:settings:connect_account")
async def handle_connect_account_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"
    await edit_or_answer(
        callback,
        t("connect_account", lang=user_lang),
        reply_markup=connect_keyboard_account(lang=user_lang),
    )


@router.callback_query(F.data == "menu:connect:free")
async def handle_connect_account_free(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "🔐 Подключить свободный аккаунт".

    Очищает текущее состояние FSM, регистрирует пользователя в базе данных (если его ещё нет)
    с языком по умолчанию "unset", и отправляет пользователю сообщение с приглашением
    🔐 Подключить свободный аккаунт через автоматическое подключение свободного аккаунта.

    :param message: (Message) Объект входящего сообщения от пользователя.
    :param state: (FSMContext) Контекст машины состояний, используется для сброса текущего состояния.
    """
    await state.clear()  # Завершаем текущее состояние машины состояния
    await callback.answer()
    message = callback.message

    # Создаём пользователя с language = "unset", если его нет
    user, created = User.get_or_create(
        user_id=callback.from_user.id,
        defaults={
            "username": callback.from_user.username,
            "first_name": callback.from_user.first_name,
            "last_name": callback.from_user.last_name,
            "language": "unset"  # ← ключевое: "unset" = язык не выбран
        }
    )
    user_lang = user.language if user.language != "unset" else "ru"

    # Подключение свободного аккаунта
    free_accounts = list(AccountFree.select())
    if not free_accounts:
        logger.warning(f"Нет доступных свободных аккаунтов для пользователя {user.user_id}")
        await message.answer(
            text=t("no_free_accounts", lang=user_lang),
            reply_markup=back_keyboard(lang=user_lang, callback_data="back:settings")
        )
        return

    # Выбираем случайный свободный аккаунт
    selected_account = random.choice(free_accounts)
    session_string = selected_account.session_string
    phone_number = selected_account.phone_number

    logger.info(f"Подключаем свободный аккаунт {phone_number} пользователю {user.user_id}")

    # Записываем в персональную таблицу аккаунтов пользователя
    write_account_to_user_table(
        user_id=user.user_id,
        session_string=session_string,
        phone_number=phone_number
    )

    # Удаляем аккаунт из свободных аккаунтов, чтобы другие не могли его использовать
    selected_account.delete_instance()

    await message.answer(
        text=t("account_connected_free", lang=user_lang),
        reply_markup=back_keyboard(lang=user_lang, callback_data="back:settings")
    )


def creates_temporary_folder_for_accounts():
    """
    Создание временной папки для аккаунтов пользователя.
    :return:
    """
    sessions_dir = Path("accounts")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def sanitization_file_name(document, sessions_dir):
    """
    Очистка имени файла от недопустимых символов (файлов сессии).
    :return:
    """
    safe_file_name = "".join(c for c in document.file_name if c.isalnum() or c in "._-")
    local_file_path = sessions_dir / safe_file_name
    return local_file_path, safe_file_name


@router.callback_query(F.data == "menu:connect:account")
async def handle_connect_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user, created = User.get_or_create(
        user_id=callback.from_user.id,
        defaults={
            "username": callback.from_user.username,
            "first_name": callback.from_user.first_name,
            "last_name": callback.from_user.last_name,
            "language": "unset"
        }
    )
    user_lang = user.language if user.language != "unset" else "ru"
    await callback.message.edit_text(
        text=t("connect_account", lang=user_lang),
        reply_markup=back_keyboard(lang=user_lang, callback_data="back:settings")
    )
    await state.set_state(MyStates.waiting_for_session_file_user)


# ✅ Фильтр: только документы И только в нужном состоянии
@router.message(MyStates.waiting_for_session_file_user, F.document)
async def handle_account_file(message: Message, state: FSMContext):
    """Обработчик приёма файла сессии (.session) от пользователя"""
    local_file_path = None  # для безопасного удаления в finally

    user = User.get(User.user_id == message.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"

    try:
        logger.info(f"User {message.from_user.id} отправил файл: {message.document.file_name}")

        # ✅ Проверяем расширение — если не .session, остаёмся в состоянии
        if not message.document.file_name.endswith('.session'):
            await message.answer(t("invalid_session_file", lang=user_lang))
            return  # state НЕ сбрасываем — ждём правильный файл

        sessions_dir = creates_temporary_folder_for_accounts()
        local_file_path, safe_file_name = sanitization_file_name(message.document, sessions_dir)

        await message.bot.download(message.document, destination=local_file_path)
        logger.info(f"✅ Файл скачан: {local_file_path}")

        await message.answer(t("session_file_received", lang=user_lang, filename=safe_file_name))

        session_path_without_ext = str(local_file_path.with_suffix(""))
        checker = CheckingAccountsValidity(message=message, path=session_path_without_ext)
        client = await checker.connect_client()

        if client:
            account_info = await get_account_info(client)
            phone = account_info["phone"] or "unknown"
            first_name = account_info["first_name"] or ""

            session_string = StringSession.save(client.session)
            write_account_to_user_table(
                user_id=message.from_user.id,
                session_string=session_string,
                phone_number=phone
            )
            await client.disconnect()

            logger.info(f"✅ Сессия добавлена: {phone} | {first_name}")
            await message.answer(
                t("session_connected_success", lang=user_lang, filename=safe_file_name, phone=phone,
                  name=first_name),
                parse_mode="HTML"
            )
        else:
            logger.warning(f"❌ Сессия {safe_file_name} не валидна для пользователя {message.from_user.id}")
            await message.answer(
                t("session_validation_failed", lang=user_lang, filename=safe_file_name),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.exception(f"Ошибка при обработке сессии пользователя {message.from_user.id}: {e}")
        await message.answer(t("session_check_error", lang=user_lang))

    finally:
        # ✅ Удаляем временный файл в любом случае
        if local_file_path and local_file_path.exists():
            local_file_path.unlink()
        # ✅ Сбрасываем состояние только в конце
        await state.clear()
