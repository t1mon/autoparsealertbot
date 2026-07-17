"""Пресеты шаблона алерта: full | compact | minimal."""

from __future__ import annotations

ALERT_TEMPLATES = ("full", "compact", "minimal")
DEFAULT_ALERT_TEMPLATE = "full"

_TEMPLATE_FTL = {
    "full": "keyword_match_alert",
    "compact": "keyword_match_alert_compact",
    "minimal": "keyword_match_alert_minimal",
}


def normalize_alert_template(value: str | None) -> str:
    v = (value or DEFAULT_ALERT_TEMPLATE).strip().lower()
    return v if v in ALERT_TEMPLATES else DEFAULT_ALERT_TEMPLATE


def alert_template_ftl_key(template: str | None) -> str:
    return _TEMPLATE_FTL[normalize_alert_template(template)]
