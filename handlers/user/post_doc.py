import os

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from groq import AsyncGroq

from core.config import GROQ_API_KEY
from core.proxy import setup_proxy
from database.database import User, add_question
from keyboards.user.keyboards import back_keyboard
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


# Чтение базы знаний
def load_knowledge_base():
    """Загружает содержимое файла базы знаний."""
    if os.path.exists("doc/doc.md"):
        with open("doc/doc.md", "r", encoding="utf-8") as file:
            return file.read()
    else:
        return "База знаний не найдена. Пожалуйста, создайте файл doc/doc.md."


@router.callback_query(F.data == "menu:instruction")
async def send_instruction(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды "Инструкция по использованию".
    Отправляет файл инструкции и переводит пользователя в состояние ожидания вопроса к ИИ.
    """
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"

    try:
        # Отправляем файл инструкции
        await callback.message.edit_text(
            text=t("instruction_question_prompt", lang=user_lang),
            parse_mode="html",
            reply_markup=back_keyboard(lang=user_lang, callback_data="back:main")
        )
        # Устанавливаем состояние для ожидания вопроса
        await state.set_state(MyStates.waiting_for_instruction_question)

    except FileNotFoundError:
        await callback.message.answer(t("instruction_file_not_found", lang=user_lang))
    except Exception as e:
        logger.exception("instruction_send_error", error=e)
        await callback.message.answer(t("instruction_send_error", lang=user_lang))


@router.message(MyStates.waiting_for_instruction_question, F.text)
async def handle_instruction_question(message: Message, state: FSMContext):
    """
    Обрабатывает вопросы пользователя по инструкции с использованием Groq AI.
    """
    text_question = message.text  # Получаем вопрос пользователя
    user_db = User.get(User.user_id == message.from_user.id)
    user_lang = user_db.language if user_db.language != "unset" else "ru"

    knowledge_base_content = load_knowledge_base()  # Загружаем базу знаний из файла doc/doc.md

    # Индикация того, что бот "печатает"
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        setup_proxy()
        client = AsyncGroq(api_key=GROQ_API_KEY)

        system_prompt = t('ai_support_assistant_system_prompt', lang=user_lang)

        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\nБАЗА ЗНАНИЙ:\n{knowledge_base_content}"},
                {"role": "user", "content": text_question},
            ],
            model="llama-3.3-70b-versatile",
        )

        answer = chat_completion.choices[0].message.content

        add_question(user_id=message.from_user.id, question=text_question, answer=answer)

        await message.answer(
            answer,
            parse_mode="HTML",
            reply_markup=back_keyboard(lang=user_lang, callback_data="back:main"),
        )

    except Exception as e:
        logger.exception("instruction_question_error", error=e)
        await message.answer(t("instruction_send_error", lang=user_db.language))
