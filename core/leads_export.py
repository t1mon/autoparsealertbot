"""Сборка Excel-выгрузки лидов (личка и команды в группе)."""

from __future__ import annotations

import os
from datetime import date, datetime

from database.database import Lead, get_leads_for_export
from handlers.user.get_dada import create_excel_file
from locales.locales import t


def build_leads_export_rows(leads: list[Lead]) -> list[tuple]:
    data: list[tuple] = []
    for idx, lead in enumerate(leads, start=1):
        data.append(
            (
                idx,
                lead.matched_at.strftime("%Y-%m-%d %H:%M:%S") if lead.matched_at else "",
                lead.matched_keyword,
                lead.author_name or "",
                lead.author_username or "",
                lead.author_tg_id or "",
                getattr(lead, "author_kind", None) or "",
                lead.chat_title or "",
                lead.chat_username or "",
                lead.message_link or "",
                lead.message_text or "",
            )
        )
    return data


def leads_export_headers(lang: str) -> list[str]:
    return [
        t("excel_header_number", lang=lang),
        t("excel_header_lead_time", lang=lang),
        t("excel_header_keyword", lang=lang),
        t("excel_header_author_name", lang=lang),
        t("excel_header_author_username", lang=lang),
        t("excel_header_author_id", lang=lang),
        t("excel_header_author_kind", lang=lang),
        t("excel_header_chat_title", lang=lang),
        t("excel_header_username", lang=lang),
        t("excel_header_link", lang=lang),
        t("excel_header_message_text", lang=lang),
    ]


def build_leads_xlsx_path(
    owner_user_id: int,
    lang: str,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[str, int] | None:
    """
    Создаёт xlsx на диске.
    Returns (filepath, count) или None, если лидов нет.
    """
    leads = get_leads_for_export(owner_user_id, date_from=date_from, date_to=date_to)
    if not leads:
        return None

    data = build_leads_export_rows(leads)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = ""
    if date_from and date_to:
        suffix = f"_{date_from.isoformat()}_{date_to.isoformat()}"
    elif date_from:
        suffix = f"_{date_from.isoformat()}"
    filename = f"leads_{owner_user_id}{suffix}_{timestamp}.xlsx"
    filepath = create_excel_file(
        data=data,
        headers=leads_export_headers(lang),
        filename=filename,
        sheet_name="Leads",
    )
    return filepath, len(data)


def remove_export_file(filepath: str) -> None:
    try:
        os.remove(filepath)
    except OSError:
        pass
