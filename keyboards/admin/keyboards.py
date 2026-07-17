"""Inline keyboards for admin / main menu rows."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from core.config import WEBAPP_URL
from locales.locales import t


def _btn(text: str, callback_data: str, style: str | None = None) -> InlineKeyboardButton:
    kwargs: dict = {"text": text, "callback_data": callback_data}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(**kwargs)


def menu_user_admin_rows(
    lang: str = "ru",
    tracking_active: bool = False,
    ready: bool = False,
) -> list[list[InlineKeyboardButton]]:
    if tracking_active:
        tracking_row = [_btn(t("stop_tracking_button", lang=lang), "menu:tracking:stop", "danger")]
    elif ready:
        tracking_row = [_btn(t("launch_tracking_button", lang=lang), "menu:tracking:start", "success")]
    else:
        tracking_row = [_btn(t("setup_before_start_button", lang=lang), "menu:wizard", "primary")]

    rows: list[list[InlineKeyboardButton]] = [
        tracking_row,
        [_btn(t("my_parsing_button", lang=lang), "menu:cabinet", "primary")],
        [
            _btn(t("ai_search_button", lang=lang), "menu:ai", "primary"),
            _btn(t("get_database_button", lang=lang), "menu:database", "primary"),
        ],
        [_btn(t("instruction_button", lang=lang), "menu:instruction", "primary")],
        [_btn(t("settings_button", lang=lang), "menu:settings", "primary")],
    ]

    if WEBAPP_URL:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Веб панель",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        )

    return rows


def main_menu_keyboard(
    lang: str = "ru",
    tracking_active: bool = False,
    ready: bool = False,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=menu_user_admin_rows(lang, tracking_active=tracking_active, ready=ready)
    )


def main_admin_keyboard(
    lang: str = "ru",
    tracking_active: bool = False,
    ready: bool = False,
) -> InlineKeyboardMarkup:
    rows = menu_user_admin_rows(lang, tracking_active=tracking_active, ready=ready)
    rows.append([_btn(t("admin_panel_button", lang=lang), "menu:admin", "success")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("admin_tracking_button", lang=lang), "menu:admin:tracking", "success")],
            [
                _btn(t("get_log_file_button", lang=lang), "menu:admin:logs", "primary"),
                _btn(t("update_database_button", lang=lang), "menu:admin:update_db", "primary"),
            ],
            [
                _btn(t("export_questions_button", lang=lang), "menu:admin:export", "primary"),
                _btn(t("assign_category_button", lang=lang), "menu:admin:assign_category", "primary"),
                _btn(t("check_accounts_button", lang=lang), "menu:admin:check_accounts", "success"),
            ],
            [
                _btn(t("assign_language_button", lang=lang), "menu:admin:assign_lang", "primary"),
                _btn(t("connect_account_button", lang=lang), "menu:admin:connect_account", "primary"),
            ],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def admin_tracking_keyboard(lang: str, user_ids: list[int] | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for uid in user_ids or []:
        rows.append(
            [
                _btn(
                    t("admin_tracking_stop_button", lang=lang, user_id=uid),
                    f"menu:admin:tracking:stop:{uid}",
                    "danger",
                )
            ]
        )
    rows.append(
        [_btn(t("admin_tracking_refresh_button", lang=lang), "menu:admin:tracking:refresh", "primary")]
    )
    rows.append([_btn(t("back_button", lang=lang), "back:admin", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_method_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("fast_method_button", lang=lang), "menu:admin:method:fast", "primary")],
            [
                _btn(
                    t("powerful_method_openrouter_button", lang=lang),
                    "menu:admin:method:openrouter",
                    "success",
                )
            ],
            [
                _btn(
                    t("powerful_method_groq_button", lang=lang),
                    "menu:admin:method:groq",
                    "success",
                )
            ],
            [_btn(t("back_button", lang=lang), "back:admin", "danger")],
        ]
    )
