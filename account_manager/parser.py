import asyncio
import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import structlog

logger = structlog.get_logger(__name__)
from telethon import events, types
from telethon.errors import (
    FloodWaitError,
    InviteRequestSentError,
    AuthKeyUnregisteredError,
    AuthKeyDuplicatedError,
    AuthKeyNotFound,
    PhoneNumberBannedError,
    UserDeactivatedBanError,
)
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import Channel, Chat, User as TlUser

from account_manager.auth import CheckingAccountsValidity
from account_manager.chat_targets import (
    get_subscribed_refs,
    is_member_of_ref,
    resolve_tracking_targets,
)
from account_manager.subscription import subscription_telegram
from core.telegram_utils import chat_ref_label, normalize_telegram_chat_ref, normalize_telegram_username
from core.keyword_match import MatchDetail, find_matching_keyword_detail
from core.chat_filter import chat_type_allowed, classify_chat_entity
from core.author_kind import author_kind_allowed, classify_author_kind
from core.stopwords import find_stopword
from database.database import (
    create_keywords_model, TelegramGroup, get_active_account, get_user_channel_usernames,
    User, lead_exists, save_lead, get_user_match_mode, is_user_in_quiet_hours,
    get_user_digest_settings, get_user_chat_filter, get_user_stopwords,
    get_user_alert_template, get_failover_account, set_active_account,
    get_user_author_filter,
)
from keyboards.user.keyboards import alert_actions_keyboard, resolve_main_keyboard
from locales.locales import t
from system.dispatcher import bot
from core.config import ADMIN_USER_IDS, TIMEZONE
from core import tracking_store
from core.alert_dedup import claim_alert
from core.alert_delivery import deliver_alert
from core.alert_template import alert_template_ftl_key
from core.channel_mute import is_channel_muted
from core.digest import digest_worker, enqueue_digest_item, flush_digest

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
    from core.metrics import mark_tracking_started

    user_id_str = str(user_id)
    async with _user_lock(user_id):
        if user_id_str in stop_flags:
            return None
        stop_event = asyncio.Event()
        stop_flags[user_id_str] = stop_event
        await tracking_store.mark_active(user_id)
        mark_tracking_started(user_id)
        return stop_event


async def abort_tracking(user_id, user, message, *, notify: str | None = None):
    """Снимает флаг отслеживания и возвращает клавиатуру «Запуск»."""
    from core.metrics import clear_tracking_started

    await tracking_store.unmark_active(user_id)
    stop_flags.pop(str(user_id), None)
    clear_tracking_started(user_id)
    if notify:
        await message.answer(notify, reply_markup=_main_keyboard(user, user_id, tracking_active=False))


