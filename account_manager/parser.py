import asyncio
import html
import random
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import structlog

logger = structlog.get_logger(__name__)
from telethon import events, types
from telethon.errors import FloodWaitError, InviteRequestSentError
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import Channel

from account_manager.auth import CheckingAccountsValidity
from account_manager.chat_targets import (
    get_subscribed_refs,
    is_member_of_ref,
    resolve_tracking_targets,
)
from account_manager.subscription import subscription_telegram
from core.telegram_utils import chat_ref_label, normalize_telegram_chat_ref, normalize_telegram_username
from core.keyword_match import find_matching_keyword
from database.database import (
    create_keywords_model, create_group_model, TelegramGroup, get_user_accounts, get_user_channel_usernames, Groups,
    User
)
from keyboards.user.keyboards import connect_grup_keyboard_tech, resolve_main_keyboard
from locales.locales import t
from system.dispatcher import bot
from core.config import ADMIN_USER_IDS
from core import tracking_store

# 🧠 Простейший трекер сообщений (в памяти)
forwarded_messages = set()

# 🛑 Словарь активных клиентов и флагов остановки
active_clients = {}  # {user_id: client}
stop_flags = {}  # {user_id: asyncio.Event}
_user_locks: dict[str, asyncio.Lock] = {}


def is_tracking_active(user_id) -> bool:
    return str(user_id) in stop_flags


async def is_tracking_marked(user_id) -> bool:
    return str(user_id) in stop_flags or await tracking_store.is_marked(user_id)


def _user_lock(user_id) -> asyncio.Lock:
    key = str(user_id)
    if key not in _user_locks:
        _user_locks[key] = asyncio.Lock()
    return _user_locks[key]


async def begin_tracking(user_id) -> asyncio.Event | None:
    """Резервирует слот отслеживания. None — уже запущено."""
    user_id_str = str(user_id)
    async with _user_lock(user_id):
        if user_id_str in stop_flags:
            return None
        stop_event = asyncio.Event()
        stop_flags[user_id_str] = stop_event
        await tracking_store.mark_active(user_id)
        return stop_event


async def abort_tracking(user_id, user, message, *, notify: str | None = None):
    """Снимает флаг отслеживания и возвращает клавиатуру «Запуск»."""
    await tracking_store.unmark_active(user_id)
    stop_flags.pop(str(user_id), None)
    if notify:
        await message.answer(notify, reply_markup=_main_keyboard(user, user_id, tracking_active=False))


def _main_keyboard(user, user_id, *, tracking_active: bool | None = None):
    if tracking_active is None:
        tracking_active = is_tracking_active(user_id)
    return resolve_main_keyboard(
        user.language,
        tracking_active=tracking_active,
        is_admin=int(user_id) in ADMIN_USER_IDS,
    )


async def _sleep_with_stop(seconds: int, stop_event: asyncio.Event | None) -> bool:
    """Ждёт до `seconds` секунд. Возвращает True, если сработал флаг остановки."""
    if stop_event is None:
        await asyncio.sleep(seconds)
        return False
    for _ in range(seconds):
        if stop_event.is_set():
            return True
        await asyncio.sleep(1)
    return stop_event.is_set()


def _channel_key(username: str) -> str | None:
    canonical = normalize_telegram_chat_ref(username) or normalize_telegram_username(username)
    if not canonical:
        return None
    if canonical.startswith("@"):
        return canonical.lower()
    return canonical


def _count_matched_in_dialogs(db_channels: set, subscribed_usernames: set, subscribed_peer_ids: set) -> int:
    matched = 0
    for ch in db_channels:
        canonical = normalize_telegram_chat_ref(ch) or normalize_telegram_username(ch)
        if not canonical:
            continue
        if canonical.startswith("@") and canonical.lower() in subscribed_usernames:
            matched += 1
        elif canonical.startswith("id:"):
            try:
                if int(canonical[3:]) in subscribed_peer_ids:
                    matched += 1
            except ValueError:
                pass
    return matched


