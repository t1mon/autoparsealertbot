import os

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from account_manager.parser import filter_messages, is_tracking_marked, begin_tracking
from account_manager.session import find_session_file
from database.database import (
    User, getting_number_records_database, get_session_count, get_keywords_count,
    get_tracked_channels_count, Groups
)
from keyboards.user.keyboards import (
    get_lang_keyboard, resolve_main_keyboard, settings_keyboard, back_keyboard,
    connect_keyboard_account, get_stars_topup_inline_keyboard
)
from locales.locales import t
from aiogram.types import CallbackQuery, LabeledPrice, Message, ReplyKeyboardRemove
from states.states import MyStates
from core.config import ADMIN_USER_IDS
from core.telegram_utils import normalize_telegram_chat_ref
from handlers.user.menu_helpers import edit_or_answer, show_main_menu

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


async def get_main_reply_markup(user_id: int, lang: str, is_admin: bool):
    return resolve_main_keyboard(
        lang,
        tracking_active=await is_tracking_marked(user_id),
        is_admin=is_admin,
    )


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
        await message.answer("\u2060", reply_markup=ReplyKeyboardRemove())
        # Если язык ещё не выбран — просим выбрать
        if user.language == "unset":
            await message.answer(
                "👋 Привет! Пожалуйста, выберите язык / Please choose your language:",
                reply_markup=get_lang_keyboard()
            )
        else:
            is_admin = message.from_user.id in ADMIN_USER_IDS
            reply_markup = await get_main_reply_markup(message.from_user.id, user.language, is_admin)

            await message.answer(
                text=generate_welcome_message(user_language=user.language, user_tg_id=message.from_user.id),
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

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


def generate_welcome_message(user_language: str, user_tg_id: int) -> str:
    """
    Генерирует приветственное сообщение для пользователя с подставленными данными.

    Собирает информацию о:
    - версии бота
    - общем количестве найденных групп в базе
    - количестве подключённых пользователем сессий (аккаунтов)
    - количестве подключённых технических групп (для пересылки)
    - количестве отслеживаемых каналов
    - количестве сохранённых ключевых слов

    :param user_language: Язык пользователя (например, 'ru', 'en') для выбора шаблона.
    :param user_tg_id: Telegram ID пользователя для получения его данных.
    :return: Готовое текстовое сообщение для отправки.
    """
    version = "0.0.9"
    groups_count = getting_number_records_database()  # Общее число найденных групп
    count = get_session_count(user_id=user_tg_id)  # Сессии пользователя
    get_groups = get_tracked_channels_count(user_id=user_tg_id)  # Отслеживаемые каналы
    keywords_count = get_keywords_count(user_id=user_tg_id)  # Ключевые слова

    return t(
        "welcome_message_template",
        lang=user_language,
        version=version,
        groups_count=groups_count,
        count=count,
        get_groups=get_groups,
        keywords_count=keywords_count
    )


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


async def _save_tracking_usernames(message: Message, raw_values: list[str], user) -> None:
    added_count = 0
    skipped_count = 0
    errors_count = 0

    for raw_username in raw_values:
        username = normalize_telegram_chat_ref(raw_username)
        if not username:
            errors_count += 1
            logger.warning(f"Пропущен невалидный чат: {raw_username}")
            continue

        try:
            Groups.create(
                user_id=message.from_user.id,
                username=username
            )
            added_count += 1
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                skipped_count += 1
            else:
                errors_count += 1
                logger.error(f"Ошибка при добавлении {username}: {e}")

    response = t(
        "groups_upload_summary",
        lang=user.language,
        added=added_count,
        skipped=skipped_count,
        errors=errors_count
    )
    await message.answer(response)


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
        confirmation_text = t("lang_selected", lang=user.language)

        user.save()

        await edit_or_answer(
            callback,
            confirmation_text,
            reply_markup=await get_main_reply_markup(
                callback.from_user.id,
                user.language,
                callback.from_user.id in ADMIN_USER_IDS,
            ),
        )
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
    """
    Обработчик команды "Запуск отслеживания".

    Проверяет наличие подключенного Telegram-аккаунта (.session файл) у пользователя.
    Если аккаунт найден, запускает процесс фильтрации сообщений с помощью `filter_messages`.
    Если аккаунт не найден, уведомляет пользователя и предлагает 🔐 Подключить аккаунт.

    - Путь к сессии ищется в папке `accounts/{user_id}/`.
    - Используется первое найденное .session-расширение.
    - Сообщение о запуске отправляется до начала парсинга.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, не используется напрямую.
    :return: None
    :raises: Передаётся в `filter_messages`, где обрабатывается.
    """
    await state.clear()
    await callback.answer()
    message = callback.message
    try:
        user = User.get(User.user_id == callback.from_user.id)
        user_id = callback.from_user.id
        is_admin = user_id in ADMIN_USER_IDS

        if await is_tracking_marked(user_id):
            await message.answer(
                t("tracking_already_active", lang=user.language),
                reply_markup=await get_main_reply_markup(user_id, user.language, is_admin),
            )
            return

        logger.info(
            f"Пользователь {user_id} {callback.from_user.username} {callback.from_user.first_name} {callback.from_user.last_name} перешел в меню запуска парсинга.")

        session_dir = os.path.join("accounts", str(user_id))
        os.makedirs(session_dir, exist_ok=True)

        session_path = await find_session_file(
            user_id=user_id,
            user=user,
            message=message,
        )

        logger.info(session_path)
        if session_path is None:
            logger.warning("Нет подключенного аккаунта")
            await message.answer(
                text="Нет подключенного аккаунта. Подключите аккаунт.",
                reply_markup=connect_keyboard_account(lang=user.language),
            )
            return

        stop_event = await begin_tracking(user_id)
        if stop_event is None:
            await message.answer(
                t("tracking_already_active", lang=user.language),
                reply_markup=await get_main_reply_markup(user_id, user.language, is_admin),
            )
            return

        await message.answer(
            t("launching_tracking", lang=user.language),
            reply_markup=await get_main_reply_markup(user_id, user.language, is_admin),
        )

        await filter_messages(
            message=message,
            user_id=user_id,
            user=user,
            stop_event=stop_event,
        )
    except Exception as e:
        logger.exception("start_tracking_error", error=e)


@router.callback_query(F.data == "menu:settings:update_list")
async def handle_refresh_groups_list(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "🔁 Обновить список".

    Позволяет пользователю добавить новые группы или каналы для отслеживания.
    Отправляет приглашение ввести username-ы и переводит пользователя в состояние ожидания ввода.

    - Принимает несколько username за раз, разделённые пробелами или переносами строк.
    - После отправки сообщения пользователь должен ввести @username-ы.
    - Используется состояние `MyStates.waiting_username_group`.

    :param message: (Message) Входящее сообщение от пользователя.
    :param state: (FSMContext) Контекст машины состояний, используется для установки состояния.
    :return: None
    """
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)

    logger.info(
        f"Пользователь {callback.from_user.id} {callback.from_user.username} {callback.from_user.first_name} {callback.from_user.last_name} перешел в меню 🔁 Обновить список")

    await callback.message.edit_text(
        text=t("update_list", lang=user.language),  # текст сообщения
        reply_markup=back_keyboard(lang=user.language, callback_data="back:settings"),
        parse_mode="HTML"
    )
    await state.set_state(MyStates.waiting_username_group)


@router.message(MyStates.waiting_username_group, F.document)
async def handle_group_usernames_file(message, state: FSMContext, bot):
    """
    Обработчик загрузки .txt файла со списком групп/каналов.
    """
    user = User.get(User.user_id == message.from_user.id)
    document = message.document

    # Проверяем расширение файла
    if not document.file_name.endswith(".txt"):
        await message.answer(t("only_txt_files_supported", lang=user.language))
        return

    # Скачиваем файл
    file = await bot.get_file(document.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read().decode("utf-8")

    # Парсим строки — каждая строка это отдельный username
    usernames = [line.strip() for line in content.splitlines() if line.strip()]

    if not usernames:
        await message.answer(t("empty_file_no_usernames", lang=user.language))
        await state.clear()
        return

    await _save_tracking_usernames(message, usernames, user)
    await state.clear()


@router.message(MyStates.waiting_username_group, F.text)
async def handle_group_usernames_text(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода списка групп/каналов.
    """
    user = User.get(User.user_id == message.from_user.id)
    raw_values = [
        item.strip()
        for item in message.text.replace(",", "\n").splitlines()
        if item.strip()
    ]

    if not raw_values:
        await message.answer(t("empty_file_no_usernames", lang=user.language))
        return

    await _save_tracking_usernames(message, raw_values, user)
    await state.clear()


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
