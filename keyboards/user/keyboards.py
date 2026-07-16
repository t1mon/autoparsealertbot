"""Inline keyboards for user UI."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales.locales import t

CATEGORY_KEYS = (
    "investments_button",
    "finance_and_personal_budget_button",
    "crypto_and_blockchain_button",
    "business_and_entrepreneurship_button",
    "marketing_and_promotion_button",
    "tech_and_it_button",
    "education_and_self_development_button",
    "work_and_career_button",
    "real_estate_button",
    "health_and_medicine_button",
    "travel_button",
    "auto_and_transport_button",
    "shopping_and_discounts_button",
    "entertainment_and_leisure_button",
    "politics_and_society_button",
    "science_and_research_button",
    "sports_and_fitness_button",
    "cooking_and_food_button",
    "fashion_and_beauty_button",
    "hobbies_and_creativity_button",
)

CATEGORIES_PER_PAGE = 8


def _btn(text: str, callback_data: str, style: str | None = None) -> InlineKeyboardButton:
    kwargs: dict = {"text": text, "callback_data": callback_data}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(**kwargs)


def search_group_ai(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("all_database_button", lang=lang), "menu:database:all", "primary")],
            [
                _btn(t("channels_database_button", lang=lang), "menu:database:channels", "primary"),
                _btn(t("groups_database_button", lang=lang), "menu:database:groups", "primary"),
            ],
            [_btn(t("select_category_button", lang=lang), "menu:database:category", "primary")],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def get_categories_keyboard(lang: str = "ru", page: int = 0) -> InlineKeyboardMarkup:
    total = len(CATEGORY_KEYS)
    start = page * CATEGORIES_PER_PAGE
    end = min(start + CATEGORIES_PER_PAGE, total)
    rows: list[list[InlineKeyboardButton]] = []

    for key in CATEGORY_KEYS[start:end]:
        rows.append([_btn(t(key, lang=lang), f"menu:cat:{key}", "primary")])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("⬅️", f"menu:catpage:{page - 1}"))
    if end < total:
        nav.append(_btn("➡️", f"menu:catpage:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn(t("back_button", lang=lang), "back:database", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_lang_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(t("russian_language_button", lang=lang), "menu:lang:ru", "primary"),
                _btn(t("english_language_button", lang=lang), "menu:lang:en", "primary"),
            ]
        ]
    )


def resolve_main_keyboard(
    lang: str,
    *,
    tracking_active: bool = False,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    from keyboards.admin.keyboards import main_admin_keyboard, main_menu_keyboard

    if is_admin:
        return main_admin_keyboard(lang=lang, tracking_active=tracking_active)
    return main_menu_keyboard(lang=lang, tracking_active=tracking_active)


def ai_search_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("ai_search_button_user", lang=lang), "menu:ai:user", "primary")],
            [_btn(t("global_ai_search_button", lang=lang), "menu:ai:global", "primary")],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def settings_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(t("update_list_button", lang=lang), "menu:settings:update_list", "primary"),
                _btn(t("enter_keyword_button", lang=lang), "menu:settings:enter_keyword", "primary"),
            ],
            [
                _btn(t("delete_group_from_tracking_button", lang=lang), "menu:settings:delete_group", "danger"),
                _btn(t("clear_all_tracked_channels_button", lang=lang), "menu:settings:clear_channels", "danger"),
            ],
            [
                _btn(t("keywords_list_button", lang=lang), "menu:settings:keywords", "primary"),
                _btn(t("tracking_links_button", lang=lang), "menu:settings:links", "primary"),
            ],
            [_btn(t("connect_account_button", lang=lang), "menu:settings:connect_account", "success")],
            [
                _btn(t("change_language_button", lang=lang), "menu:settings:change_lang", "primary"),
                _btn(t("topup_stars_button", lang=lang), "menu:settings:stars", "primary"),
            ],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def connect_keyboard_account(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("connect_account_button", lang=lang), "menu:connect:account", "success")],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def back_keyboard(lang: str = "ru", callback_data: str = "back:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_btn(t("back_button", lang=lang), callback_data, "danger")]]
    )


def clear_all_channels_confirm_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("confirm_btn", lang=lang),
                    callback_data="clear_channels_confirm",
                ),
                InlineKeyboardButton(
                    text=t("cancel_btn", lang=lang),
                    callback_data="clear_channels_cancel",
                ),
            ]
        ]
    )


def get_stars_topup_inline_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 5 Stars", callback_data="buy_stars_5"),
                InlineKeyboardButton(text="⭐ 15 Stars", callback_data="buy_stars_15"),
            ],
            [
                InlineKeyboardButton(text="⭐ 50 Stars", callback_data="buy_stars_50"),
                InlineKeyboardButton(text="⭐ 100 Stars", callback_data="buy_stars_100"),
            ],
            [
                InlineKeyboardButton(
                    text=t("back_button", lang=lang),
                    callback_data="menu:settings",
                )
            ],
        ]
    )

