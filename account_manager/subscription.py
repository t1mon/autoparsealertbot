import asyncio

import structlog

logger = structlog.get_logger(__name__)
from telethon.errors import (
    UserAlreadyParticipantError, FloodWaitError, InviteRequestSentError, AuthKeyUnregisteredError, ChannelPrivateError
)
from telethon.tl.functions.channels import JoinChannelRequest

from account_manager.chat_targets import join_chat_ref
from core.telegram_utils import normalize_telegram_chat_ref, normalize_telegram_username


async def subscription_telegram(client, target_username) -> str:
    """
    Подписка на группу/канал Telegram.

    :return: "joined" — новая подписка, "already" — уже подписан, "error" — ошибка
    """
    normalized = normalize_telegram_chat_ref(target_username) or normalize_telegram_username(target_username)
    if not normalized:
        logger.error(f"❌ Неверная ссылка на чат: {target_username}")
        return "error"

    try:
        result = await join_chat_ref(client, normalized)
        if result == "joined":
            logger.info(f"✅ Подписались на {normalized}")
        elif result == "already":
            logger.info(f"✅ Уже подписан на {normalized}")
        return result
    except FloodWaitError as e:
        logger.warning(f"⚠️ Ошибка FloodWait. Ожидание {e.seconds} секунд...")
        await asyncio.sleep(e.seconds)
        try:
            return await join_chat_ref(client, normalized)
        except Exception as retry_error:
            logger.error(f"❌ Не удалось подписаться на {normalized} после FloodWait: {retry_error}")
            return "error"
    except AuthKeyUnregisteredError:
        logger.error("Не валидная сессия Telegram. Разорвано соединение")
        return "error"
    except InviteRequestSentError:
        logger.error(f"❌ Запрос на приглашение отправлен для {normalized}, ожидание одобрения")
        return "error"
    except ChannelPrivateError:
        logger.error(f"⚠️ Чат {normalized} приватный или недоступен")
        return "error"
    except Exception as e:
        logger.exception("subscription_error", error=e)
        return "error"
