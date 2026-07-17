import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("ID")
API_HASH = os.getenv("HASH")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
POLZA_AI_API_KEY = os.getenv("POLZA_AI_API_KEY")

PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_IP = os.getenv("PROXY_IP")

WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").strip()
ENABLE_MOCK_AUTH = os.getenv("ENABLE_MOCK_AUTH", "false").lower() in ("1", "true", "yes")

BOT_MODE = (os.getenv("BOT_MODE") or "polling").lower().strip()
WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or "").strip()
WEBHOOK_SECRET = (os.getenv("WEBHOOK_SECRET") or "").strip()


def _parse_webhook_path(webhook_url: str) -> str:
    from urllib.parse import urlparse

    path = urlparse(webhook_url).path
    return path if path else "/webhook/telegram"


WEBHOOK_PATH = _parse_webhook_path(WEBHOOK_URL) if WEBHOOK_URL else "/webhook/telegram"


def _parse_admin_user_ids(raw: str | None) -> frozenset[int]:
    if not raw or not raw.strip():
        return frozenset()
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"ADMIN_USER_IDS: неверный ID '{part}' (ожидается число)")
        ids.add(int(part))
    return frozenset(ids)


ADMIN_USER_IDS = _parse_admin_user_ids(os.getenv("ADMIN_USER_IDS"))

_allowed_raw = os.getenv("ALLOWED_USER_IDS")
ALLOWED_USER_IDS = (
    _parse_admin_user_ids(_allowed_raw) if _allowed_raw and _allowed_raw.strip() else ADMIN_USER_IDS
)

CLOSED_BETA = (os.getenv("CLOSED_BETA") or "true").lower() in ("1", "true", "yes")

_developer = (os.getenv("DEVELOPER_USERNAME") or "cheef_engineer").strip().lstrip("@")
DEVELOPER_USERNAME = _developer or "cheef_engineer"
DEVELOPER_CONTACT_URL = f"https://t.me/{DEVELOPER_USERNAME}"


def _parse_port(raw: str | None) -> int:
    if not raw or not raw.strip().isdigit():
        return 8000
    return int(raw.strip())


PORT = _parse_port(os.getenv("PORT"))


def _parse_cors_origins(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


CORS_ORIGINS = _parse_cors_origins(os.getenv("CORS_ORIGINS"))

REDIS_URL = (os.getenv("REDIS_URL") or "").strip()


def _parse_positive_int(raw: str | None, default: int) -> int:
    if not raw or not str(raw).strip().isdigit():
        return default
    return max(1, int(str(raw).strip()))


def _parse_nonneg_int(raw: str | None, default: int) -> int:
    if raw is None or not str(raw).strip():
        return default
    if not str(raw).strip().isdigit():
        return default
    return max(0, int(str(raw).strip()))


# Антибан при массовых JoinChannel (секунды / лимиты)
JOIN_DELAY_MIN = _parse_positive_int(os.getenv("JOIN_DELAY_MIN"), 20)
JOIN_DELAY_MAX = _parse_positive_int(os.getenv("JOIN_DELAY_MAX"), 45)
if JOIN_DELAY_MAX < JOIN_DELAY_MIN:
    JOIN_DELAY_MAX = JOIN_DELAY_MIN
JOIN_ERROR_DELAY_MIN = _parse_positive_int(os.getenv("JOIN_ERROR_DELAY_MIN"), 10)
JOIN_ERROR_DELAY_MAX = _parse_positive_int(os.getenv("JOIN_ERROR_DELAY_MAX"), 25)
if JOIN_ERROR_DELAY_MAX < JOIN_ERROR_DELAY_MIN:
    JOIN_ERROR_DELAY_MAX = JOIN_ERROR_DELAY_MIN
JOIN_BATCH_LIMIT = _parse_positive_int(os.getenv("JOIN_BATCH_LIMIT"), 40)
JOIN_DAILY_LIMIT = _parse_positive_int(os.getenv("JOIN_DAILY_LIMIT"), 80)
# 0 = не слать промежуточные «подписался на …»; иначе каждые N новых join (+ первый)
JOIN_NOTIFY_EVERY = _parse_nonneg_int(os.getenv("JOIN_NOTIFY_EVERY"), 5)

# Logging (как в bedolaga)
LOG_LEVEL = (os.getenv("LOG_LEVEL") or "INFO").strip()
LOG_FILE = (os.getenv("LOG_FILE") or "logs/bot.log").strip()
LOG_DIR = (os.getenv("LOG_DIR") or "logs").strip()
LOG_COLORS = (os.getenv("LOG_COLORS") or "true").lower() in ("1", "true", "yes")
LOG_ROTATION_ENABLED = (os.getenv("LOG_ROTATION_ENABLED") or "false").lower() in ("1", "true", "yes")
LOG_INFO_FILE = (os.getenv("LOG_INFO_FILE") or "info.log").strip()
LOG_WARNING_FILE = (os.getenv("LOG_WARNING_FILE") or "warning.log").strip()
LOG_ERROR_FILE = (os.getenv("LOG_ERROR_FILE") or "error.log").strip()
TIMEZONE = (os.getenv("TIMEZONE") or os.getenv("TZ") or "UTC").strip()


def validate_config() -> None:
    errors: list[str] = []

    if not BOT_TOKEN or BOT_TOKEN.strip() in ("", "_____"):
        errors.append("BOT_TOKEN не задан")
    if not API_ID or API_ID.strip() in ("", "_____"):
        errors.append("ID (API_ID) не задан")
    if not API_HASH or API_HASH.strip() in ("", "_____"):
        errors.append("HASH (API_HASH) не задан")
    if not ADMIN_USER_IDS:
        errors.append("ADMIN_USER_IDS не задан или пуст")

    if BOT_MODE not in ("polling", "webhook"):
        errors.append("BOT_MODE должен быть 'polling' или 'webhook'")

    if BOT_MODE == "webhook":
        if not WEBHOOK_URL:
            errors.append("WEBHOOK_URL обязателен при BOT_MODE=webhook")
        elif not WEBHOOK_URL.startswith("https://"):
            errors.append("WEBHOOK_URL должен начинаться с https://")

    if errors:
        print("Ошибка конфигурации (.env):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("\nСкопируйте .env.example в .env и заполните обязательные поля.", file=sys.stderr)
        sys.exit(1)
