import os

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message

from account_manager.parser import filter_messages, is_tracking_marked, begin_tracking
from account_manager.session import find_session_file
from core.config import ADMIN_USER_IDS
from database.database import User
from handlers.user.menu_helpers import (
    edit_or_answer,
    format_readiness_gaps,
    get_main_reply_markup,
    is_parsing_ready,
    show_cabinet,
    show_main_menu,
    show_main_or_wizard,
    show_wizard,
)
from keyboards.user.keyboards import (
    back_keyboard,
    cabinet_keyboard,
    connect_keyboard_account,
    get_lang_keyboard,
    get_stars_topup_inline_keyboard,
    settings_keyboard,
)
from locales.locales import t

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.message(CommandStart())
async def handle_start_command(message, state: FSMContext) -> None:
    """
    Обработчик команды /start.

    Инициализирует пользователя в базе данных при первом запуске, обновляет его профиль
    при последующих запусках и приветствует пользователя. Если язык не выбран,
    предлагает выбрать язык интерфейса.

    Является точкой входа в бота.

    - Создаёт или получает запись в таблице `User`.
    - При повторном запуске обновляет имя и username пользователя.
    - Проверяет, является ли пользователь администратором по ID.
    - Использует ключ "unset" для обозначения незаданного языка.

    :param message: (Message) Входящее сообщение от пользователя с командой /start.
    :param state: (FSMContext) Контекст машины состояний, сбрасывается при старте.
    """
    try:
        await state.clear()  # Завершаем текущее состояние машины состояний

        user = get_or_create_user(message.from_user)  # Получаем или создаём пользователя
        # Если язык ещё не выбран — просим выбрать
        if user.language == "unset":
            await message.answer(
                "👋 Привет! Пожалуйста, выберите язык / Please choose your language:",
                reply_markup=get_lang_keyboard()
            )
        else:
            await show_main_or_wizard(message, state)

    except TelegramForbiddenError:
        logger.error(f"Пользователь {message.from_user.id, message.from_user.username} заблокировал бота")

    except Exception as e:
        logger.exception("start_handler_error", error=e)


@router.callback_query(F.data.in_({"back:main", "menu:main"}))
async def handle_back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "Назад".

    Очищает состояние FSM и возвращает пользователя в главное меню.
    Логика аналогична обработчику /start: проверяет наличие пользователя,
    обновляет профиль и показывает главное меню или запрос языка.

    Используется для навигации из подменю (настройки, добавление групп и т.д.) в основное меню.

    - Повторно использует логику инициализации из handle_start_command.
    - Не сохраняет состояние после возврата.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, сбрасывается перед возвратом.
    :return: None
    """
    try:
        get_or_create_user(callback.from_user)
        await show_main_menu(callback, state)
    except Exception as e:
        logger.exception("main_menu_error", error=e)


@router.callback_query(F.data.in_({"menu:cabinet", "back:cabinet"}))
async def handle_cabinet(callback: CallbackQuery, state: FSMContext):
    """Экран «Мой парсинг» с чеклистом готовности."""
    try:
        get_or_create_user(callback.from_user)
        await show_cabinet(callback, state)
    except Exception as e:
        logger.exception("cabinet_menu_error", error=e)


@router.callback_query(F.data.in_({"menu:wizard", "back:wizard"}))
async def handle_wizard(callback: CallbackQuery, state: FSMContext):
    try:
        get_or_create_user(callback.from_user)
        await show_wizard(callback, state)
    except Exception as e:
        logger.exception("wizard_menu_error", error=e)


@router.callback_query(F.data == "menu:wizard:account")
async def handle_wizard_account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = user.language if user.language != "unset" else "ru"
    await callback.message.edit_text(
        text=t("connect_account", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:wizard"),
    )
    from states.states import MyStates

    await state.set_state(MyStates.waiting_for_session_file_user)


@router.callback_query(F.data == "menu:wizard:keywords")
async def handle_wizard_keywords(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = user.language if user.language != "unset" else "ru"
    await edit_or_answer(
        callback,
        t("enter_keyword", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:wizard"),
    )
    from states.states import MyStates

    await state.set_state(MyStates.entering_keyword)


@router.callback_query(F.data == "menu:wizard:channels")
async def handle_wizard_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = user.language if user.language != "unset" else "ru"
    await edit_or_answer(
        callback,
        t("update_list", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="back:wizard"),
    )
    from states.states import MyStates

    await state.set_state(MyStates.waiting_username_group)


def get_or_create_user(user_tg):
    """
    Получает существующего пользователя из базы данных или создаёт нового, если он не существует.

    При создании нового пользователя устанавливает язык интерфейса в "unset" (не выбран).
    При наличии существующего пользователя обновляет его профиль (username, имя, фамилия),
    чтобы синхронизировать данные с актуальной информацией из Telegram.

    :param user_tg: (User) Объект пользователя из Telegram (aiogram.types.User).
    :return: (User) Экземпляр модели пользователя из базы данных.
    """
    # Создаём пользователя с language = "unset", если его нет
    user, created = User.get_or_create(
        user_id=user_tg.id,
        defaults={
            "username": user_tg.username,
            "first_name": user_tg.first_name,
            "last_name": user_tg.last_name,
            "language": "unset"  # ← ключевое: "unset" = язык не выбран
        }
    )
    if not created:
        # Обновляем профиль (на случай смены имени и т.п.)
        user.username = user_tg.username
        user.first_name = user_tg.first_name
        user.last_name = user_tg.last_name
        user.save()

    logger.info(
        f"Пользователь {user_tg.id} {user_tg.username} {user_tg.first_name} {user_tg.last_name} начал работу с ботом.")

    return user


@router.callback_query(F.data.in_({"menu:lang:ru", "menu:lang:en"}))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора языка пользователем.

    Обрабатывает нажатие на кнопки "🇷🇺 Русский" или "🇬🇧 English".
    Сохраняет выбранный язык в базе данных и отображает главное меню.

    Используется при первом запуске бота, когда язык установлен в "unset".

    - Выбранный язык используется для локализации всех последующих сообщений.
    - После выбора пользователь переходит в основное меню.

    :param message: (Message) Входящее сообщение с выбранным языком.
    :param state: (FSMContext) Контекст машины состояний, сбрасывается перед обработкой.
    :return: None
    :raises Exception: Не ожидается, но возможна ошибка записи в БД.
    """
    try:
        await state.clear()  # Завершаем текущее состояние машины состояния
        user = User.get(User.user_id == callback.from_user.id)
        user.language = callback.data.rsplit(":", 1)[-1]
        user.save()

        await show_main_or_wizard(callback, state)
    except Exception as e:
        logger.exception("language_selection_error", error=e)


