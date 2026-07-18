"""Тип автора сообщения и фильтр «только люди» / всё."""

from __future__ import annotations

AUTHOR_KINDS = ("user", "bot", "channel", "anonymous", "forward_channel")
DEFAULT_AUTHOR_KIND = "anonymous"

AUTHOR_FILTERS = ("humans", "humans_anon", "all")
DEFAULT_AUTHOR_FILTER = "humans"

_ALLOWED: dict[str, frozenset[str]] = {
    "humans": frozenset({"user"}),
    "humans_anon": frozenset({"user", "anonymous"}),
    "all": frozenset(AUTHOR_KINDS),
}


def normalize_author_kind(value: str | None) -> str:
    v = (value or DEFAULT_AUTHOR_KIND).strip().lower()
    return v if v in AUTHOR_KINDS else DEFAULT_AUTHOR_KIND


def normalize_author_filter(value: str | None) -> str:
    v = (value or DEFAULT_AUTHOR_FILTER).strip().lower()
    return v if v in AUTHOR_FILTERS else DEFAULT_AUTHOR_FILTER


def classify_author_kind(sender, message) -> str:
    """
    Определяет тип автора по Telethon sender + message.
    user | bot | channel | anonymous | forward_channel
    """
    if message is not None:
        fwd = getattr(message, "fwd_from", None)
        if fwd is not None:
            from_id = getattr(fwd, "from_id", None)
            if from_id is not None and hasattr(from_id, "channel_id"):
                return "forward_channel"

    try:
        from telethon.tl.types import Channel, Chat, User as TlUser

        if isinstance(sender, TlUser):
            return "bot" if getattr(sender, "bot", False) else "user"
        if isinstance(sender, Channel):
            return "channel"
        if isinstance(sender, Chat):
            return "anonymous"
    except Exception:
        pass

    # Duck-typing (тесты / неожиданные типы)
    if sender is not None:
        if hasattr(sender, "first_name") and hasattr(sender, "bot"):
            return "bot" if getattr(sender, "bot", False) else "user"
        if hasattr(sender, "broadcast"):
            return "channel"
        if type(sender).__name__ == "Chat":
            return "anonymous"

    if message is not None:
        if getattr(message, "post_author", None):
            return "channel"
        from_id = getattr(message, "from_id", None)
        if from_id is not None:
            if hasattr(from_id, "user_id"):
                return "user"
            if hasattr(from_id, "channel_id"):
                return "channel"

    return "anonymous"


def author_kind_allowed(author_filter: str, author_kind: str) -> bool:
    mode = normalize_author_filter(author_filter)
    kind = normalize_author_kind(author_kind)
    return kind in _ALLOWED[mode]
