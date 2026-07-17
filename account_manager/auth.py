import asyncio
import csv
import os
import random
from pathlib import Path

from aiogram.types import Message
import structlog

logger = structlog.get_logger(__name__)
from telethon import TelegramClient
from telethon.errors import (
    AuthKeyDuplicatedError, TimedOutError, PhoneNumberBannedError, UserDeactivatedBanError, AuthKeyNotFound,
    AuthKeyUnregisteredError
)
from telethon.sessions import StringSession

from core.config import API_ID, API_HASH
from database.database import User, delete_account_from_db, get_active_account, getting_account
from locales.locales import t

mobile_device = {
    "device_model": "Pixel 5",
    "system_version": "11",
    "app_version": "8.4.1",
    "lang_code": "en",
    "system_lang_code": "en-US",
}


async def get_account_info(client: TelegramClient) -> dict:
    """
    Получает информацию о пользователе Telegram через client.get_me().

    :param client: Авторизованный клиент Telethon.
    :return: dict с полями: id, phone, first_name, last_name, username
    """
    me = await client.get_me()
    phone = me.phone or ""
    logger.info(f"🧾 Аккаунт: | ID: {me.id} | Phone: {phone}")

    return {
        "id": me.id,  # Идентификатор пользователя Telegram
        "phone": phone,  # Номер телефона пользователя Telegram
        "first_name": me.first_name,  # Имя пользователя Telegram
        "last_name": me.last_name,  # Фамилия пользователя Telegram
        "username": me.username  # Никнейм пользователя Telegram
    }


