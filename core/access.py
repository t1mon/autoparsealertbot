"""Проверка доступа к боту (закрытая бета)."""

from __future__ import annotations

from core.config import ADMIN_USER_IDS, ALLOWED_USER_IDS, CLOSED_BETA


def is_user_allowed(user_id: int) -> bool:
    """True — пользователь может пользоваться ботом и Web API."""
    if not CLOSED_BETA:
        return True
    return int(user_id) in ALLOWED_USER_IDS
