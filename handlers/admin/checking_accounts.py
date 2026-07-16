from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
import structlog

logger = structlog.get_logger(__name__)

from account_manager.auth import CheckingAccountsValidity
from database.database import getting_account, User
from locales.locales import t

router = Router(name=__name__)


@router.callback_query(F.data == "menu:admin:check_accounts")
async def checking_accounts_handler(callback: CallbackQuery, state: FSMContext):
    """✅ Проверка аккаунтов на валидность"""
    try:
        await state.clear()  # Сбрасываем текущее состояние FSM
        await callback.answer()
        message = callback.message

        user = User.get(User.user_id == callback.from_user.id)

        records = getting_account()  # Получаем все аккаунты в базе данных
        logger.info(f"Получено аккаунтов: {len(records)}")

        await message.answer(t("checking_accounts_start", lang=user.language, count=len(records)))

        for session_name in records:
            logger.info(f"✅ Проверка аккаунта на валидность: {session_name}")

            # ✅ Проверка аккаунтов на валидность
            checker = CheckingAccountsValidity(
                message=message,
                user_id=callback.from_user.id,
            )

            await checker.verify_account(session_name)

        await message.answer(
            t("checking_accounts_complete", lang=user.language)
        )

    except Exception as e:
        logger.exception("checking_accounts_error", error=e)
