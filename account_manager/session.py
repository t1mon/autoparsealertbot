import random

import structlog

logger = structlog.get_logger(__name__)
from telethon import TelegramClient
from telethon.sessions import StringSession

from core.config import ADMIN_USER_IDS, API_ID, API_HASH
from database.database import get_user_accounts
from keyboards.user.keyboards import resolve_main_keyboard
from locales.locales import t


async def _main_kb(user, user_id):
    from account_manager.parser import is_tracking_marked
    return resolve_main_keyboard(
        user.language,
        tracking_active=await is_tracking_marked(user_id),
        is_admin=int(user_id) in ADMIN_USER_IDS,
    )


async def find_session_file(user_id: int, user, message):
    """
    Получает валидную StringSession из базы данных пользователя.

    :param user_id: (int) ID пользователя Telegram
    :param user: (User) Модель пользователя из БД (для языка и уведомлений)
    :param message: (aiogram.types.Message) Для отправки ответа
    :return: dict с данными аккаунта {"session_string": str, "phone": str} или None
    """
    try:
        # Получаем все аккаунты пользователя из его персональной таблицы
        accounts = get_user_accounts(user_id)

        if not accounts:
            logger.warning(f"⚠️ У пользователя {user_id} нет подключённых аккаунтов в БД")
            await message.answer(
                t("no_accounts", lang=user.language),
                reply_markup=await _main_kb(user, user_id)
            )
            return None

        logger.info(f"📦 Найдено {len(accounts)} аккаунтов в БД для пользователя {user_id}")

        # Случайным образом выбираем один аккаунт (можно изменить логику выбора)
        selected_account = random.choice(accounts)
        session_string = selected_account["session_string"]
        phone = selected_account["phone_number"]

        # Быстрая проверка валидности StringSession (опционально, но рекомендуется)
        if not await _is_session_valid(session_string):
            logger.warning(f"⚠️ Сессия {phone} не валидна — удаляем из БД")
            await message.answer(
                t("session_invalid", lang=user.language, phone=phone),
                reply_markup=await _main_kb(user, user_id)
            )
            # Удаляем невалидную сессию из БД

            # Рекурсивно пробуем найти другой аккаунт
            return await find_session_file(user_id, user, message)

        logger.info(f"✅ Выбрана сессия: {phone} (первые 30 символов: {session_string[:30]}...)")

        return {
            "session_string": session_string,
            "phone_number": phone
        }

    except Exception as e:
        logger.exception(f"❌ Ошибка получения аккаунта из БД для пользователя {user_id}: {e}")
        await message.answer(
            t("account_fetch_error", lang=user.language),
            reply_markup=await _main_kb(user, user_id)
        )
        return None


async def _is_session_valid(session_string: str) -> bool:
    """
    Быстрая проверка валидности StringSession без полноценного подключения.

    :param session_string: Строка сессии Telethon
    :return: True если сессия выглядит валидной, False если нет
    """

    # Простая проверка: сессия не должна быть пустой и должна иметь правильный формат
    if not session_string or len(session_string) < 50:
        return False

    # Пробуем создать клиент и подключиться (быстрый тест)
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)

    try:
        await client.connect()
        is_authorized = await client.is_user_authorized()
        await client.disconnect()
        return is_authorized
    except Exception as e:
        logger.debug(f"⚠️ Проверка сессии не прошла: {type(e).__name__}")
        try:
            await client.disconnect()
        except Exception as e:
            logger.exception("session_lookup_error", error=e)
            # pass
        return False
