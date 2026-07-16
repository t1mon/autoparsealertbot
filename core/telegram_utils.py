import re
from urllib.parse import urlparse

_TELEGRAM_USERNAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{3,31}$")
_INVITE_HASH_RE = re.compile(r"(?:joinchat/|\+)([A-Za-z0-9_-]+)")
_PRIVATE_CHAT_LINK_RE = re.compile(r"/c/(\d+)(?:/|$)")
_CHAT_ID_RE = re.compile(r"^-100\d+$")


def normalize_telegram_username(raw: str) -> str | None:
    """
    Приводит ссылку или имя канала/группы к формату @username.

    Поддерживает: @name, name, https://t.me/name, t.me/name, @https://t.me/name
    Не обрабатывает приватные invite-ссылки и t.me/c/... — для них normalize_telegram_chat_ref.
    """
    if not raw:
        return None

    text = raw.strip()
    if not text:
        return None

    if text.startswith("@"):
        text = text[1:]

    lower = text.lower()
    if lower.startswith(("http://", "https://")) or lower.startswith("t.me/") or "t.me/" in lower:
        if not lower.startswith("http"):
            text = f"https://{text.lstrip('/')}"
        path = urlparse(text).path.strip("/").split("/")[0].split("?")[0]
        if not path or path.startswith("+") or path in {"c", "joinchat"}:
            return None
        text = path
    else:
        text = text.split("/")[0].split("?")[0]

    text = text.lstrip("@").strip()
    if not text or not _TELEGRAM_USERNAME_RE.match(text):
        return None

    return f"@{text}"


def _extract_invite_hash(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None

    if text.startswith("+"):
        return text[1:].split("?")[0].strip() or None

    if not text.lower().startswith("http"):
        text = f"https://{text.lstrip('/')}"

    match = _INVITE_HASH_RE.search(text)
    return match.group(1) if match else None


def _extract_private_chat_id(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None

    if text.lower().startswith("id:"):
        candidate = text[3:].strip()
        if _CHAT_ID_RE.match(candidate):
            return int(candidate)
        return None

    if _CHAT_ID_RE.match(text):
        return int(text)

    if not text.lower().startswith("http"):
        text = f"https://{text.lstrip('/')}"

    match = _PRIVATE_CHAT_LINK_RE.search(text)
    if not match:
        return None

    return int(f"-100{match.group(1)}")


def normalize_telegram_chat_ref(raw: str) -> str | None:
    """
    Каноническая ссылка на чат для хранения и отслеживания.

    Форматы:
    - @username — публичный канал/группа
    - invite:HASH — приватная группа по invite-ссылке
    - id:-100... — приватный чат по ID или ссылке t.me/c/...
    """
    if not raw:
        return None

    text = raw.strip()
    if not text:
        return None

    invite_hash = _extract_invite_hash(text)
    if invite_hash:
        return f"invite:{invite_hash}"

    chat_id = _extract_private_chat_id(text)
    if chat_id is not None:
        return f"id:{chat_id}"

    username = normalize_telegram_username(text)
    if username:
        return username

    return None


def chat_ref_label(ref: str) -> str:
    """Короткая подпись чата для логов."""
    if ref.startswith("@"):
        return ref
    if ref.startswith("invite:"):
        return f"invite +{ref[7:][:8]}..."
    if ref.startswith("id:"):
        return f"chat {ref[3:]}"
    return ref