def _main_keyboard(user, user_id, *, tracking_active: bool | None = None):
    if tracking_active is None:
        tracking_active = is_tracking_active(user_id)
    return resolve_main_keyboard(
        user.language,
        tracking_active=tracking_active,
        user_id=int(user_id),
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


# FloodWait дольше этого — пробуем другой аккаунт вместо долгого ожидания
_FAILOVER_FLOOD_SECONDS = 300

_AUTH_ERRORS = (
    AuthKeyUnregisteredError,
    AuthKeyDuplicatedError,
    AuthKeyNotFound,
    PhoneNumberBannedError,
    UserDeactivatedBanError,
)


async def _safe_disconnect(client) -> None:
    try:
        if client and client.is_connected():
            await client.disconnect()
    except Exception as e:
        logger.debug("telethon_disconnect_error", error=str(e))


async def _reconnect_telethon_client(
    client,
    stop_event: asyncio.Event,
    *,
    user_id,
    initial_delay: int = 5,
    max_delay: int = 300,
) -> str:
    """
    Переподключает Telethon после обрыва.
    Возвращает: ok | stopped | auth_dead | flood_long
    """
    from core.metrics import record_floodwait

    delay = initial_delay
    attempt = 0
    while not stop_event.is_set():
        attempt += 1
        await _safe_disconnect(client)
        logger.info(
            "telethon_reconnect_attempt",
            user_id=user_id,
            attempt=attempt,
            delay=delay,
        )
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("telethon_session_invalid", user_id=user_id)
                return "auth_dead"
            me = await client.get_me()
            logger.info(
                "telethon_reconnected",
                user_id=user_id,
                attempt=attempt,
                account_id=getattr(me, "id", None),
            )
            return "ok"
        except FloodWaitError as e:
            try:
                await record_floodwait()
            except Exception:
                pass
            logger.warning(
                "telethon_reconnect_floodwait",
                user_id=user_id,
                seconds=e.seconds,
            )
            if e.seconds >= _FAILOVER_FLOOD_SECONDS:
                return "flood_long"
            wait_s = min(int(e.seconds) + 1, max_delay)
            if await _sleep_with_stop(wait_s, stop_event):
                return "stopped"
            continue
        except _AUTH_ERRORS as e:
            logger.error(
                "telethon_reconnect_auth_dead",
                user_id=user_id,
                error=str(e),
            )
            return "auth_dead"
        except Exception as e:
            logger.warning(
                "telethon_reconnect_failed",
                user_id=user_id,
                attempt=attempt,
                error=str(e),
            )
        if await _sleep_with_stop(delay, stop_event):
            return "stopped"
        delay = min(delay * 2, max_delay)
    return "stopped"


async def _connect_tracking_account(message, user_id, account: dict):
    """Подключает Telethon-клиент для tracking по записи аккаунта."""
    checker = CheckingAccountsValidity(message=message, user_id=user_id)
    return await checker.client_connect_string_session(
        account["session_string"],
        for_tracking=True,
    )


async def _try_failover_client(
    *,
    user_id,
    user,
    message,
    old_client,
    exclude_ids: set[int],
) -> tuple[object | None, dict | None]:
    """
    Переключает активного на другой аккаунт и подключает клиент.
    exclude_ids пополняется неудачными/старыми id.
    """
    await _safe_disconnect(old_client)
    active = get_active_account(user_id)
    if active and active.get("id") is not None:
        exclude_ids.add(int(active["id"]))

    while True:
        candidate = get_failover_account(user_id, exclude_ids)
        if not candidate:
            return None, None
        acc_id = int(candidate["id"])
        exclude_ids.add(acc_id)
        phone = (candidate.get("phone_number") or "?").strip() or "?"
        logger.info(
            "telethon_failover_try",
            user_id=user_id,
            account_id=acc_id,
            phone=phone,
        )
        if not set_active_account(user_id, acc_id):
            continue
        new_client = await _connect_tracking_account(message, user_id, candidate)
        if not new_client:
            logger.warning(
                "telethon_failover_connect_failed",
                user_id=user_id,
                account_id=acc_id,
            )
            continue
        active_clients[str(user_id)] = new_client
        from_phone = (active or {}).get("phone_number") or "?"
        try:
            await message.answer(
                t(
                    "tracking_failover_ok",
                    lang=user.language,
                    from_phone=from_phone,
                    to_phone=phone,
                )
            )
        except Exception:
            pass
        logger.info(
            "telethon_failover_ok",
            user_id=user_id,
            from_phone=from_phone,
            to_phone=phone,
        )
        return new_client, candidate


async def _listen_with_reconnect(
    client,
    stop_event: asyncio.Event,
    *,
    user_id,
    user,
    message,
    monitored_chats: list,
):
    """Слушает NewMessage; при обрыве — reconnect; при auth/долгом flood — failover."""

    exclude_ids: set[int] = set()
    active = get_active_account(user_id)
    if active and active.get("id") is not None:
        exclude_ids.add(int(active["id"]))

    def _attach_handler(c) -> None:
        @c.on(events.NewMessage(chats=monitored_chats))
        async def handle_new_message(event: events.NewMessage.Event):
            try:
                await process_message(
                    client=c,
                    message=event.message,
                    chat_id=event.chat_id,
                    user_id=str(user_id),
                    user_language=user.language,
                )
            except Exception as e:
                logger.exception(f"Не удалось обработать сообщение: {e}")

    current = client
    _attach_handler(current)

    logger.info(
        f"👂 Слушаю новые сообщения в {len(monitored_chats)} чатах "
        f"(из списка, user_id={user_id})"
    )
    await message.answer(text=t("bot_listening", lang=user.language))

    async def _recover_or_failover() -> bool:
        """True — продолжаем слушать; False — выходим из цикла."""
        nonlocal current
        status = await _reconnect_telethon_client(
            current, stop_event, user_id=user_id
        )
        if status == "ok":
            try:
                await message.answer(t("tracking_reconnected", lang=user.language))
            except Exception:
                pass
            return True
        if status == "stopped" or stop_event.is_set():
            return False
        # auth_dead / flood_long — пробуем другой аккаунт
        new_client, _acc = await _try_failover_client(
            user_id=user_id,
            user=user,
            message=message,
            old_client=current,
            exclude_ids=exclude_ids,
        )
        if not new_client:
            return False
        current = new_client
        _attach_handler(current)
        return True

    while not stop_event.is_set():
        if not current.is_connected():
            logger.warning("telethon_not_connected", user_id=user_id)
            if not await _recover_or_failover():
                break
            continue

        run_task = asyncio.create_task(current.run_until_disconnected())
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait(
            {run_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if stop_event.is_set():
            break

        err = None
        if run_task in done:
            try:
                run_task.result()
            except Exception as e:
                err = e
        logger.warning(
            "telethon_connection_lost",
            user_id=user_id,
            error=str(err) if err else None,
        )
        if not await _recover_or_failover():
            break

    if stop_event.is_set():
        logger.info(f"🛑 Прослушивание остановлено для user_id={user_id}")
        try:
            await message.answer(
                t("tracking_stopped", lang=user.language),
                reply_markup=_main_keyboard(user, user_id, tracking_active=False),
            )
        except Exception:
            pass
    else:
        logger.error("telethon_reconnect_gave_up", user_id=user_id)
        await tracking_store.unmark_active(user_id)
        try:
            await message.answer(
                t("tracking_failover_failed", lang=user.language),
                reply_markup=_main_keyboard(user, user_id, tracking_active=False),
            )
        except Exception:
            pass
        stop_event.set()


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


async def _resolve_message_author(message, client, lang: str) -> tuple[str, dict]:
    """
    Автор для алерта + поля для БД.
    Возвращает (display_html, {author_tg_id, author_username, author_name, author_kind}).
    """
    meta = {
        "author_tg_id": None,
        "author_username": None,
        "author_name": None,
        "author_kind": "anonymous",
    }

    try:
        sender = await message.get_sender()
    except Exception as e:
        logger.debug("get_sender_failed", error=str(e))
        sender = None

    meta["author_kind"] = classify_author_kind(sender, message)

    if isinstance(sender, TlUser):
        name = " ".join(
            part for part in (getattr(sender, "first_name", None), getattr(sender, "last_name", None)) if part
        ).strip()
        meta["author_tg_id"] = getattr(sender, "id", None)
        meta["author_username"] = getattr(sender, "username", None)
        meta["author_name"] = name or None
    elif isinstance(sender, (Channel, Chat)):
        meta["author_tg_id"] = getattr(sender, "id", None)
        meta["author_username"] = getattr(sender, "username", None)
        meta["author_name"] = getattr(sender, "title", None)

    formatted = _format_sender_entity(sender, lang)
    if formatted:
        return formatted, meta

    post_author = getattr(message, "post_author", None)
    if post_author:
        if not meta["author_name"]:
            meta["author_name"] = str(post_author).strip()
        return t("alert_author_signed", lang=lang, name=html.escape(str(post_author).strip())), meta

    fwd = getattr(message, "fwd_from", None)
    if fwd is not None:
        fwd_label = await _format_forward_author(message, client, fwd, lang)
        if fwd_label:
            if getattr(fwd, "from_name", None) and not meta["author_name"]:
                meta["author_name"] = str(fwd.from_name).strip()
            return fwd_label, meta

    from_id = getattr(message, "from_id", None)
    if from_id is not None and hasattr(from_id, "user_id"):
        meta["author_tg_id"] = from_id.user_id
        if meta["author_kind"] == "anonymous":
            meta["author_kind"] = "user"
        return t("alert_author_id_only", lang=lang, id=from_id.user_id), meta

    return t("alert_author_unknown", lang=lang), meta


def _format_sender_entity(sender, lang: str) -> str | None:
    if sender is None:
        return None

    if isinstance(sender, TlUser):
        name = " ".join(
            part for part in (getattr(sender, "first_name", None), getattr(sender, "last_name", None)) if part
        ).strip()
        bits: list[str] = []
        if name:
            bits.append(html.escape(name))
        username = getattr(sender, "username", None)
        if username:
            bits.append(f"(@{html.escape(username)})")
        user_id = getattr(sender, "id", None)
        if user_id:
            bits.append(t("alert_author_id", lang=lang, id=user_id))
        return " ".join(bits) if bits else None

    if isinstance(sender, (Channel, Chat)):
        title = getattr(sender, "title", None) or getattr(sender, "username", None) or "—"
        bits = [html.escape(str(title))]
        username = getattr(sender, "username", None)
        if username:
            bits.append(f"(@{html.escape(username)})")
        entity_id = getattr(sender, "id", None)
        if entity_id:
            bits.append(t("alert_author_id", lang=lang, id=entity_id))
        kind = t("alert_author_channel", lang=lang) if isinstance(sender, Channel) and getattr(sender, "broadcast", False) else ""
        label = " ".join(bits)
        return f"{label} ({kind})" if kind else label

    return None


async def _format_forward_author(message, client, fwd, lang: str) -> str | None:
    """Подпись для пересланных сообщений."""
    try:
        if getattr(fwd, "from_name", None):
            return t(
                "alert_author_forward",
                lang=lang,
                name=html.escape(str(fwd.from_name).strip()),
            )
        # from_id → попробуем entity
        from_id = getattr(fwd, "from_id", None)
        if from_id is not None:
            try:
                entity = await client.get_entity(from_id)
                formatted = _format_sender_entity(entity, lang)
                if formatted:
                    return t("alert_author_forward_entity", lang=lang, author=formatted)
            except Exception:
                if hasattr(from_id, "user_id"):
                    return t("alert_author_forward_id", lang=lang, id=from_id.user_id)
                if hasattr(from_id, "channel_id"):
                    return t("alert_author_forward_id", lang=lang, id=from_id.channel_id)
    except Exception as e:
        logger.debug("forward_author_failed", error=str(e))
    return None


def _resolve_app_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        logger.warning("invalid_timezone_fallback_utc", timezone=TIMEZONE)
        return ZoneInfo("UTC")


def _format_alert_time(message, lang: str) -> str:
    """Дата/время сообщения в TIMEZONE из конфига."""
    dt = getattr(message, "date", None)
    if not isinstance(dt, datetime):
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_resolve_app_timezone())
    stamp = local.strftime("%d.%m.%Y %H:%M")
    tz_name = local.tzname() or TIMEZONE
    return t("alert_time_value", lang=lang, datetime=stamp, tz=tz_name)


def _chat_type_label(entity, lang: str) -> str | None:
    if entity is None:
        return None
    if isinstance(entity, Channel):
        if getattr(entity, "broadcast", False):
            return t("alert_chat_type_channel", lang=lang)
        if getattr(entity, "megagroup", False):
            return t("alert_chat_type_supergroup", lang=lang)
        return t("alert_chat_type_channel", lang=lang)
    if isinstance(entity, Chat):
        return t("alert_chat_type_group", lang=lang)
    if isinstance(entity, TlUser):
        return t("alert_chat_type_user", lang=lang)
    return None


def _format_source_title(chat_title: str, entity, lang: str, topic_suffix: str = "") -> str:
    base = f"{chat_title}{topic_suffix}".strip() or "—"
    kind = _chat_type_label(entity, lang)
    if kind:
        return f"{base} ({kind})"
    return base


def _format_chat_line(entity, chat_id: int, lang: str) -> str:
    """
    Строка «Чат»: @username / id … либо только id + тип, если username нет.
    """
    username = getattr(entity, "username", None) if entity else None
    chat_id_str = str(chat_id)
    if username:
        return f"@{username} / id {chat_id_str}"

    kind = _chat_type_label(entity, lang)
    if kind:
        return t("alert_chat_id_typed", lang=lang, chat_id=chat_id_str, chat_type=kind)
    return t("alert_chat_id_only", lang=lang, chat_id=chat_id_str)


def _format_match_why(detail: MatchDetail, lang: str) -> str:
    """Человекочитаемая причина срабатывания для алерта."""
    mode_name = t(f"match_mode_{detail.mode}_name", lang=lang)
    tokens = ", ".join(detail.hit_tokens) if detail.hit_tokens else detail.keyword
    if detail.reason == "exact":
        return t("alert_why_exact", lang=lang, mode=mode_name)
    if detail.reason == "loose":
        return t(
            "alert_why_loose",
            lang=lang,
            mode=mode_name,
            tokens=tokens,
        )
    return t("alert_why_tokens", lang=lang, mode=mode_name, tokens=tokens)


async def process_message(client, message, chat_id: int, user_id, user_language: str = "ru"):
    """
    Обрабатывает входящее сообщение, проверяет совпадение с ключевыми словами
    и отправляет уведомление пользователю в личный чат с ботом.
    """
    if not message.message:
        return

    if await is_channel_muted(user_id, int(chat_id)):
        return

    message_text = message.message

    keywords = create_keywords_model(user_id=user_id)

    if not keywords.table_exists():
        keywords.create_table()
        logger.info(f"Создана таблица ключевых слов для пользователя {user_id}")
        return

    keywords = [keyword.user_keyword for keyword in keywords.select() if keyword.user_keyword]
    if not keywords:
        return

    match_mode = get_user_match_mode(int(user_id))
    match_detail = find_matching_keyword_detail(
        message_text,
        keywords,
        mode=match_mode,
    )
    if not match_detail:
        return
    matched_keyword = match_detail.keyword

    stopwords = get_user_stopwords(int(user_id))
    hit = find_stopword(message_text, stopwords)
    if hit:
        logger.info(
            "stopword_skip",
            user_id=user_id,
            chat_id=chat_id,
            stopword=hit,
            matched_keyword=matched_keyword,
        )
        return

    chat_entity = None
    chat_title = "Неизвестно"
    try:
        chat_entity = await client.get_entity(chat_id)
        chat_title = (
            getattr(chat_entity, "title", None)
            or getattr(chat_entity, "username", None)
            or "Неизвестно"
        )
    except Exception as e:
        logger.warning(f"Не удалось получить название чата: {e}")

    chat_kind = classify_chat_entity(chat_entity)
    chat_filter = get_user_chat_filter(int(user_id))
    if not chat_type_allowed(chat_filter, chat_kind):
        logger.debug(
            "chat_filter_skip",
            user_id=user_id,
            chat_id=chat_id,
            chat_kind=chat_kind,
            chat_filter=chat_filter,
        )
        return

    # Дедуп после матча: Redis (TTL) + lead в БД — переживает рестарт
    if lead_exists(int(user_id), int(chat_id), int(message.id)):
        return
    if not await claim_alert(user_id, int(chat_id), int(message.id)):
        return

    match_why = _format_match_why(match_detail, user_language)
    logger.info(
        "keyword_match",
        user_id=user_id,
        keyword=matched_keyword,
        mode=match_detail.mode,
        reason=match_detail.reason,
        hit_tokens=list(match_detail.hit_tokens),
        miss_tokens=list(match_detail.miss_tokens),
    )
    try:
        from core.metrics import record_match

        await record_match()
    except Exception:
        pass
    try:
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
        topic_id = None
        if message.reply_to:
            topic_id = getattr(message.reply_to, "reply_to_top_id", None) or getattr(
                message.reply_to, "forum_topic", None
            )
        topic_suffix = f" (топик {topic_id})" if topic_id else ""

        source_title = _format_source_title(chat_title, chat_entity, user_language, topic_suffix)
        chat_line = _format_chat_line(chat_entity, int(chat_id), user_language)
        message_time = _format_alert_time(message, user_language)

        author_display, author_meta = await _resolve_message_author(message, client, user_language)
        author_kind = author_meta.get("author_kind") or "anonymous"
        author_filter = get_user_author_filter(int(user_id))
        if not author_kind_allowed(author_filter, author_kind):
            logger.info(
                "author_filter_skip",
                user_id=user_id,
                chat_id=chat_id,
                message_id=getattr(message, "id", None),
                author_kind=author_kind,
                author_filter=author_filter,
                keyword=matched_keyword,
            )
            return

        try:
            save_lead(
                owner_user_id=int(user_id),
                chat_id=int(chat_id),
                message_id=int(message.id),
                message_text=message_text,
                matched_keyword=matched_keyword,
                chat_title=f"{chat_title}{topic_suffix}",
                chat_username=chat_username,
                message_link=message_link if message_link.startswith("http") else None,
                author_tg_id=author_meta.get("author_tg_id"),
                author_username=author_meta.get("author_username"),
                author_name=author_meta.get("author_name"),
                author_kind=author_kind,
            )
        except Exception as e:
            logger.exception("lead_save_unexpected", error=e)

        if is_user_in_quiet_hours(int(user_id)):
            logger.info(
                "quiet_hours_skip_alert",
                user_id=user_id,
                chat_id=chat_id,
                message_id=getattr(message, "id", None),
            )
            return

        digest = get_user_digest_settings(int(user_id))
        if digest["enabled"]:
            preview = (message.message or "")[:160].replace("\n", " ")
            await enqueue_digest_item(
                user_id,
                {
                    "keyword": matched_keyword,
                    "chat_title": source_title,
                    "chat_line": chat_line,
                    "author": author_meta.get("author_name")
                    or author_meta.get("author_username")
                    or "",
                    "link": message_link if str(message_link).startswith("http") else "",
                    "preview": preview,
                    "time": message_time,
                },
            )
            # срочный flush, если буфер переполнен
            await flush_digest(user_id, user_language)
            logger.info("digest_enqueued", user_id=user_id, keyword=matched_keyword)
            return

        alert_ftl = alert_template_ftl_key(get_user_alert_template(user_id))
        alert_text = t(
            alert_ftl,
            lang=user_language,
            chat_title=html.escape(source_title),
            chat_username=html.escape(chat_line),
            author=author_display,
            message_time=html.escape(message_time),
            message_link=message_link,
            matched_keyword=html.escape(matched_keyword),
            match_why=html.escape(match_why),
            message_text=html.escape(message.message[:3000]),
        )

        await deliver_alert(
            int(user_id),
            text=alert_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=alert_actions_keyboard(
                user_language,
                url=message_link if str(message_link).startswith("http") else None,
                chat_id=int(chat_id),
            ),
        )
        logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
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

    Паузы и лимиты — account_manager.join_throttle (антибан).
    Уже подписанные каналы пропускаются без задержек.
    """
    from account_manager.join_throttle import (
        apply_batch_cap,
        join_channels_safely,
        remaining_daily_joins,
        should_notify_join,
    )
    from core.config import JOIN_BATCH_LIMIT, JOIN_DAILY_LIMIT

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

    pending_list = list(pending)
    capped, original_len = apply_batch_cap(pending_list)
    if original_len > len(capped):
        await message.answer(
            t(
                "too_many_channels",
                lang=user.language,
                total=original_len,
                limit=JOIN_BATCH_LIMIT,
            ),
            parse_mode="HTML",
        )

    daily_left = await remaining_daily_joins(user_id)
    if daily_left <= 0:
        await message.answer(
            t("join_daily_limit", lang=user.language, limit=JOIN_DAILY_LIMIT),
            parse_mode="HTML",
        )
        return

    async def _on_progress(stats, channel, result, delay):
        if result == "joined" and should_notify_join(stats.joined):
            await message.answer(
                t(
                    "channel_subscribed",
                    lang=user.language,
                    channel=html.escape(channel),
                    delay=delay,
                ),
                parse_mode="HTML",
            )

    batch = await join_channels_safely(
        client=client,
        channels=capped,
        user_id=user_id,
        stop_event=stop_event,
        on_progress=_on_progress,
    )

    if batch.stopped:
        logger.info(f"🛑 Подписка прервана пользователем {user_id}")

    await message.answer(
        t(
            "join_batch_summary",
            lang=user.language,
            joined=batch.joined,
            already=batch.already,
            errors=batch.error,
            skipped=batch.skipped_limit,
        ),
        parse_mode="HTML",
    )

    logger.info(
        f"📊 Итог проверки подписок: новых {batch.joined}, "
        f"уже подписаны {batch.already}, ошибок {batch.error}, "
        f"пропущено лимитом {batch.skipped_limit}"
    )


async def get_user_channels_or_notify(user_id: int, user, message, client):
    channels, _ = get_user_channel_usernames(user_id=user_id, only_enabled=True)

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
        # === Проверка активного аккаунта ===
        account = get_active_account(user_id)
        if not account:
            logger.warning(f"⚠️ У пользователя {user_id} нет подключённых аккаунтов в БД")
            await abort_tracking(user_id, user, message, notify=t("no_accounts", lang=user.language))
            return None
        logger.info(f"📦 Активный аккаунт пользователя {user_id}: {account.get('phone_number')}")

        # === Подключаем клиент (с failover на другие аккаунты) ===
        client = await _connect_tracking_account(message, user_id, account)
        if not client:
            exclude_ids: set[int] = set()
            if account.get("id") is not None:
                exclude_ids.add(int(account["id"]))
            client, new_acc = await _try_failover_client(
                user_id=user_id,
                user=user,
                message=message,
                old_client=None,
                exclude_ids=exclude_ids,
            )
            if not client:
                logger.error("telethon_connect_failed", user_id=user_id)
                await abort_tracking(
                    user_id,
                    user,
                    message,
                    notify=t("search_client_error", lang=user.language),
                )
                return None
            account = new_acc or get_active_account(user_id) or account
        active_clients[str(user_id)] = client

        already_subscribed_usernames, subscribed_peer_ids = await get_subscribed_refs(client)

        # === 1️⃣ Читаем каналы из БД — быстро, без запросов к Telegram ===
        channels = await get_user_channels_or_notify(user_id=int(user_id), user=user, message=message, client=client)
        if not channels:
            return

        canonical_refs = _canonical_chat_refs(channels)
        _log_tracking_channels(user_id, canonical_refs)

        # Предупреждение: на что аккаунт ещё не подписан (подписка пойдёт в фоне)
        try:
            from account_manager.chat_targets import check_channels_membership
            from core.telegram_utils import chat_ref_label

            membership = await check_channels_membership(
                client, canonical_refs, delay_sec=0.05
            )
            missing = membership["missing"]
            if missing:
                preview = ", ".join(chat_ref_label(x) for x in missing[:8])
                if len(missing) > 8:
                    preview += f" …+{len(missing) - 8}"
                await message.answer(
                    t(
                        "tracking_not_subscribed_warn",
                        lang=user.language,
                        count=len(missing),
                        preview=html.escape(preview),
                    ),
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.warning("membership_precheck_failed", user_id=user_id, error=str(e))

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
            await _listen_with_reconnect(
                client,
                stop_event,
                user_id=user_id,
                user=user,
                message=message,
                monitored_chats=monitored_chats,
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
        digest_task = asyncio.create_task(
            digest_worker(user_id, user.language, stop_event)
        )
        await listen_task
        if not subscribe_task.done():
            subscribe_task.cancel()
            try:
                await subscribe_task
            except asyncio.CancelledError:
                pass
        try:
            await asyncio.wait_for(digest_task, timeout=10)
        except asyncio.TimeoutError:
            digest_task.cancel()
            try:
                await digest_task
            except asyncio.CancelledError:
                pass
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
        from core.metrics import clear_tracking_started

        user_id_str = str(user_id)
        if user_id_str in active_clients:
            client = active_clients.pop(user_id_str)
            await _safe_disconnect(client)
            logger.info(f"🛑 Клиент для user_id={user_id_str} отключён.")
        if user_id_str in stop_flags:
            stop_flags.pop(user_id_str)
            logger.info(f"🗑️ Флаг остановки для user_id={user_id_str} удалён.")
        clear_tracking_started(user_id)


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
        # Разблокируем run_until_disconnected
        client = active_clients.get(user_id_str)
        if client:
            await _safe_disconnect(client)
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
