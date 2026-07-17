from pathlib import Path

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from telethon.sessions import StringSession

from account_manager.auth import CheckingAccountsValidity, get_account_info
from account_manager.session import _is_session_valid
from database.database import (
    User,
    delete_user_account,
    get_active_account,
    get_user_accounts,
    set_active_account,
    write_account_to_user_table,
)
from handlers.user.menu_helpers import edit_or_answer
from keyboards.user.keyboards import accounts_menu_keyboard, back_keyboard
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def creates_temporary_folder_for_accounts():
    """
    Создание временной папки для аккаунтов пользователя.
    :return:
    """
    sessions_dir = Path("accounts")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def sanitization_file_name(document, sessions_dir):
    """
    Очистка имени файла от недопустимых символов (файлов сессии).
    :return:
    """
    safe_file_name = "".join(c for c in document.file_name if c.isalnum() or c in "._-")
    local_file_path = sessions_dir / safe_file_name
    return local_file_path, safe_file_name


def _accounts_screen_text(lang: str, user_id: int) -> str:
    accounts = get_user_accounts(user_id)
    active = get_active_account(user_id)
    if active:
        active_label = (active.get("phone_number") or "").strip() or t(
            "account_connected_unknown", lang=lang
        )
    else:
        active_label = t("account_not_connected", lang=lang)
    return t(
        "accounts_menu_template",
        lang=lang,
        active_label=active_label,
        count=len(accounts),
    )


async def show_accounts_menu(event: Message | CallbackQuery, state: FSMContext | None = None) -> None:
    if state is not None:
        await state.clear()
    user_id = event.from_user.id
    lang = "ru"
    try:
        user = User.get(User.user_id == user_id)
        lang = user.language if user.language != "unset" else "ru"
    except User.DoesNotExist:
        pass
    accounts = get_user_accounts(user_id)
    await edit_or_answer(
        event,
        _accounts_screen_text(lang, user_id),
        reply_markup=accounts_menu_keyboard(lang=lang, accounts=accounts),
    )


@router.callback_query(F.data.in_({"menu:accounts", "back:accounts", "menu:settings:connect_account"}))
async def handle_accounts_menu(callback: CallbackQuery, state: FSMContext):
    await show_accounts_menu(callback, state)


@router.callback_query(F.data.startswith("menu:accounts:set:"))
async def handle_set_active_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = User.get(User.user_id == user_id)
    lang = user.language if user.language != "unset" else "ru"
    try:
        account_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return

    account = set_active_account(user_id, account_id)
    if not account:
        await callback.answer(t("accounts_not_found", lang=lang), show_alert=True)
        return

    phone = (account.get("phone_number") or "").strip() or "?"
    await callback.answer(t("accounts_set_active_ok", lang=lang, phone=phone))
    await show_accounts_menu(callback, state)


@router.callback_query(F.data.startswith("menu:accounts:del:"))
async def handle_delete_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = User.get(User.user_id == user_id)
    lang = user.language if user.language != "unset" else "ru"
    try:
        account_id = int(callback.data.split(":")[-1])
    except ValueError:
        await callback.answer()
        return

    ok = delete_user_account(user_id, account_id)
    if not ok:
        await callback.answer(t("accounts_not_found", lang=lang), show_alert=True)
        return

    await callback.answer(t("accounts_deleted_ok", lang=lang))
    await show_accounts_menu(callback, state)


@router.callback_query(F.data == "menu:accounts:check")
async def handle_check_active_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = User.get(User.user_id == user_id)
    lang = user.language if user.language != "unset" else "ru"
    account = get_active_account(user_id)
    if not account:
        await callback.answer(t("no_accounts", lang=lang), show_alert=True)
        return

    phone = (account.get("phone_number") or "").strip() or "?"
    await callback.answer(t("accounts_check_progress", lang=lang))
    valid = await _is_session_valid(account["session_string"])
    if valid:
        text = t("accounts_check_ok", lang=lang, phone=phone)
    else:
        text = t("accounts_check_fail", lang=lang, phone=phone)

    accounts = get_user_accounts(user_id)
    await edit_or_answer(
        callback,
        f"{_accounts_screen_text(lang, user_id)}\n\n{text}",
        reply_markup=accounts_menu_keyboard(lang=lang, accounts=accounts),
    )


@router.callback_query(F.data.in_({"menu:accounts:connect", "menu:connect:account"}))
async def handle_connect_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user, _created = User.get_or_create(
        user_id=callback.from_user.id,
        defaults={
            "username": callback.from_user.username,
            "first_name": callback.from_user.first_name,
            "last_name": callback.from_user.last_name,
            "language": "unset",
        },
    )
    user_lang = user.language if user.language != "unset" else "ru"
    await callback.message.edit_text(
        text=t("connect_account", lang=user_lang),
        reply_markup=back_keyboard(lang=user_lang, callback_data="back:accounts"),
    )
    await state.set_state(MyStates.waiting_for_session_file_user)


# ✅ Фильтр: только документы И только в нужном состоянии
@router.message(MyStates.waiting_for_session_file_user, F.document)
async def handle_account_file(message: Message, state: FSMContext):
    """Обработчик приёма файла сессии (.session) от пользователя"""
    local_file_path = None  # для безопасного удаления в finally

    user = User.get(User.user_id == message.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"

    try:
        logger.info(f"User {message.from_user.id} отправил файл: {message.document.file_name}")

        # ✅ Проверяем расширение — если не .session, остаёмся в состоянии
        if not message.document.file_name.endswith(".session"):
            await message.answer(t("invalid_session_file", lang=user_lang))
            return  # state НЕ сбрасываем — ждём правильный файл

        sessions_dir = creates_temporary_folder_for_accounts()
        local_file_path, safe_file_name = sanitization_file_name(message.document, sessions_dir)

        await message.bot.download(message.document, destination=local_file_path)
        logger.info(f"✅ Файл скачан: {local_file_path}")

        await message.answer(t("session_file_received", lang=user_lang, filename=safe_file_name))

        session_path_without_ext = str(local_file_path.with_suffix(""))
        checker = CheckingAccountsValidity(message=message, path=session_path_without_ext)
        client = await checker.connect_client()

        if client:
            account_info = await get_account_info(client)
            phone = account_info["phone"] or "unknown"
            first_name = account_info["first_name"] or ""

            session_string = StringSession.save(client.session)
            write_account_to_user_table(
                user_id=message.from_user.id,
                session_string=session_string,
                phone_number=phone,
            )
            await client.disconnect()

            logger.info(f"✅ Сессия добавлена: {phone} | {first_name}")
            await message.answer(
                t(
                    "session_connected_success",
                    lang=user_lang,
                    filename=safe_file_name,
                    phone=phone,
                    name=first_name,
                ),
                parse_mode="HTML",
            )
            from handlers.user.menu_helpers import show_wizard

            await show_wizard(message, state)
            return
        else:
            logger.warning(
                f"❌ Сессия {safe_file_name} не валидна для пользователя {message.from_user.id}"
            )
            await message.answer(
                t("session_validation_failed", lang=user_lang, filename=safe_file_name),
                parse_mode="HTML",
            )

    except Exception as e:
        logger.exception(f"Ошибка при обработке сессии пользователя {message.from_user.id}: {e}")
        await message.answer(t("session_check_error", lang=user_lang))

    finally:
        # ✅ Удаляем временный файл в любом случае
        if local_file_path and local_file_path.exists():
            local_file_path.unlink()
        # ✅ Сбрасываем состояние только в конце
        await state.clear()