class CheckingAccountsValidity:

    def __init__(self, message: Message, path: str | None = None, user_id: int | None = None):
        """
        :param message: Сообщение для отправки уведомлений (опционально)
        :param path: Путь к папке с .session файлами (опционально)
        """
        self.message = message
        self.path = Path(path) if path else None
        self.user_id = user_id if user_id is not None else message.from_user.id

    async def client_connect_string_session(
        self,
        session_name,
        *,
        for_tracking: bool = False,
    ) -> TelegramClient | None:
        """
        Подключение к Telegram аккаунту через StringSession

        :param session_name: Имя аккаунта для подключения (файл .session)
        :param for_tracking: долгий клиент — бесконечные внутренние retries
        :return: Клиент Telegram или None, если подключение не удалось
        """
        client_kwargs: dict = {}
        if for_tracking:
            # Внутренний auto-reconnect Telethon + наш внешний цикл в parser
            client_kwargs["connection_retries"] = None
            client_kwargs["retry_delay"] = 2
            client_kwargs["auto_reconnect"] = True

        client = TelegramClient(
            StringSession(session_name),
            api_id=API_ID,
            api_hash=API_HASH,
            device_model=mobile_device["device_model"],
            system_version=mobile_device["system_version"],
            app_version=mobile_device["app_version"],
            lang_code=mobile_device["lang_code"],
            system_lang_code=mobile_device["system_lang_code"],
            **client_kwargs,
        )

        try:
            await client.connect()

            if not await client.is_user_authorized():
                logger.error("❌ Сессия недействительна или аккаунт не авторизован!")
                await self.write_csv(data=session_name)
                try:
                    await client.disconnect()
                except ValueError:
                    logger.error("❌ Сессия недействительна или аккаунт не авторизован!")
                return None

            await get_account_info(client)
            return client

        except AuthKeyDuplicatedError:
            logger.error(
                "❌ AuthKeyDuplicatedError: Повторный ввод ключа авторизации "
                "(сессия используется в другом месте)")
            await client.disconnect()
            await self.write_csv(data=session_name)
            return None
        except Exception as e:
            logger.exception(f"Ошибка подключения: {e}")
            await client.disconnect()
            return None

    async def write_csv(self, data):
        """
        Запись данных в CSV файл.
        :param data: Список значений (например, список аккаунтов)
        """
        with open('file.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([data])

    async def read_invalid_sessions(self) -> list[str]:
        """Чтение всех невалидных сессий из CSV"""
        invalid_sessions = []
        if os.path.exists('file.csv'):
            with open('file.csv', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        invalid_sessions.append(row[0])
        return invalid_sessions

    async def verify_account(self, session_name) -> None:
        """
        Проверяет и сортирует аккаунты.
        :param session_name: Имя аккаунта для проверки
        """
        try:
            logger.info(f"Проверка аккаунта {session_name}")
            client: TelegramClient = await self.client_connect_string_session(session_name=session_name)

            if client is None:
                return

            try:
                if not await client.is_user_authorized():
                    await client.disconnect()
                    await asyncio.sleep(5)
                    await self.write_csv(data=session_name)
                else:
                    logger.info(f"Аккаунт {session_name} авторизован")
                    await client.disconnect()
            except (PhoneNumberBannedError, UserDeactivatedBanError, AuthKeyNotFound,
                    AuthKeyUnregisteredError, AuthKeyDuplicatedError) as e:
                await delete_account_from_db(session_string=session_name)
            except TimedOutError as e:
                logger.exception("account_validation_error", error=e)
                await asyncio.sleep(2)
            except AttributeError:
                pass

            invalid_sessions = await self.read_invalid_sessions()
            logger.info(f"❌ Невалидные сессии: {invalid_sessions}")
            for session in invalid_sessions:
                await delete_account_from_db(session_string=session)

            try:
                os.remove("file.csv")
            except FileNotFoundError:
                pass

        except Exception as error:
            logger.exception(error)

    async def connect_client(self) -> TelegramClient | None:
        """
        Подключение клиента Telethon и проверка сессии.
        :return: client или None, если сессия невалидна
        """
        client = TelegramClient(
            self.path,
            api_id=API_ID,
            api_hash=API_HASH,
            device_model=mobile_device["device_model"],
            system_version=mobile_device["system_version"],
            app_version=mobile_device["app_version"],
            lang_code=mobile_device["lang_code"],
            system_lang_code=mobile_device["system_lang_code"],
        )
        try:
            await client.connect()

            if not await client.is_user_authorized():
                logger.warning(f"⚠️ Сессия {self.path} не авторизована")
                return None
            account_info = await get_account_info(client)
            logger.info(f"✅ Сессия активна: {account_info['phone'] or account_info['id']}")
            return client
        except Exception as e:
            logger.exception(f"Ошибка подключения к {self.path}: {e}")
            return None

    async def start_user_client(self, user_id: int | None = None, *, notify: bool = True) -> TelegramClient | None:
        """
        Подключает Telethon-клиент через аккаунт пользователя из UserAccountsTable.
        """
        uid = user_id if user_id is not None else self.user_id
        selected = get_active_account(uid)
        if not selected:
            logger.warning(f"⚠️ У пользователя {uid} нет подключённых аккаунтов в БД")
            if notify and self.message:
                from keyboards.user.keyboards import connect_keyboard_account
                user = User.get(User.user_id == uid)
                lang = user.language if user.language != "unset" else "ru"
                await self.message.answer(
                    t("no_accounts", lang=lang),
                    reply_markup=connect_keyboard_account(lang=lang),
                )
            return None

        logger.info(f"Используется аккаунт пользователя {uid}: {selected.get('phone_number', 'unknown')}")
        return await self.client_connect_string_session(selected["session_string"])

    async def start_random_client(self):
        """
        Запускает Telegram-клиент со случайной сессией из указанной папки.
        :return: Авторизованный TelegramClient или None
        """
        try:
            records = getting_account()
            chosen_session_name = random.choice(records)

            if not chosen_session_name or not isinstance(chosen_session_name, str):
                logger.error(f"❌ Неверный формат сессии: {type(chosen_session_name)}")
                return None

            logger.info(f"Используется сессия: {chosen_session_name[:30]}...")

            return await self.client_connect_string_session(chosen_session_name)

        except Exception as e:
            logger.exception(f"❌ Ошибка запуска клиента: {e}")
            return None
