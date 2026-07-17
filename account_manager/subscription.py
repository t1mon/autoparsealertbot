import asyncio

import structlog

logger = structlog.get_logger(__name__)
from telethon.errors import (
    AuthKeyUnregisteredError,
    ChannelPrivateError,
    FloodWaitError,
    InviteRequestSentError,
    UserAlreadyParticipantError,
)

from account_manager.chat_targets import join_chat_ref
from account_manager.join_result import JoinResult
from core.membership_status import (
    MEMBERSHIP_OK,
    REASON_INVALID_REF,
    REASON_PENDING_APPROVAL,
    REASON_PRIVATE,
    REASON_UNKNOWN,
    reason_to_status,
)
from core.telegram_utils import normalize_telegram_chat_ref, normalize_telegram_username
from database.database import set_group_membership_by_ref


async def subscription_telegram(client, target_username, *, user_id: int | None = None) -> JoinResult:
    """
    Подписка на группу/канал Telegram.
    """
    normalized = normalize_telegram_chat_ref(target_username) or normalize_telegram_username(target_username)
    if not normalized:
        logger.error(f"❌ Неверная ссылка на чат: {target_username}")
        result = JoinResult("error", REASON_INVALID_REF)
        if user_id is not None:
            set_group_membership_by_ref(user_id, target_username, reason_to_status(REASON_INVALID_REF))
        return result

    try:
        result = await join_chat_ref(client, normalized)
        if result.outcome == "joined":
            logger.info(f"✅ Подписались на {normalized}")
        elif result.outcome == "already":
            logger.info(f"✅ Уже подписан на {normalized}")
        if user_id is not None:
            if result.ok:
                set_group_membership_by_ref(user_id, normalized, MEMBERSHIP_OK)
            else:
                set_group_membership_by_ref(user_id, normalized, reason_to_status(result.reason))
        return result
    except FloodWaitError as e:
        logger.warning(f"⚠️ Ошибка FloodWait. Ожидание {e.seconds} секунд...")
        try:
            from core.metrics import record_floodwait

            await record_floodwait()
        except Exception:
            pass
        await asyncio.sleep(e.seconds)
        try:
            result = await join_chat_ref(client, normalized)
            if user_id is not None:
                if result.ok:
                    set_group_membership_by_ref(user_id, normalized, MEMBERSHIP_OK)
                else:
                    set_group_membership_by_ref(user_id, normalized, reason_to_status(result.reason))
            return result
        except Exception as retry_error:
            logger.error(f"❌ Не удалось подписаться на {normalized} после FloodWait: {retry_error}")
            result = JoinResult("error", REASON_UNKNOWN)
            if user_id is not None:
                set_group_membership_by_ref(user_id, normalized, reason_to_status(REASON_UNKNOWN))
            return result
    except AuthKeyUnregisteredError:
        logger.error("Не валидная сессия Telegram. Разорвано соединение")
        return JoinResult("error", REASON_UNKNOWN)
    except InviteRequestSentError:
        logger.error(f"❌ Запрос на приглашение отправлен для {normalized}, ожидание одобрения")
        result = JoinResult("error", REASON_PENDING_APPROVAL)
        if user_id is not None:
            set_group_membership_by_ref(user_id, normalized, reason_to_status(REASON_PENDING_APPROVAL))
        return result
    except ChannelPrivateError:
        logger.error(f"⚠️ Чат {normalized} приватный или недоступен")
        result = JoinResult("error", REASON_PRIVATE)
        if user_id is not None:
            set_group_membership_by_ref(user_id, normalized, reason_to_status(REASON_PRIVATE))
        return result
    except Exception as e:
        logger.exception("subscription_error", error=e)
        result = JoinResult("error", REASON_UNKNOWN)
        if user_id is not None:
            set_group_membership_by_ref(user_id, normalized, reason_to_status(REASON_UNKNOWN))
        return result
