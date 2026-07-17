"""Фильтр алертов по типу чата: all | channels | groups."""

from __future__ import annotations

CHAT_FILTERS = ("all", "channels", "groups")
DEFAULT_CHAT_FILTER = "all"


def normalize_chat_filter(value: str | None) -> str:
    v = (value or DEFAULT_CHAT_FILTER).strip().lower()
    return v if v in CHAT_FILTERS else DEFAULT_CHAT_FILTER


def classify_chat_entity(entity) -> str:
    """
    Returns: channel | group | other
    """
    if entity is None:
        return "other"
    # Telethon Channel
    broadcast = getattr(entity, "broadcast", None)
    megagroup = getattr(entity, "megagroup", None)
    if broadcast is True:
        return "channel"
    if megagroup is True:
        return "group"
    # Old Chat group
    class_name = type(entity).__name__
    if class_name == "Chat":
        return "group"
    if class_name == "Channel":
        # неизвестный Channel без флагов — считаем каналом
        return "channel"
    return "other"


def chat_type_allowed(chat_filter: str, chat_kind: str) -> bool:
    mode = normalize_chat_filter(chat_filter)
    if mode == "all":
        return True
    if mode == "channels":
        return chat_kind == "channel"
    if mode == "groups":
        return chat_kind == "group"
    return True
