import os

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from groq import AsyncGroq, AuthenticationError, APIConnectionError

from core.config import GROQ_API_KEY
from core.proxy import setup_proxy
from database.database import User, add_question
from handlers.user.menu_helpers import edit_or_answer, is_parsing_ready
from keyboards.user.keyboards import back_keyboard, instruction_keyboard
from locales.locales import t
from states.states import MyStates

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


def load_knowledge_base():
    """Загружает содержимое файла базы знаний."""
    if os.path.exists("doc/doc.md"):
        with open("doc/doc.md", "r", encoding="utf-8") as file:
            return file.read()
    return "База знаний не найдена. Пожалуйста, создайте файл doc/doc.md."


def _instruction_text(lang: str) -> str:
    return t("howto_3_steps", lang=lang) + "\n\n" + t("instruction_howto_extra", lang=lang)


def _lang(user: User) -> str:
    return user.language if user.language != "unset" else "ru"


@router.callback_query(F.data == "menu:instruction")
async def send_instruction(callback: CallbackQuery, state: FSMContext):
    """Короткая инструкция «за 3 шага» + вход в Q&A."""
    await state.clear()
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    try:
        await edit_or_answer(
            callback,
            _instruction_text(lang),
            reply_markup=instruction_keyboard(
                lang=lang,
                ready=is_parsing_ready(callback.from_user.id),
            ),
        )
    except Exception as e:
        logger.exception("instruction_menu_error", error=e)
        await callback.message.answer(t("instruction_menu_error", lang=lang))


@router.callback_query(F.data == "menu:instruction:ask")
async def ask_instruction_question(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = User.get(User.user_id == callback.from_user.id)
    lang = _lang(user)
    await edit_or_answer(
        callback,
        t("instruction_ask_prompt", lang=lang),
        reply_markup=back_keyboard(lang=lang, callback_data="menu:instruction"),
    )
    await state.set_state(MyStates.waiting_for_instruction_question)


@router.message(MyStates.waiting_for_instruction_question, F.text)
async def handle_instruction_question(message: Message, state: FSMContext):
    """Ответ на вопрос по инструкции через Groq AI."""
    text_question = message.text
    user_db = User.get(User.user_id == message.from_user.id)
    user_lang = _lang(user_db)
    kb = instruction_keyboard(
        lang=user_lang,
        ready=is_parsing_ready(message.from_user.id),
    )

    if not (GROQ_API_KEY or "").strip():
        await message.answer(t("instruction_ai_no_key", lang=user_lang), reply_markup=kb)
        return

    knowledge_base_content = load_knowledge_base()
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        setup_proxy()
        client = AsyncGroq(api_key=GROQ_API_KEY)
        system_prompt = t("ai_support_assistant_system_prompt", lang=user_lang)

        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nБАЗА ЗНАНИЙ:\n{knowledge_base_content}",
                },
                {"role": "user", "content": text_question},
            ],
            model="llama-3.3-70b-versatile",
        )

        answer = (chat_completion.choices[0].message.content or "").strip()
        if not answer:
            await message.answer(t("instruction_ai_empty", lang=user_lang), reply_markup=kb)
            return

        add_question(user_id=message.from_user.id, question=text_question, answer=answer)

        try:
            await message.answer(answer, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await message.answer(answer, reply_markup=kb)
    except AuthenticationError:
        logger.error("instruction_ai_auth_error")
        await message.answer(t("instruction_ai_auth_error", lang=user_lang), reply_markup=kb)
    except APIConnectionError as e:
        logger.exception("instruction_ai_connection_error", error=e)
        await message.answer(t("instruction_ai_connection_error", lang=user_lang), reply_markup=kb)
    except Exception as e:
        logger.exception("instruction_question_error", error=e)
        await message.answer(t("instruction_ai_error", lang=user_lang), reply_markup=kb)
