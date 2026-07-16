import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from account_manager.parser import stop_tracking
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.callback_query(F.data == "menu:tracking:stop")
async def handle_stop_tracking(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "🛑 Остановить отслеживание".

    Очищает состояние FSM, получает данные пользователя и вызывает функцию `stop_tracking`
    для прекращения фонового парсинга сообщений в отслеживаемых группах.
    После остановки отправляет подтверждение пользователю.

    - Команда доступна только во время активного отслеживания.
    - Использует глобальный механизм управления задачами в `parsing/parser.py`.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, сбрасывается перед остановкой.
    :raise Exception: Передаётся в `stop_tracking`, где обрабатывается.
    """
    await state.clear()
    await callback.answer()
    logger.info(
        f"Пользователь {callback.from_user.id} {callback.from_user.username} {callback.from_user.first_name} {callback.from_user.last_name} нажал кнопку остановки отслеживания")

    await stop_tracking(user_id=callback.from_user.id, message=callback.message)
