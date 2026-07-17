"""Коды статуса подписки аккаунта на канал (для БД и UI)."""

from __future__ import annotations

# Значения в Groups.membership_status
MEMBERSHIP_OK = "ok"
MEMBERSHIP_MISSING = "missing"
MEMBERSHIP_PENDING = "pending"
MEMBERSHIP_PRIVATE = "private"
MEMBERSHIP_ERROR = "error"

# Детальные причины (ключи локализации membership_reason_*)
REASON_NOT_MEMBER = "not_member"
REASON_PENDING_APPROVAL = "pending_approval"
REASON_PRIVATE = "private"
REASON_CHECK_FAILED = "check_failed"
REASON_INVALID_REF = "invalid_ref"
REASON_INVITE_EXPIRED = "invite_expired"
REASON_UNKNOWN = "unknown"


def reason_to_status(reason: str | None) -> str:
    if not reason:
        return MEMBERSHIP_MISSING
    if reason == REASON_PENDING_APPROVAL:
        return MEMBERSHIP_PENDING
    if reason in (REASON_PRIVATE, REASON_INVITE_EXPIRED):
        return MEMBERSHIP_PRIVATE
    if reason in (REASON_CHECK_FAILED, REASON_INVALID_REF, REASON_UNKNOWN):
        return MEMBERSHIP_ERROR
    return MEMBERSHIP_MISSING


def membership_badge(status: str | None) -> str:
    if not status or status == MEMBERSHIP_OK:
        return ""
    if status == MEMBERSHIP_PENDING:
        return "🕐"
    if status == MEMBERSHIP_PRIVATE:
        return "🔒"
    if status == MEMBERSHIP_ERROR:
        return "❌"
    if status == MEMBERSHIP_MISSING:
        return "⚠️"
    return "⚠️"


def membership_status_label(lang: str, status: str | None) -> str:
    from locales.locales import t

    if not status:
        return ""
    key = f"channel_membership_{status}"
    text = t(key, lang=lang)
    return text if text != key else ""


def membership_reason_label(lang: str, reason: str | None) -> str:
    from locales.locales import t

    if not reason:
        return t("membership_reason_not_member", lang=lang)
    key = f"membership_reason_{reason}"
    text = t(key, lang=lang)
    return text if text != key else reason
