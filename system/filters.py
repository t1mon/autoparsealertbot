from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from core.access import is_user_allowed
from core.config import ADMIN_USER_IDS

_GROUP_CHAT_TYPES = frozenset({"group", "supergroup"})


def _event_chat_type(event: TelegramObject) -> str | None:
    if isinstance(event, Message):
        return event.chat.type if event.chat else None
    if isinstance(event, CallbackQuery) and event.message and event.message.chat:
        return event.message.chat.type
    return None


def _event_user_id(event: TelegramObject) -> int | None:
    user = getattr(event, "from_user", None)
    if user is None and isinstance(event, CallbackQuery) and event.message:
        user = event.message.from_user
    if user is None:
        return None
    return int(user.id)


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        uid = _event_user_id(event)
        return uid is not None and uid in ADMIN_USER_IDS


class IsAllowedUser(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        uid = _event_user_id(event)
        return uid is not None and is_user_allowed(uid)


class IsAccessRestricted(BaseFilter):
    """Пользователь не в allowlist при включённой CLOSED_BETA."""

    async def __call__(self, event: TelegramObject) -> bool:
        uid = _event_user_id(event)
        return uid is not None and not is_user_allowed(uid)


class IsPrivateChat(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        return _event_chat_type(event) == "private"


class IsGroupChat(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        return _event_chat_type(event) in _GROUP_CHAT_TYPES
