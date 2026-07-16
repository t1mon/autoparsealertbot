import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async
from g4f.client import Client
from groq import AsyncGroq
import structlog
from openai import AsyncOpenAI

from ai.ai import category_assignment
from core.config import GROQ_API_KEY, OPENROUTER_API_KEY
from database.database import TelegramGroup, db, get_groups_without_category, User
from handlers.user.menu_helpers import edit_or_answer
from keyboards.admin.keyboards import admin_keyboard, category_method_keyboard
from locales.locales import t
from states.states import CategoryMethod

router = Router(name=__name__)
logger = structlog.get_logger(__name__)


@router.callback_query(F.data == "menu:admin:assign_category")
async def checking_group_for_ai_db(callback: CallbackQuery, state: FSMContext):
    """Предлагает выбор метода присвоения категорий"""
    await state.set_state(CategoryMethod.waiting_for_method)
    await callback.answer()

    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"

    await edit_or_answer(
        callback,
        t("ai_category_select_method", lang=user_lang),
        reply_markup=category_method_keyboard(lang=user_lang),
    )


async def get_best_g4f_model(client: Client) -> str:
    """Проверяет доступность моделей g4f и возвращает первую рабочую."""
    models_to_check = [
        "llama-3.1-8b-instant",
        "gpt-4o-mini",
        "llama-3.2-3b",
        "mistral-7b",
        "llama-3.2-1b",
    ]

    test_prompt = [{"role": "user", "content": "Hi"}]

    for model in models_to_check:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=model,
                    messages=test_prompt,
                    timeout=5,
                ),
                timeout=7,
            )
            logger.info("Модель доступна", model=model)
            return model
        except asyncio.TimeoutError:
            logger.warning("Таймаут модели", model=model)
        except Exception as e:
            logger.warning("Модель не работает", model=model, error=type(e).__name__)
            continue

    logger.warning("Ни одна модель не доступна, используем gpt-4o-mini")
    return "gpt-4o-mini"


@router.callback_query(F.data.startswith("menu:admin:method:"))
async def process_category_method_choice(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор метода присвоения категорий"""
    await callback.answer()
    user = User.get(User.user_id == callback.from_user.id)
    user_lang = user.language if user.language != "unset" else "ru"
    method = callback.data.rsplit(":", 1)[-1]
    message = callback.message

    if method == "fast":
        await state.clear()
        client = Client()
        status_msg = await message.answer(t("ai_category_checking_models", lang=user_lang))
        model = await get_best_g4f_model(client)
        await status_msg.edit_text(t("ai_category_model_selected", lang=user_lang, model=model))
        await asyncio.sleep(1)
        await status_msg.delete()
        await assign_categories(message, client, model)

    elif method == "openrouter":
        await state.clear()
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        model = "deepseek/deepseek-v4-flash"
        await assign_categories(message, client, model=model)

    elif method == "groq":
        await state.clear()
        client = AsyncGroq(api_key=GROQ_API_KEY)
        model = "llama-3.1-8b-instant"
        await assign_categories(message, client, model)

    else:
        await edit_or_answer(
            callback,
            t("ai_category_select_from_keyboard", lang=user_lang),
            reply_markup=category_method_keyboard(lang=user_lang),
        )


async def assign_categories(message: Message, client, model):
    """Универсальная функция присвоения категорий (любой AI клиент).

    При вызове из CallbackQuery.from_user на message — бот, поэтому берём chat.id.
    """
    user_id = message.chat.id
    user = User.get(User.user_id == user_id)
    user_lang = user.language if user.language != "unset" else "ru"

    status_msg = await message.answer(t("ai_category_processing", lang=user_lang, total=0))

    try:
        groups_to_process = await get_groups_without_category()

        if not groups_to_process:
            await status_msg.edit_text(t("ai_category_all_have_categories", lang=user_lang))
            return

        total = len(groups_to_process)
        logger.info("Групп для обработки", total=total)

        await status_msg.edit_text(t("ai_category_processing", lang=user_lang, total=total))

        for i, group_data in enumerate(groups_to_process, 1):
            try:
                result = await category_assignment(group_data, client, model)

                if result.get("success") and result.get("category"):
                    category_lower = result["category"].lower()
                    await sync_to_async(
                        lambda: TelegramGroup.update(category=category_lower)
                        .where(TelegramGroup.telegram_id == result["telegram_id"])
                        .execute(),
                        thread_sensitive=True,
                    )()
                    logger.info(
                        "Категория присвоена",
                        index=i,
                        total=total,
                        name=group_data["name"],
                        category=category_lower,
                    )
                else:
                    logger.warning(
                        "AI не определил категорию",
                        index=i,
                        total=total,
                        name=group_data["name"],
                    )

                if type(client).__name__ == "Client":
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error("Ошибка обработки группы", name=group_data.get("name"), error=e)
                continue

        await status_msg.edit_text(t("ai_category_done", lang=user_lang), parse_mode="HTML")

    except Exception as e:
        logger.exception("assign_categories_error", error=e)
        await status_msg.edit_text(t("ai_category_error", lang=user_lang, error=str(e)))