@router.callback_query(F.data.in_({"menu:settings", "back:settings"}))
async def handle_settings_menu(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "Настройки".

    Отображает меню настроек с возможностью смены языка интерфейса.
    Не требует предварительной настройки аккаунта.

    - Текст меню локализован в зависимости от языка пользователя.
    - Клавиатура включает кнопку для смены языка.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, не используется напрямую.
    :return: None
    """
    try:
        await state.clear()  # Завершаем текущее состояние машины состояния

        user = User.get(User.user_id == callback.from_user.id)

        await edit_or_answer(
            callback,
            t("settings_message", lang=user.language),
            reply_markup=settings_keyboard(lang=user.language)
        )
    except Exception as e:
        logger.exception("settings_menu_error", error=e)


@router.callback_query(F.data.in_({"menu:lang", "menu:settings:change_lang"}))
async def handle_change_language(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "Сменить язык".

    Предлагает пользователю выбрать язык интерфейса.
    Использует клавиатуру выбора языка.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, сбрасывается.
    :return: None
    """
    try:
        await state.clear()

        await edit_or_answer(
            callback,
            t("welcome_ask_language", lang="ru"),
            reply_markup=get_lang_keyboard()
        )
    except Exception as e:
        logger.exception("language_menu_error", error=e)


@router.callback_query(F.data == "menu:tracking:start")
async def handle_start_tracking(callback: CallbackQuery, state: FSMContext):
    """Запуск отслеживания — только если аккаунт, ключи и включённые каналы готовы."""
    await state.clear()
    await callback.answer()
    message = callback.message
    try:
        user = User.get(User.user_id == callback.from_user.id)
        user_id = callback.from_user.id
        is_admin = user_id in ADMIN_USER_IDS
        lang = user.language if user.language != "unset" else "ru"

        if await is_tracking_marked(user_id):
            await message.answer(
                t("tracking_already_active", lang=lang),
                reply_markup=await get_main_reply_markup(user_id, lang, is_admin),
            )
            return

        if not is_parsing_ready(user_id):
            gaps = format_readiness_gaps(user_id, lang)
            await message.answer(
                t("tracking_not_ready", lang=lang, gaps=gaps),
                reply_markup=cabinet_keyboard(lang=lang, ready=False),
                parse_mode="HTML",
            )
            return

        logger.info(
            "tracking_start",
            user_id=user_id,
            username=callback.from_user.username,
        )

        session_dir = os.path.join("accounts", str(user_id))
        os.makedirs(session_dir, exist_ok=True)

        session_path = await find_session_file(
            user_id=user_id,
            user=user,
            message=message,
        )

        if session_path is None:
            logger.warning("no_session_account", user_id=user_id)
            await message.answer(
                t("account_missing", lang=lang),
                reply_markup=connect_keyboard_account(lang=lang),
            )
            return

        stop_event = await begin_tracking(user_id)
        if stop_event is None:
            await message.answer(
                t("tracking_already_active", lang=lang),
                reply_markup=await get_main_reply_markup(user_id, lang, is_admin),
            )
            return

        await message.answer(
            t("launching_tracking", lang=lang),
            reply_markup=await get_main_reply_markup(user_id, lang, is_admin),
        )

        await filter_messages(
            message=message,
            user_id=user_id,
            user=user,
            stop_event=stop_event,
        )
    except Exception as e:
        logger.exception("start_tracking_error", error=e)


@router.callback_query(F.data == "menu:settings:stars")
async def handle_stars_balance(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"
    
    keyboard = get_stars_topup_inline_keyboard(user_lang)
    msg_text = t("stars_balance_msg", lang=user_lang, stars=user.stars)
    
    await edit_or_answer(callback, msg_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("buy_stars_"))
async def handle_buy_stars_callback(callback: CallbackQuery, state: FSMContext):
    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"
    
    action = callback.data.split("_")[2]
    
    if action == "cancel":
        await callback.message.delete()
        await callback.answer()
        return
        
    try:
        amount = int(action)
    except ValueError:
        await callback.answer("Error", show_alert=True)
        return
        
    await callback.message.answer_invoice(
        title=t("stars_invoice_title", lang=user_lang),
        description=t("stars_invoice_desc", lang=user_lang, amount=amount),
        payload=f"topup_stars_{amount}",
        provider_token="",  # must be empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)]
    )
    await callback.answer()
