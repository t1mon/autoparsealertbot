"""Inline keyboards for user UI."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.membership_status import membership_badge
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
    ready: bool | None = None,
    is_admin: bool = False,
    user_id: int | None = None,
) -> InlineKeyboardMarkup:
    from keyboards.admin.keyboards import main_admin_keyboard, main_menu_keyboard

    if ready is None and user_id is not None:
        from handlers.user.menu_helpers import is_parsing_ready

        ready = is_parsing_ready(user_id)
    if ready is None:
        ready = False

    if is_admin:
        return main_admin_keyboard(lang=lang, tracking_active=tracking_active, ready=ready)
    return main_menu_keyboard(lang=lang, tracking_active=tracking_active, ready=ready)


def ai_search_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("ai_search_button_user", lang=lang), "menu:ai:user", "primary")],
            [_btn(t("global_ai_search_button", lang=lang), "menu:ai:global", "primary")],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def cabinet_keyboard(lang: str = "ru", ready: bool = True) -> InlineKeyboardMarkup:
    """Экран «Мой парсинг»: сущности парсинга (без дубля «Настройки»)."""
    rows: list[list[InlineKeyboardButton]] = []
    if not ready:
        rows.append([_btn(t("wizard_continue_button", lang=lang), "menu:wizard", "success")])
    rows.extend(
        [
            [_btn(t("cabinet_account_button", lang=lang), "menu:accounts", "success")],
            [_btn(t("keywords_menu_button", lang=lang), "menu:keywords", "primary")],
            [_btn(t("channels_menu_button", lang=lang), "menu:channels", "primary")],
            [_btn(t("leads_menu_button", lang=lang), "menu:leads", "primary")],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def wizard_keyboard(lang: str = "ru", step: str = "account") -> InlineKeyboardMarkup:
    """CTA текущего шага онбординга."""
    rows: list[list[InlineKeyboardButton]] = []
    if step == "account":
        rows.append([_btn(t("wizard_cta_account", lang=lang), "menu:wizard:account", "success")])
    elif step == "keywords":
        rows.append([_btn(t("wizard_cta_keywords", lang=lang), "menu:wizard:keywords", "success")])
    elif step == "channels":
        rows.append([_btn(t("wizard_cta_channels", lang=lang), "menu:wizard:channels", "success")])
    elif step == "ready":
        rows.append([_btn(t("launch_tracking_button", lang=lang), "menu:tracking:start", "success")])
    rows.append([_btn(t("wizard_skip_button", lang=lang), "back:main", "primary")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def after_setup_keyboard(lang: str, user_id: int, fallback: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """После добавления сущности — предложить продолжить wizard, если ещё не ready."""
    from handlers.user.menu_helpers import get_wizard_step

    step = get_wizard_step(user_id)
    if step == "ready":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [_btn(t("launch_tracking_button", lang=lang), "menu:tracking:start", "success")],
                *fallback.inline_keyboard,
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("wizard_continue_button", lang=lang), "menu:wizard", "success")],
            *fallback.inline_keyboard,
        ]
    )


def accounts_menu_keyboard(lang: str = "ru", accounts: list[dict] | None = None) -> InlineKeyboardMarkup:
    """Список аккаунтов: ● активный / ○ выбрать; ✕ удалить."""
    rows: list[list[InlineKeyboardButton]] = []
    for acc in accounts or []:
        phone = (acc.get("phone_number") or "?").strip() or "?"
        label = phone if len(phone) <= 22 else phone[:19] + "…"
        mark = "●" if acc.get("is_active") else "○"
        rows.append(
            [
                _btn(f"{mark} {label}", f"menu:accounts:set:{acc['id']}", "primary"),
                _btn("✕", f"menu:accounts:del:{acc['id']}", "danger"),
            ]
        )
    rows.append([_btn(t("accounts_connect_button", lang=lang), "menu:accounts:connect", "success")])
    if accounts:
        rows.append([_btn(t("accounts_check_button", lang=lang), "menu:accounts:check", "primary")])
    rows.append([_btn(t("back_button", lang=lang), "back:cabinet", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def keywords_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("keywords_add_button", lang=lang), "menu:keywords:add", "success")],
            [_btn(t("keywords_view_list_button", lang=lang), "menu:keywords:list", "primary")],
            [_btn(t("match_mode_button", lang=lang), "menu:match_mode", "primary")],
            [_btn(t("match_check_button", lang=lang), "menu:keywords:check", "primary")],
            [_btn(t("stopwords_menu_button", lang=lang), "menu:stopwords", "primary")],
            [
                _btn(t("keywords_export_txt_button", lang=lang), "menu:keywords:export:txt", "primary"),
                _btn(t("keywords_export_xlsx_button", lang=lang), "menu:keywords:export:xlsx", "primary"),
            ],
            [_btn(t("back_button", lang=lang), "back:cabinet", "danger")],
        ]
    )


def match_mode_keyboard(lang: str = "ru", current: str = "smart") -> InlineKeyboardMarkup:
    def mark(mode: str, label_key: str) -> str:
        prefix = "● " if mode == current else "○ "
        return prefix + t(label_key, lang=lang)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(mark("strict", "match_mode_strict_button"), "menu:match_mode:strict", "primary")],
            [_btn(mark("smart", "match_mode_smart_button"), "menu:match_mode:smart", "success")],
            [_btn(mark("loose", "match_mode_loose_button"), "menu:match_mode:loose", "primary")],
            [_btn(t("back_button", lang=lang), "back:keywords", "danger")],
        ]
    )


def keywords_list_keyboard(
    lang: str,
    items: list[tuple[int, str]],
    page: int,
    total: int,
    page_size: int = 10,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for kw_id, text in items:
        label = text if len(text) <= 28 else text[:25] + "…"
        rows.append(
            [
                _btn(f"✕ {label}", f"menu:keywords:del:{kw_id}:{page}", "danger"),
            ]
        )

    max_page = max(0, (total - 1) // page_size) if total else 0
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("⬅️", f"menu:keywords:page:{page - 1}"))
    if page < max_page:
        nav.append(_btn("➡️", f"menu:keywords:page:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn(t("back_button", lang=lang), "back:keywords", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channels_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("channels_add_button", lang=lang), "menu:channels:add", "success")],
            [_btn(t("channels_view_list_button", lang=lang), "menu:channels:list", "primary")],
            [_btn(t("channels_check_subs_button", lang=lang), "menu:channels:check_subs", "primary")],
            [
                _btn(t("channels_export_txt_button", lang=lang), "menu:channels:export:txt", "primary"),
                _btn(t("channels_export_xlsx_button", lang=lang), "menu:channels:export:xlsx", "primary"),
            ],
            [_btn(t("channels_clear_button", lang=lang), "menu:channels:clear", "danger")],
            [_btn(t("back_button", lang=lang), "back:cabinet", "danger")],
        ]
    )


def channels_list_keyboard(
    lang: str,
    items: list[dict],
    page: int,
    total: int,
    page_size: int = 8,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in items:
        username = item["username"] or ""
        label = username if len(username) <= 16 else username[:13] + "…"
        toggle_text = "✅" if item["parse_enabled"] else "⏸"
        sub_badge = membership_badge(item.get("membership_status"))
        prefix = f"{sub_badge} " if sub_badge else ""
        rows.append(
            [
                _btn(f"{toggle_text} {prefix}{label}", f"menu:channels:toggle:{item['id']}:{page}", "primary"),
                _btn("✕", f"menu:channels:del:{item['id']}:{page}", "danger"),
            ]
        )

    max_page = max(0, (total - 1) // page_size) if total else 0
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("⬅️", f"menu:channels:page:{page - 1}"))
    if page < max_page:
        nav.append(_btn("➡️", f"menu:channels:page:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn(t("back_button", lang=lang), "back:channels", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channels_check_subs_keyboard(lang: str, *, can_join: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if can_join:
        rows.append(
            [_btn(t("channels_join_missing_button", lang=lang), "menu:channels:join_missing", "success")]
        )
    rows.append([_btn(t("channels_check_subs_button", lang=lang), "menu:channels:check_subs", "primary")])
    rows.append([_btn(t("back_button", lang=lang), "back:channels", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channels_join_progress_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(t("channels_join_cancel_button", lang=lang), "menu:channels:join_cancel", "danger"),
                _btn(t("back_button", lang=lang), "back:channels", "danger"),
            ]
        ]
    )


def channels_join_cancel_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(t("channels_join_cancel_yes", lang=lang), "menu:channels:join_cancel:yes", "danger"),
                _btn(t("cancel_btn", lang=lang), "menu:channels:join_cancel:no", "primary"),
            ]
        ]
    )


def leads_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("leads_view_list_button", lang=lang), "menu:leads:list", "primary")],
            [_btn(t("leads_export_xlsx_button", lang=lang), "menu:leads:export:xlsx", "primary")],
            [_btn(t("back_button", lang=lang), "back:cabinet", "danger")],
        ]
    )


def leads_list_keyboard(
    lang: str,
    items: list[tuple[int, str]],
    page: int,
    total: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for lead_id, keyword in items:
        label = keyword if len(keyword) <= 28 else keyword[:25] + "…"
        rows.append([_btn(f"📄 {label}", f"menu:leads:view:{lead_id}:{page}", "primary")])

    max_page = max(0, (total - 1) // page_size) if total else 0
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("⬅️", f"menu:leads:page:{page - 1}"))
    if page < max_page:
        nav.append(_btn("➡️", f"menu:leads:page:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn(t("back_button", lang=lang), "back:leads", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Прочее: фильтры алертов, язык, stars (сущности — в «Мой парсинг»)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("quiet_hours_button", lang=lang), "menu:quiet_hours", "primary")],
            [_btn(t("digest_button", lang=lang), "menu:digest", "primary")],
            [_btn(t("chat_filter_button", lang=lang), "menu:chat_filter", "primary")],
            [_btn(t("alert_template_button", lang=lang), "menu:alert_template", "primary")],
            [_btn(t("alert_destination_button", lang=lang), "menu:alert_destination", "primary")],
            [
                _btn(t("change_language_button", lang=lang), "menu:settings:change_lang", "primary"),
                _btn(t("topup_stars_button", lang=lang), "menu:settings:stars", "primary"),
            ],
            [_btn(t("back_button", lang=lang), "back:main", "danger")],
        ]
    )


def quiet_hours_keyboard(
    lang: str,
    *,
    enabled: bool,
    start: int,
    end: int,
) -> InlineKeyboardMarkup:
    toggle = (
        t("quiet_hours_disable_button", lang=lang)
        if enabled
        else t("quiet_hours_enable_button", lang=lang)
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(toggle, "menu:quiet_hours:toggle", "success" if not enabled else "danger")],
            [
                _btn(t("quiet_hours_preset_2308", lang=lang), "menu:quiet_hours:preset:23:8", "primary"),
                _btn(t("quiet_hours_preset_0007", lang=lang), "menu:quiet_hours:preset:0:7", "primary"),
            ],
            [
                _btn(t("quiet_hours_preset_2209", lang=lang), "menu:quiet_hours:preset:22:9", "primary"),
            ],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def digest_keyboard(lang: str, *, enabled: bool, interval_min: int) -> InlineKeyboardMarkup:
    toggle = (
        t("digest_disable_button", lang=lang)
        if enabled
        else t("digest_enable_button", lang=lang)
    )

    def mark(minutes: int, label_key: str) -> str:
        prefix = "● " if minutes == interval_min else "○ "
        return prefix + t(label_key, lang=lang)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(toggle, "menu:digest:toggle", "success" if not enabled else "danger")],
            [
                _btn(mark(15, "digest_interval_15"), "menu:digest:interval:15", "primary"),
                _btn(mark(30, "digest_interval_30"), "menu:digest:interval:30", "primary"),
                _btn(mark(60, "digest_interval_60"), "menu:digest:interval:60", "primary"),
            ],
            [_btn(t("digest_flush_now_button", lang=lang), "menu:digest:flush", "primary")],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def chat_filter_keyboard(lang: str, current: str = "all") -> InlineKeyboardMarkup:
    def mark(mode: str, label_key: str) -> str:
        prefix = "● " if mode == current else "○ "
        return prefix + t(label_key, lang=lang)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(mark("all", "chat_filter_all_button"), "menu:chat_filter:all", "success")],
            [_btn(mark("channels", "chat_filter_channels_button"), "menu:chat_filter:channels", "primary")],
            [_btn(mark("groups", "chat_filter_groups_button"), "menu:chat_filter:groups", "primary")],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def alert_template_keyboard(lang: str, current: str = "full") -> InlineKeyboardMarkup:
    def mark(mode: str, label_key: str) -> str:
        prefix = "● " if mode == current else "○ "
        return prefix + t(label_key, lang=lang)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(mark("full", "alert_template_full_button"), "menu:alert_template:full", "success")],
            [
                _btn(
                    mark("compact", "alert_template_compact_button"),
                    "menu:alert_template:compact",
                    "primary",
                )
            ],
            [
                _btn(
                    mark("minimal", "alert_template_minimal_button"),
                    "menu:alert_template:minimal",
                    "primary",
                )
            ],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def alert_destination_keyboard(
    lang: str,
    *,
    alert_to_dm: bool,
    alert_to_group: bool,
    group_bound: bool,
) -> InlineKeyboardMarkup:
    dm_label = ("✅ " if alert_to_dm else "⬜ ") + t("alert_destination_dm_button", lang=lang)
    group_label = ("✅ " if alert_to_group else "⬜ ") + t("alert_destination_group_button", lang=lang)
    rows = [
        [_btn(dm_label, "menu:alert_destination:toggle_dm", "success" if alert_to_dm else "primary")],
        [_btn(group_label, "menu:alert_destination:toggle_group", "success" if alert_to_group else "primary")],
    ]
    if alert_to_group:
        if group_bound:
            rows.append(
                [_btn(t("alert_destination_rebind_button", lang=lang), "menu:alert_destination:bind", "primary")]
            )
            rows.append(
                [_btn(t("alert_destination_unbind_button", lang=lang), "menu:alert_destination:unbind", "danger")]
            )
        else:
            rows.append(
                [_btn(t("alert_destination_bind_button", lang=lang), "menu:alert_destination:bind", "primary")]
            )
    rows.append([_btn(t("back_button", lang=lang), "back:settings", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alert_destination_bind_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("alert_destination_bind_ready_button", lang=lang), "menu:alert_destination:bind_ready", "success")],
            [_btn(t("back_button", lang=lang), "back:alert_destination", "danger")],
        ]
    )


def stopwords_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("stopwords_add_button", lang=lang), "menu:stopwords:add", "success")],
            [_btn(t("stopwords_view_list_button", lang=lang), "menu:stopwords:list", "primary")],
            [_btn(t("back_button", lang=lang), "back:settings", "danger")],
        ]
    )


def stopwords_list_keyboard(
    lang: str,
    items: list[tuple[int, str]],
    page: int,
    total: int,
    page_size: int = 10,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for sw_id, text in items:
        label = text if len(text) <= 28 else text[:25] + "…"
        rows.append([_btn(f"✕ {label}", f"menu:stopwords:del:{sw_id}:{page}", "danger")])

    max_page = max(0, (total - 1) // page_size) if total else 0
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(_btn("⬅️", f"menu:stopwords:page:{page - 1}"))
    if page < max_page:
        nav.append(_btn("➡️", f"menu:stopwords:page:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn(t("back_button", lang=lang), "back:stopwords", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def connect_keyboard_account(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn(t("connect_account_button", lang=lang), "menu:accounts:connect", "success")],
            [_btn(t("back_button", lang=lang), "back:accounts", "danger")],
        ]
    )


def back_keyboard(lang: str = "ru", callback_data: str = "back:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_btn(t("back_button", lang=lang), callback_data, "danger")]]
    )


def instruction_keyboard(lang: str = "ru", *, ready: bool = True) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [_btn(t("instruction_ask_button", lang=lang), "menu:instruction:ask", "primary")],
    ]
    if not ready:
        rows.append([_btn(t("wizard_continue_button", lang=lang), "menu:wizard", "success")])
    rows.append([_btn(t("back_button", lang=lang), "back:main", "danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alert_actions_keyboard(
    lang: str,
    *,
    url: str | None = None,
    chat_id: int | None = None,
) -> InlineKeyboardMarkup | None:
    """Кнопки под алертом: Открыть (url) + Игнор канала 24ч."""
    rows: list[list[InlineKeyboardButton]] = []
    if url and str(url).startswith("http"):
        rows.append([InlineKeyboardButton(text=t("alert_open_button", lang=lang), url=str(url))])
    if chat_id is not None:
        rows.append(
            [
                _btn(
                    t("alert_mute_24h_button", lang=lang),
                    f"alert:mute:{int(chat_id)}",
                    "danger",
                )
            ]
        )
    if not rows:
        return None
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alert_open_keyboard(lang: str, url: str) -> InlineKeyboardMarkup | None:
    """Обратная совместимость — только «Открыть»."""
    return alert_actions_keyboard(lang, url=url)


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