def _canonical_chat_refs(channels: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for channel in channels:
        normalized = normalize_telegram_chat_ref(channel) or normalize_telegram_username(channel)
        if not normalized:
            continue
        key = normalized.lower() if normalized.startswith("@") else normalized
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


async def _expand_with_discussion_chats(client, targets: list[str | int]) -> list[str | int]:
    """
    Добавляет к публичным каналам их привязанные группы обсуждений, чтобы ловить комментарии.
    """
    expanded: list[str | int] = []
    seen_ids: set[int] = set()
    seen_str: set[str] = set()

    for target in targets:
        if isinstance(target, str):
            key = target.lower()
            if key not in seen_str:
                seen_str.add(key)
                expanded.append(target)
        else:
            if target not in seen_ids:
                seen_ids.add(target)
                expanded.append(target)

        try:
            entity = await client.get_entity(target)
            if not isinstance(entity, Channel) or not getattr(entity, "broadcast", False):
                continue

            full_entity = await client(GetFullChannelRequest(channel=entity))
            linked_chat_id = getattr(full_entity.full_chat, "linked_chat_id", None)
            if not linked_chat_id or linked_chat_id in seen_ids:
                continue

            seen_ids.add(linked_chat_id)
            expanded.append(linked_chat_id)
            logger.info(
                f"💬 Добавлена группа обсуждений для {chat_ref_label(str(target))}: linked_chat_id={linked_chat_id}"
            )
        except Exception as e:
            logger.debug(f"Не удалось определить группу обсуждений для {target}: {e}")

    return expanded


async def get_subscribed_usernames(client) -> set[str]:
    usernames, _ = await get_subscribed_refs(client)
    return usernames


async def resolve_pending_subscriptions(
    client,
    db_channels: set,
    subscribed_usernames: set[str],
    subscribed_peer_ids: set[int],
) -> tuple[list[str], int]:
    """Чаты для подписки и число чатов, подтверждённых участником через API."""
    pending: list[str] = []
    confirmed_via_api = 0
    seen: set[str] = set()

    for channel in db_channels:
        canonical = normalize_telegram_chat_ref(channel) or normalize_telegram_username(channel)
        if not canonical:
            continue
        key = canonical.lower() if canonical.startswith("@") else canonical
        if key in seen:
            continue
        seen.add(key)

        if await is_member_of_ref(client, canonical, subscribed_usernames, subscribed_peer_ids):
            confirmed_via_api += 1
            continue

        pending.append(canonical)

    return pending, confirmed_via_api


def _log_tracking_channels(user_id, channels: list[str]) -> None:
    """Пишет в лог полный список чатов, поставленных на отслеживание."""
    if not channels:
        logger.warning(f"⚠️ Список чатов для отслеживания пуст (user_id={user_id})")
        return
    logger.info(f"📋 На отслеживание поставлено {len(channels)} чатов (user_id={user_id}):")
    for channel in channels:
        logger.info(f"   • {chat_ref_label(channel)}")


async def join_target_group(client, user_id, message):
    """
    Подписывает клиента Telethon на целевую группу пользователя для пересылки сообщений.

    Получает username целевой группы из персональной таблицы пользователя в базе данных и пытается присоединиться к ней.
    Возвращает идентификатор группы для дальнейшей отправки.

    - Использует модель `create_group_model` для доступа к данным пользователя.
    - Предполагается, что в таблице всегда одна запись (первый элемент списка).

    :param client: (TelegramClient) Активный клиент Telethon для выполнения запросов.
    :param user_id: (int) Уникальный идентификатор пользователя Telegram.
    :param message: (Message) Сообщение, которое вызвало команду (для ответа).
    :return: int or None: Идентификатор целевой группы (entity.id) или None при ошибке.

    :raises UserAlreadyParticipantError: Если клиент уже участник группы (обрабатывается).
    :raises FloodWaitError: Если достигнут лимит запросов (обрабатывается с задержкой).
    :raises InviteRequestSentError: Если требуется подтверждение приглашения.
    :raises Exception: Логируется при любых других ошибках.
    """
    user = User.get(User.user_id == user_id)
    group_model = create_group_model(user_id=user_id)
    logger.info(f"🔍 Проверяю целевую группу... {group_model}")
    if not group_model.table_exists():
        group_model.create_table()
        return None
    groups = list(group_model.select())
    logger.info(f"🔍 Проверяю целевую группу... {groups}")
    if not groups:
        logger.warning(f"❌ Не найдена целевая группа для пользователя {user_id}")
        # Если группа не найдена, то высылаем сообщение пользователю группы, что такой группы нет и клавиатуру для добавления группы для пересылки
        await message.answer(
            text=t("target_group_not_found", lang=user.language),
            reply_markup=connect_grup_keyboard_tech()
        )
        return None  # Возвращаем None, если группа не найдена
    target_username = normalize_telegram_username(groups[0].user_group)
    if not target_username:
        logger.error(f"❌ Целевая группа имеет пустой username для user_id={user_id}")
        await message.answer(
            text=t("target_group_not_found", lang=user.language),
            reply_markup=connect_grup_keyboard_tech()
        )
        return None
    try:
        target_usernames = f'https://t.me/{target_username.lstrip("@")}'
        # ToDo сделать общую функцию для подписки на канал / группу
        await client(JoinChannelRequest(target_usernames))
        # Получаем ID группы
        entity = await client.get_entity(target_username)
        return entity.id
    except FloodWaitError as e:
        logger.error(f"⚠️ FloodWait {e.seconds} сек.")
        await asyncio.sleep(e.seconds)
        try:
            # ToDo сделать общую функцию для подписки на канал / группу
            await client(JoinChannelRequest(target_usernames))
        except InviteRequestSentError:
            logger.error(f"✉️ Приглашение уже отправлено: {target_usernames}")
    except Exception as e:
        logger.exception(f"❌ Не удалось присоединиться к целевой группе {target_username}: {e}")
        return None


async def process_message(client, message, chat_id: int, user_id, user_language: str = "ru"):
    """
    Обрабатывает входящее сообщение, проверяет совпадение с ключевыми словами
    и отправляет уведомление пользователю в личный чат с ботом.
    """
    if not message.message:
        return

    message_text = message.message
    msg_key = f"{chat_id}-{message.id}"

    if msg_key in forwarded_messages:
        return

    keywords = create_keywords_model(user_id=user_id)

    if not keywords.table_exists():
        keywords.create_table()
        logger.info(f"Создана таблица ключевых слов для пользователя {user_id}")
        return

    keywords = [keyword.user_keyword for keyword in keywords.select() if keyword.user_keyword]
    if not keywords:
        return

    matched_keyword = find_matching_keyword(message_text, keywords)
    if not matched_keyword:
        return

    logger.info(f"📌 Найдено совпадение по ключевому слову '{matched_keyword}'. Отправляю уведомление user_id={user_id}")
    try:
        chat_entity = None
        chat_title = "Неизвестно"
        try:
            chat_entity = await client.get_entity(chat_id)
            chat_title = getattr(chat_entity, "title", None) or getattr(chat_entity, "username", None) or "Неизвестно"
        except Exception as e:
            logger.warning(f"Не удалось получить название чата: {e}")

        if str(chat_id).startswith("-100"):
            clean_chat_id = str(chat_id)[4:]
            topic_id = None
            if message.reply_to:
                topic_id = getattr(message.reply_to, "reply_to_top_id", None) or getattr(
                    message.reply_to, "forum_topic", None
                )
            if topic_id:
                message_link = f"https://t.me/c/{clean_chat_id}/{topic_id}/{message.id}"
            else:
                message_link = f"https://t.me/c/{clean_chat_id}/{message.id}"
        elif chat_entity and getattr(chat_entity, "username", None):
            message_link = f"https://t.me/{chat_entity.username}/{message.id}"
        else:
            message_link = t("message_link_unavailable", lang=user_language)

        chat_username = getattr(chat_entity, "username", None) if chat_entity else None
        username_display = f"@{chat_username}" if chat_username else "—"
        topic_id = None
        if message.reply_to:
            topic_id = getattr(message.reply_to, "reply_to_top_id", None) or getattr(
                message.reply_to, "forum_topic", None
            )
        topic_suffix = f" (топик {topic_id})" if topic_id else ""

        alert_text = t(
            "keyword_match_alert",
            lang=user_language,
            chat_title=f"{chat_title}{topic_suffix}",
            chat_username=username_display,
            message_link=message_link,
            matched_keyword=matched_keyword,
            message_text=html.escape(message.message[:3000]),
        )

        await bot.send_message(
            chat_id=int(user_id),
            text=alert_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
        forwarded_messages.add(msg_key)
    except TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота — уведомление не доставлено")
    except TelegramBadRequest as e:
        logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке уведомления: {e}")


def determine_telegram_chat_type(entity):
    """
    Определяет тип чата в Telegram по сущности.

    Поддерживаемые типы:
    - 'Группа (супергруппа)' — если это мегагруппа
    - 'Канал' — если это канал (broadcast)
    - 'Обычный чат (группа старого типа)' — обычные группы без username

    :param entity: (Channel, Chat) Объект сущности из Telethon.
    :return: str Тип чата как строка.
    """
    if entity.megagroup:
        return 'Группа (супергруппа)'
    elif entity.broadcast:
        return 'Канал'
    else:
        return 'Обычный чат (группа старого типа)'


async def get_grup_accaunt(client):
    """
    Собирает и обновляет данные о группах и каналах из аккаунта пользователя.

    Проходит по всем диалогам, фильтрует супергруппы и каналы, получает полную информацию
    (участники, описание, ссылка), определяет тип чата и сохраняет/обновляет запись в базе данных.

    Пропускает личные чаты и обычные группы без username.
    Добавлена защита от ошибок и ограничений Telegram API.

    :param client: (TelegramClient) Активный клиент Telethon.
    :return: set — множество username (@username), на которые подписан аккаунт
    """
    subscribed_usernames = set()

    try:
        async for dialog in client.iter_dialogs():
            try:
                # Используем entity напрямую — он уже содержит всю нужную информацию
                entity = dialog.entity

                # Пропускаем личные чаты (User)
                if isinstance(entity, types.User):
                    logger.debug(f"💬 Пропущен личный чат: {entity.id}")
                    continue

                # Для списка подписок — любой диалог с @username
                username = getattr(entity, "username", None)
                if username:
                    subscribed_usernames.add(f"@{username.lower()}")

                # В базу — только супергруппы и каналы
                if not getattr(entity, 'megagroup', False) and not getattr(entity, 'broadcast', False):
                    continue

                # Получаем полную информацию через GetFullChannelRequest
                try:
                    full_entity = await client(GetFullChannelRequest(channel=entity))
                    participants_count = full_entity.full_chat.participants_count or 0
                    description = full_entity.full_chat.about or ""
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось получить полные данные для {username or entity.id}: {e}")
                    participants_count = 0
                    description = ""

                actual_username = f"@{username}" if username else ""
                link = f"https://t.me/{username}" if username else None
                title = entity.title or "Без названия"
                new_group_type = determine_telegram_chat_type(entity)

                logger.info(
                    f"👥 {participants_count} | 📝 {title} | Тип: {new_group_type} | 🔗 {link} | 💬 {description}")

                # Сохранение или обновление в базе
                TelegramGroup.insert(
                    group_hash=entity.access_hash,
                    name=title,
                    username=actual_username,
                    description=description,
                    participants=participants_count,
                    group_type=new_group_type,
                    language='',
                    availability='',
                    link=link or "",
                    date_added=datetime.now()
                ).on_conflict(
                    conflict_target=[TelegramGroup.group_hash],
                    update={
                        TelegramGroup.name: title,
                        TelegramGroup.username: actual_username,
                        TelegramGroup.description: description,
                        TelegramGroup.participants: participants_count,
                        TelegramGroup.group_type: new_group_type,
                        TelegramGroup.language: '',
                        TelegramGroup.availability: '',
                        TelegramGroup.link: link or "",
                    }
                ).execute()

                logger.debug(f"🔄 Обновлена группа: {title}")

                await asyncio.sleep(1)
            except Exception as e:
                logger.exception(f"⚠️ Ошибка при обработке диалога {getattr(entity, 'id', 'unknown')}: {e}")
                continue
    except Exception as error:
        logger.exception(f"🔥 Критическая ошибка в get_grup_accaunt: {error}")

    return subscribed_usernames


async def join_required_channels(
    client,
    user_id,
    message,
    subscribed_usernames: set[str],
    subscribed_peer_ids: set[int],
    stop_event=None,
):
    """
    Подписывает аккаунт на каналы из БД, на которые он ещё не подписан.

    Между новыми подписками — пауза 3–10 сек (защита от FloodWait).
    Уже подписанные каналы пропускаются без задержек и уведомлений.
    """
    user = User.get(User.user_id == user_id)
    db_channels, total_count = get_user_channel_usernames(user_id=user_id)
    db_channels = set(db_channels)

    pending, confirmed_via_api = await resolve_pending_subscriptions(
        client, db_channels, subscribed_usernames, subscribed_peer_ids
    )
    matched_in_dialogs = _count_matched_in_dialogs(db_channels, subscribed_usernames, subscribed_peer_ids)

    if total_count == 0:
        await message.answer(t("no_channels_to_track", lang=user.language))
        return

    if pending:
        logger.info(
            f"🔗 Требуется подписка на {len(pending)} чат(ов): "
            f"{', '.join(chat_ref_label(ch) for ch in pending)}"
        )
    else:
        logger.info(
            f"🔗 Все {total_count} каналов доступны аккаунту "
            f"(в диалогах: {matched_in_dialogs}, через API: {confirmed_via_api})"
        )

    if not pending:
        return

    if len(pending) > 500:
        await message.answer(
            t("too_many_channels", lang=user.language, total=len(pending), limit=500)
        )
        pending = pending[:500]

    stats = {"joined": 0, "already": 0, "error": 0}
    for channel in pending:
        if stop_event and stop_event.is_set():
            logger.info(f"🛑 Подписка прервана пользователем {user_id}")
            return

        try:
            result = await subscription_telegram(client=client, target_username=channel)
            stats[result] = stats.get(result, 0) + 1

            if result == "joined":
                delay = random.randint(3, 10)
                await message.answer(
                    t("channel_subscribed", lang=user.language, channel=channel, delay=delay)
                )
                if await _sleep_with_stop(delay, stop_event):
                    logger.info(f"🛑 Подписка прервана во время паузы для user_id={user_id}")
                    return
        except Exception as e:
            stats["error"] += 1
            logger.exception("tracking_error", error=e)

    logger.info(
        f"📊 Итог проверки подписок: новых {stats['joined']}, "
        f"уже подписаны {stats['already']}, ошибок {stats['error']}"
    )


async def ensure_joined_target_group(client, message, user_id: int):
    """
    Обеспечивает подключение клиента Telethon к целевой группе пользователя.

    Обёртка вокруг `join_target_group`, которая проверяет успешность подключения и при необходимости отправляет
    пользователю сообщение об ошибке.

    - Если подключение не удалось, функция возвращает None (клиент НЕ отключается).
    - Используется для упрощения логики в функции `filter_messages`.

    :param client: (TelegramClient) Активный клиент для выполнения запросов.
    :param message: (Message) Объект сообщения aiogram для отправки уведомления об ошибке.
    :param user_id: (int) Уникальный идентификатор пользователя Telegram.
    :return: int or None: Идентификатор целевой группы (entity.id) при успехе, иначе None.
    """
    user = User.get(User.user_id == user_id)
    logger.info("Подключаемся к целевой группе для пересылки")
    target_group_id = await join_target_group(client=client, user_id=user_id, message=message)

    if not target_group_id:
        text_error = t("target_group_join_error", lang=user.language)
        logger.error(text_error)
        await message.answer(
            text=text_error,
            reply_markup=connect_grup_keyboard_tech()
        )
        # НЕ отключаем клиент здесь — это будет сделано в finally блоке filter_messages
        return None

    return target_group_id


async def get_user_channels_or_notify(user_id: int, user, message, client):
    channels = [group.username for group in Groups.select().where(Groups.user_id == user_id)]

    if not channels:
        logger.warning(f"⚠️ Список каналов пуст для пользователя {user_id}.")
        await client.disconnect()
        await abort_tracking(
            user_id, user, message,
            notify=t("tracking_launch_error", lang=user.language),
        )
        return None

    return channels


async def filter_messages(message, user_id, user, stop_event: asyncio.Event):
    """
    Основная функция запуска процесса отслеживания сообщений в Telegram.

    1️⃣ Читает каналы из БД — мгновенно, без запросов к Telegram.
    2️⃣ Параллельно запускает:
        - прослушивание новых сообщений (сразу)
        - подписку на целевую группу и новые каналы (в фоне)

    :param message: (Message) Объект сообщения aiogram для взаимодействия с пользователем.
    :param user_id: (int) Идентификатор пользователя Telegram.
    :param user: (User) Модель пользователя из базы данных (для языка и данных).
    :return: None
    :raises Exception: Логируется при ошибках инициализации или подключения.
    """
    logger.info(f"🚀 Запуск бота для user_id={str(user_id)}...")
    client = None
    try:
        # === Проверка аккаунтов ===
        # Проверка на наличие подключенного аккаунта у пользователя для избежания ошибки
        # Получаем все аккаунты пользователя из его персональной таблицы
        accounts = get_user_accounts(user_id)
        if not accounts:
            logger.warning(f"⚠️ У пользователя {user_id} нет подключённых аккаунтов в БД")
            await abort_tracking(user_id, user, message, notify=t("no_accounts", lang=user.language))
            return None
        logger.info(f"📦 Найдено {len(accounts)} аккаунтов в БД для пользователя {user_id}")

        # === Подключаем клиент ===
        checker = CheckingAccountsValidity(message=message, user_id=user_id)  # ✅ Сохраняем активный клиент
        client = await checker.client_connect_string_session(accounts[0]['session_string'])
        active_clients[str(user_id)] = client

        already_subscribed_usernames, subscribed_peer_ids = await get_subscribed_refs(client)

        # === 1️⃣ Читаем каналы из БД — быстро, без запросов к Telegram ===
        channels = await get_user_channels_or_notify(user_id=int(user_id), user=user, message=message, client=client)
        if not channels:
            return

        canonical_refs = _canonical_chat_refs(channels)
        _log_tracking_channels(user_id, canonical_refs)
        monitored_targets = await resolve_tracking_targets(client, canonical_refs)
        if not monitored_targets:
            await abort_tracking(
                user_id,
                user,
                message,
                notify=t("tracking_launch_error", lang=user.language),
            )
            return
        monitored_chats = await _expand_with_discussion_chats(client, monitored_targets)

        async def listen():
            @client.on(events.NewMessage(chats=monitored_chats))
            async def handle_new_message(event: events.NewMessage.Event):
                try:
                    await process_message(
                        client=client,
                        message=event.message,
                        chat_id=event.chat_id,
                        user_id=str(user_id),
                        user_language=user.language,
                    )
                except Exception as e:
                    logger.exception(f"Не удалось обработать сообщение: {e}")

            logger.info(
                f"👂 Слушаю новые сообщения в {len(monitored_chats)} чатах "
                f"(из списка: {len(canonical_refs)}, user_id={user_id})"
            )
            await message.answer(text=t("bot_listening", lang=user.language))

            await stop_event.wait()

            logger.info(f"🛑 Прослушивание остановлено для user_id={user_id}")
            await message.answer(
                t("tracking_stopped", lang=user.language),
                reply_markup=_main_keyboard(user, user_id, tracking_active=False),
            )

        # === Функция подписки — работает параллельно в фоне ===
        async def subscribe():
            try:
                await join_required_channels(
                    client=client,
                    user_id=str(user_id),
                    message=message,
                    subscribed_usernames=already_subscribed_usernames,
                    subscribed_peer_ids=subscribed_peer_ids,
                    stop_event=stop_event,
                )
            except asyncio.CancelledError:
                logger.info(f"🛑 Фоновая подписка отменена для user_id={user_id}")
                raise

        listen_task = asyncio.create_task(listen())
        subscribe_task = asyncio.create_task(subscribe())
        await listen_task
        if not subscribe_task.done():
            subscribe_task.cancel()
            try:
                await subscribe_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка в filter_messages: {e}")
        try:
            await message.answer(
                t("tracking_launch_error", lang=user.language),
                reply_markup=_main_keyboard(user, user_id, tracking_active=True),
            )
        except Exception as notify_err:
            logger.exception(f"Не удалось уведомить пользователя об ошибке: {notify_err}")
    finally:
        user_id_str = str(user_id)
        if user_id_str in active_clients:
            client = active_clients.pop(user_id_str)
            if client.is_connected():
                await client.disconnect()
                logger.info(f"🛑 Клиент для user_id={user_id_str} отключён.")
        if user_id_str in stop_flags:
            stop_flags.pop(user_id_str)
            logger.info(f"🗑️ Флаг остановки для user_id={user_id_str} удалён.")


async def stop_tracking(user_id, message):
    """
    Останавливает процесс отслеживания сообщений для пользователя.

    Устанавливает флаг остановки для активной сессии пользователя, что приводит к
    завершению цикла прослушивания в функции `filter_messages`.

    - Не создаёт новое подключение к сессии (избегает блокировки SQLite).
    - Использует глобальный словарь `stop_flags` для управления состоянием.
    - Безопасно обрабатывает случаи, когда отслеживание уже остановлено.

    :param user_id: (int) Идентификатор пользователя Telegram.
    :param message: (Message) Объект сообщения aiogram для отправки подтверждения.
    """
    user = User.get(User.user_id == user_id)
    user_id_str = str(user_id)

    logger.info("Запрос на остановку отслеживания", user_id=user_id_str)

    marked = await tracking_store.is_marked(user_id)
    running = user_id_str in stop_flags

    if not marked and not running:
        logger.warning("Отслеживание не активно или уже остановлено", user_id=user_id_str)
        await message.answer(
            t("tracking_not_active", lang=user.language),
            reply_markup=_main_keyboard(user, user_id, tracking_active=False),
        )
        return

    await tracking_store.unmark_active(user_id)

    if running:
        stop_event = stop_flags[user_id_str]
        stop_event.set()
        logger.info("Флаг остановки установлен", user_id=user_id_str)
        await message.answer(
            t("tracking_stop_requested", lang=user.language),
            reply_markup=_main_keyboard(user, user_id, tracking_active=False),
        )
        return

    logger.info("Отслеживание снято из Redis (процесс не был запущен)", user_id=user_id_str)
    await message.answer(
        t("tracking_stopped", lang=user.language),
        reply_markup=_main_keyboard(user, user_id, tracking_active=False),
    )
