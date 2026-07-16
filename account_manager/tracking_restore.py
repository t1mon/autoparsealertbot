import asyncio

import structlog

logger = structlog.get_logger(__name__)

from account_manager.parser import begin_tracking, filter_messages
from core.mock_message import MockMessage
from core import tracking_store
from database.database import User
from keyboards.user.keyboards import resolve_main_keyboard
from locales.locales import t
from core.config import ADMIN_USER_IDS


async def _run_restored_tracking(user_id: int, user, mock_msg: MockMessage, stop_event: asyncio.Event) -> None:
    try:
        await filter_messages(
            message=mock_msg,
            user_id=user_id,
            user=user,
            stop_event=stop_event,
        )
    except Exception as e:
        logger.exception(f"Ошибка восстановленного отслеживания для user_id={user_id}: {e}")


async def restore_active_tracking() -> None:
    """Восстанавливает активные отслеживания из Redis после перезапуска процесса."""
    active_ids = await tracking_store.list_active()
    if not active_ids:
        logger.info("Нет активных отслеживаний для восстановления")
        return

    logger.info(f"Восстановление отслеживания для {len(active_ids)} пользователей: {active_ids}")

    for user_id in active_ids:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            logger.warning(f"Пользователь {user_id} не найден в БД — снимаем отслеживание из Redis")
            await tracking_store.unmark_active(user_id)
            continue

        stop_event = await begin_tracking(user_id)
        if stop_event is None:
            logger.debug(f"Отслеживание user_id={user_id} уже запущено в этом процессе")
            continue

        mock_msg = MockMessage(user_id=user_id, username=user.username)
        await mock_msg.answer(
            t("tracking_restored", lang=user.language),
            reply_markup=resolve_main_keyboard(
                user.language,
                tracking_active=True,
                is_admin=user_id in ADMIN_USER_IDS,
            ),
        )
        asyncio.create_task(
            _run_restored_tracking(user_id, user, mock_msg, stop_event),
            name=f"restore-tracking-{user_id}",
        )
        logger.info(f"Задача восстановления отслеживания запущена для user_id={user_id}")
