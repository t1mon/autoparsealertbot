import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from playhouse.migrate import SqliteMigrator, migrate

from database.database import User, db
from keyboards.user.keyboards import back_keyboard
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def rename_old_table_to_new_table(user_id, id_transfer_user):
    """Переименовывает таблицу в новую для пользователя"""

    # 1. Инициализируем мигратор
    migrator = SqliteMigrator(db)
    # 2. Выполняем миграцию: указываем старое имя таблицы и новое
    migrate(
        migrator.rename_table(f"{user_id}_keywords", f"{id_transfer_user}_keywords")
    )
    logger.warning("Таблица успешно переименована!")
    
    
    migrate(
        migrator.rename_table(f"{user_id}_group", f"{user_id}_group")
    )
    logger.warning("Таблица успешно переименована!")


@router.callback_query(F.data == "menu:settings:transfer")
async def transfer_settings(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()  # Завершаем текущее состояние машины состояния
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    await callback.message.edit_text(
        "Введите ID пользователя для передачи настроек:\n\nПример ввода - 1234567890",
        reply_markup=back_keyboard(user.language, callback_data="back:settings"),
    )

    await state.set_state(MyStates.get_id_user_transfer)


@router.message(MyStates.get_id_user_transfer, F.text)
async def get_id_for_transferring(message, state: FSMContext, bot):
    user = User.get(User.user_id == message.from_user.id)
    id_transfer_user = message.text.strip()

    await state.clear()  # Завершаем текущее состояние машины состояния

    rename_old_table_to_new_table(
        user_id=message.from_user.id, 
        id_transfer_user=id_transfer_user

        )

    await message.answer(f"Настройки успешно переданы! пользователю с id {id_transfer_user}")
