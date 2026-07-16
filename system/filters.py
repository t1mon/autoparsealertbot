from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from core.config import ADMIN_USER_IDS


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None and isinstance(event, CallbackQuery) and event.message:
            user = event.message.from_user
        return user is not None and user.id in ADMIN_USER_IDS
