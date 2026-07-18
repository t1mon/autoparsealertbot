import os
from datetime import datetime

from asgiref.sync import sync_to_async
import structlog

logger = structlog.get_logger(__name__)

from core.telegram_utils import normalize_telegram_chat_ref, normalize_telegram_username
from peewee import (
    SqliteDatabase, IntegerField, AutoField, TextField, DateTimeField, Model, CharField, BooleanField, DoesNotExist, fn
)

DB_PATH = "data/bot.db"

db = SqliteDatabase(
    DB_PATH, timeout=30,
    pragmas={'journal_mode': 'wal', 'cache_size': 4096, 'synchronous': 'NORMAL'},
    autocommit=True  # ✅ Важно!
)


class BaseModel(Model):
    class Meta:
        database = db


def init_database():
    """Инициализация БД и создание таблиц"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db.connect(reuse_if_open=True)
    db.create_tables([Account], safe=True)  # Создание таблицы аккаунтов
    db.create_tables([AccountFree], safe=True)  # Создание таблицы аккаунтов для подключения (свободных)
    db.create_tables([UserAccountsTable], safe=True)  # Создание таблицы аккаунтов пользователя
    db.create_tables([Groups], safe=True)  # Создание таблицы с группами пользователей
    db.create_tables([TelegramGroup], safe=True)  # Создание таблицы Telegram-групп
    db.create_tables([Question], safe=True)  # Создание таблицы вопросов пользователей для расширения базы знаний
    db.create_tables([User], safe=True)  # Создание таблицы пользователей
    db.create_tables([Lead], safe=True)  # Совпадения по ключевым словам (лиды)
    db.create_tables([StopWord], safe=True)  # Стоп-слова (чёрный список)

    # Проверка наличия колонок stars и last_free_download_at в таблице user (SQLite-миграция)
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]
    if "stars" not in columns:
        logger.info("Migrating database: adding 'stars' column to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "stars" INTEGER DEFAULT 0;')
    if "last_free_download_at" not in columns:
        logger.info("Migrating database: adding 'last_free_download_at' column to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "last_free_download_at" DATETIME;')
    if "match_mode" not in columns:
        logger.info("Migrating database: adding 'match_mode' column to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "match_mode" VARCHAR(16) DEFAULT \'smart\';')
    db.execute_sql('UPDATE "user" SET "match_mode" = \'smart\' WHERE "match_mode" IS NULL OR "match_mode" = \'\';')
    if "quiet_hours_enabled" not in columns:
        logger.info("Migrating database: adding quiet hours columns to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "quiet_hours_enabled" INTEGER DEFAULT 0;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "quiet_hours_start" INTEGER DEFAULT 23;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "quiet_hours_end" INTEGER DEFAULT 8;')
    db.execute_sql(
        'UPDATE "user" SET "quiet_hours_enabled" = 0 WHERE "quiet_hours_enabled" IS NULL;'
    )
    db.execute_sql(
        'UPDATE "user" SET "quiet_hours_start" = 23 WHERE "quiet_hours_start" IS NULL;'
    )
    db.execute_sql(
        'UPDATE "user" SET "quiet_hours_end" = 8 WHERE "quiet_hours_end" IS NULL;'
    )
    if "digest_enabled" not in columns:
        logger.info("Migrating database: adding digest columns to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "digest_enabled" INTEGER DEFAULT 0;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "digest_interval_min" INTEGER DEFAULT 60;')
    db.execute_sql(
        'UPDATE "user" SET "digest_enabled" = 0 WHERE "digest_enabled" IS NULL;'
    )
    db.execute_sql(
        'UPDATE "user" SET "digest_interval_min" = 60 WHERE "digest_interval_min" IS NULL;'
    )
    if "chat_filter" not in columns:
        logger.info("Migrating database: adding 'chat_filter' column to user table")
        db.execute_sql(
            'ALTER TABLE "user" ADD COLUMN "chat_filter" VARCHAR(16) DEFAULT \'all\';'
        )
    db.execute_sql(
        'UPDATE "user" SET "chat_filter" = \'all\' WHERE "chat_filter" IS NULL OR "chat_filter" = \'\';'
    )
    if "alert_template" not in columns:
        logger.info("Migrating database: adding 'alert_template' column to user table")
        db.execute_sql(
            'ALTER TABLE "user" ADD COLUMN "alert_template" VARCHAR(16) DEFAULT \'full\';'
        )
    db.execute_sql(
        'UPDATE "user" SET "alert_template" = \'full\' '
        'WHERE "alert_template" IS NULL OR "alert_template" = \'\';'
    )
    if "alert_to_dm" not in columns:
        logger.info("Migrating database: adding alert destination columns to user table")
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "alert_to_dm" INTEGER DEFAULT 1;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "alert_to_group" INTEGER DEFAULT 0;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "alert_chat_id" INTEGER;')
        db.execute_sql('ALTER TABLE "user" ADD COLUMN "alert_thread_id" INTEGER;')
    db.execute_sql('UPDATE "user" SET "alert_to_dm" = 1 WHERE "alert_to_dm" IS NULL;')
    db.execute_sql('UPDATE "user" SET "alert_to_group" = 0 WHERE "alert_to_group" IS NULL;')
    if "author_filter" not in columns:
        logger.info("Migrating database: adding 'author_filter' column to user table")
        db.execute_sql(
            'ALTER TABLE "user" ADD COLUMN "author_filter" VARCHAR(16) DEFAULT \'humans\';'
        )
    db.execute_sql(
        'UPDATE "user" SET "author_filter" = \'humans\' '
        'WHERE "author_filter" IS NULL OR "author_filter" = \'\';'
    )

    cursor.execute("PRAGMA table_info(leads)")
    lead_columns = [row[1] for row in cursor.fetchall()]
    if lead_columns and "author_kind" not in lead_columns:
        logger.info("Migrating database: adding 'author_kind' column to leads")
        db.execute_sql(
            'ALTER TABLE "leads" ADD COLUMN "author_kind" VARCHAR(32) DEFAULT \'anonymous\';'
        )
    if lead_columns:
        db.execute_sql(
            'UPDATE "leads" SET "author_kind" = \'anonymous\' '
            'WHERE "author_kind" IS NULL OR "author_kind" = \'\';'
        )

    cursor.execute("PRAGMA table_info(users_groups)")
    group_columns = [row[1] for row in cursor.fetchall()]
    if "parse_enabled" not in group_columns:
        logger.info("Migrating database: adding 'parse_enabled' column to users_groups")
        db.execute_sql('ALTER TABLE "users_groups" ADD COLUMN "parse_enabled" INTEGER DEFAULT 1;')
    db.execute_sql('UPDATE "users_groups" SET "parse_enabled" = 1 WHERE "parse_enabled" IS NULL;')
    if "membership_status" not in group_columns:
        logger.info("Migrating database: adding 'membership_status' column to users_groups")
        db.execute_sql('ALTER TABLE "users_groups" ADD COLUMN "membership_status" VARCHAR(16) DEFAULT \'\';')
    db.execute_sql(
        'UPDATE "users_groups" SET "membership_status" = \'\' '
        'WHERE "membership_status" IS NULL;'
    )

    cursor.execute("PRAGMA table_info(user_accounts_table)")
    account_columns = [row[1] for row in cursor.fetchall()]
    if "is_active" not in account_columns:
        logger.info("Migrating database: adding 'is_active' column to user_accounts_table")
        db.execute_sql(
            'ALTER TABLE "user_accounts_table" ADD COLUMN "is_active" INTEGER DEFAULT 0;'
        )
    _ensure_one_active_account_per_user()

    db.close()


def _ensure_one_active_account_per_user() -> None:
    """Если у пользователя есть аккаунты, но нет активного — активируем первый."""
    try:
        user_ids = [
            row.user_id
            for row in UserAccountsTable.select(UserAccountsTable.user_id).distinct()
        ]
        for uid in user_ids:
            active = (
                UserAccountsTable.select()
                .where(
                    (UserAccountsTable.user_id == uid)
                    & (UserAccountsTable.is_active == True)  # noqa: E712
                )
                .count()
            )
            if active > 0:
                continue
            first = (
                UserAccountsTable.select()
                .where(UserAccountsTable.user_id == uid)
                .order_by(UserAccountsTable.id.asc())
                .first()
            )
            if first:
                first.is_active = True
                first.save()
    except Exception as e:
        logger.exception("ensure_active_account_migration_error", error=e)


"""
Запись в базу данных вопросов пользователей, что бы расширить базу знаний
"""


class Question(BaseModel):
    id = AutoField()  # автоинкремент
    user_id = IntegerField()  # ID пользователя Telegram
    question = TextField()  # Вопрос пользователя
    answer = TextField(null=True)  # Ответ на вопрос


def add_question(user_id: int, question: str, answer: str):
    """
    Добавляет вопрос в базу данных.

    :param user_id: Telegram ID пользователя
    :param question: Вопрос пользователя
    :param answer: Ответ на вопрос
    :return: True, если вопрос добавлен, иначе False
    """
    Question.create(user_id=user_id, question=question, answer=answer)
    return True


def get_all_questions():
    """
    Получает все вопросы и ответы из базы данных.

    :return: Список словарей с вопросами и ответами
    """
    try:
        questions = Question.select()
        result = [
            {
                'user_id': q.user_id,
                'question': q.question,
                'answer': q.answer
            }
            for q in questions
        ]
        return result
    except Exception as e:
        logger.exception(f"❌ Ошибка получения всех вопросов: {e}")
        return []


"""
Работа с группами пользователя для отслеживания ключевых слов. Все данные пользователей хранится в одной таблице, 
для удобства масштабирования
"""


class Groups(BaseModel):
    id = AutoField()  # автоинкремент
    user_id = IntegerField()  # ID пользователя Telegram
    username = CharField(null=True)  # Username пользователя Telegram
    date_added = DateTimeField(default=datetime.now)  # Дата добавления группы
    parse_enabled = BooleanField(default=True)  # Парсить этот канал
    membership_status = CharField(max_length=16, default="")  # ok | missing | pending | private | error

    class Meta:
        table_name = f"users_groups"  # Имя таблицы
        indexes = (
            (("user_id", "username"), True),  # один пользователь не добавит один канал дважды
        )


def dell_group(user_id: int, username: str):
    """
    Удаляет группу из отслеживания ключевых слов.

    :param user_id: Telegram ID пользователя
    :param username: Username группы
    :return: True, если группа удалена, иначе False
    """
    try:
        deleted = (
            Groups.delete().where(Groups.user_id == user_id, Groups.username == username).execute()
        )
        return deleted > 0
    except Exception as e:
        logger.exception("database_init_error", error=e)
        return False


def delete_group_by_id(user_id: int, group_id: int) -> str | None:
    """Удаляет канал по id. Возвращает username удалённой записи или None."""
    try:
        row = Groups.get_or_none(Groups.id == group_id, Groups.user_id == user_id)
        if not row:
            return None
        username = row.username
        row.delete_instance()
        return username
    except Exception as e:
        logger.exception("database_delete_group_error", error=e)
        return None


def set_group_parse_enabled(user_id: int, group_id: int, enabled: bool) -> bool:
    try:
        updated = (
            Groups.update(parse_enabled=enabled)
            .where(Groups.id == group_id, Groups.user_id == user_id)
            .execute()
        )
        return updated > 0
    except Exception as e:
        logger.exception("database_toggle_group_error", error=e)
        return False


def set_group_membership_by_ref(user_id: int, channel_ref: str, status: str) -> None:
    """Обновляет membership_status для канала пользователя (по канонической ссылке)."""
    from core.telegram_utils import normalize_telegram_chat_ref

    canonical = normalize_telegram_chat_ref(channel_ref) or (channel_ref or "").strip()
    if not canonical:
        return
    try:
        Groups.update(membership_status=status or "").where(
            Groups.user_id == user_id,
            Groups.username == canonical,
        ).execute()
    except Exception as e:
        logger.warning("set_group_membership_error", user_id=user_id, ref=canonical, error=str(e))


def apply_membership_report(
    user_id: int,
    *,
    ok: list[str],
    missing: list[str],
    errors: list[str],
    reasons: dict[str, str],
) -> None:
    """Синхронизирует membership_status в БД после проверки подписок."""
    from core.membership_status import (
        MEMBERSHIP_ERROR,
        MEMBERSHIP_MISSING,
        MEMBERSHIP_OK,
        reason_to_status,
    )

    for ref in ok:
        set_group_membership_by_ref(user_id, ref, MEMBERSHIP_OK)
    for ref in missing:
        reason = reasons.get(ref)
        set_group_membership_by_ref(user_id, ref, reason_to_status(reason))
    for ref in errors:
        set_group_membership_by_ref(user_id, ref, MEMBERSHIP_ERROR)


def delete_all_user_groups(user_id: int) -> int:
    """Удаляет все группы/каналы пользователя из списка отслеживания."""
    try:
        return Groups.delete().where(Groups.user_id == user_id).execute()
    except Exception as e:
        logger.exception("database_cleanup_error", error=e)
        return 0


def get_tracked_channels_count(user_id: int, *, only_enabled: bool = False) -> int:
    """
    Получает количество отслеживаемых каналов для указанного пользователя.

    :param user_id: Telegram ID пользователя
    :param only_enabled: считать только каналы с parse_enabled=True
    :return: Количество отслеживаемых каналов
    """
    try:
        query = Groups.select().where(Groups.user_id == user_id)
        if only_enabled:
            query = query.where(Groups.parse_enabled == True)  # noqa: E712
        return query.count()
    except Exception as e:
        logger.error(f"Ошибка при получении количества отслеживаемых каналов для пользователя {user_id}: {e}")
        return 0


def get_channels_counts(user_id: int) -> tuple[int, int]:
    """Возвращает (включено для парсинга, всего в списке)."""
    total = get_tracked_channels_count(user_id, only_enabled=False)
    enabled = get_tracked_channels_count(user_id, only_enabled=True)
    return enabled, total


def get_user_channel_usernames(user_id: int, *, only_enabled: bool = True) -> tuple[list[str], int]:
    """
    Получает username каналов/групп пользователя по user_id.

    :param user_id: Telegram ID пользователя
    :param only_enabled: только каналы с parse_enabled=True (для парсера)
    :return: Кортеж (список username, общее количество)
    """
    try:
        query = Groups.select(Groups.id, Groups.username, Groups.parse_enabled).where(Groups.user_id == user_id)
        if only_enabled:
            query = query.where(Groups.parse_enabled == True)  # noqa: E712
        records = list(query.order_by(Groups.date_added.desc()))

        usernames = []
        for row in records:
            normalized = normalize_telegram_chat_ref(row.username) or normalize_telegram_username(row.username)
            if not normalized:
                logger.warning(f"Удаляем невалидный канал {row.username} для user_id={user_id}")
                Groups.delete().where(Groups.id == row.id).execute()
                continue

            if normalized != row.username:
                duplicate = Groups.get_or_none(Groups.user_id == user_id, Groups.username == normalized)
                if duplicate:
                    Groups.delete().where(Groups.id == row.id).execute()
                else:
                    Groups.update(username=normalized).where(Groups.id == row.id).execute()

            usernames.append(normalized)

        return usernames, len(usernames)

    except Exception as e:
        logger.error(f"Ошибка при получении каналов пользователя {user_id}: {e}")
        return [], 0


def list_user_channels(user_id: int, *, page: int = 0, page_size: int = 10) -> tuple[list[dict], int, int]:
    """Список каналов для UI: items, total, page."""
    total = Groups.select().where(Groups.user_id == user_id).count()
    max_page = max(0, (total - 1) // page_size) if total else 0
    page = max(0, min(page, max_page))
    rows = list(
        Groups.select()
        .where(Groups.user_id == user_id)
        .order_by(Groups.date_added.desc())
        .offset(page * page_size)
        .limit(page_size)
    )
    items = [
        {
            "id": row.id,
            "username": row.username,
            "parse_enabled": bool(row.parse_enabled),
            "membership_status": (row.membership_status or "").strip(),
        }
        for row in rows
    ]
    return items, total, page


"""
Таблица с аккаунтами пользователя пользователей телеграмм бота
"""


class UserAccountsTable(BaseModel):
    id = AutoField()  # ✅ Первичный ключ (обязательно!)
    user_id = IntegerField(index=True)  # ID пользователя Telegram
    session_string = CharField(unique=True, max_length=500, index=True)
    phone_number = CharField(max_length=20, index=True)
    is_active = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)  # ✅ Полезно для отладки

    class Meta:
        database = db
        table_name = f"user_accounts_table"  # Динамическое имя таблицы


def _account_to_dict(account: UserAccountsTable) -> dict:
    return {
        "id": account.id,
        "user_id": account.user_id,
        "session_string": account.session_string,
        "phone_number": account.phone_number,
        "is_active": bool(account.is_active),
        "created_at": account.created_at,
    }


def write_account_to_user_table(user_id: int, session_string: str, phone_number: str):
    """
    Записывает аккаунт пользователя. Первый / единственный без активного — становится активным.
    """
    try:
        has_active = (
            UserAccountsTable.select()
            .where(
                (UserAccountsTable.user_id == user_id)
                & (UserAccountsTable.is_active == True)  # noqa: E712
            )
            .exists()
        )
        user_accounts = UserAccountsTable.create(
            user_id=user_id,
            session_string=session_string,
            phone_number=phone_number,
            is_active=not has_active,
        )
        user_accounts.save()
        return _account_to_dict(user_accounts)
    except Exception as e:
        logger.exception("database_query_error", error=e)
        return None


def get_user_accounts(user_id: int):
    """
    Получает все аккаунты пользователя (активный первым).
    """
    try:
        accounts = (
            UserAccountsTable.select()
            .where(UserAccountsTable.user_id == user_id)
            .order_by(UserAccountsTable.is_active.desc(), UserAccountsTable.id.asc())
        )
        return [_account_to_dict(account) for account in accounts]
    except Exception as e:
        logger.exception(f"❌ Ошибка получения аккаунтов пользователя {user_id}: {e}")
        return []


def get_active_account(user_id: int) -> dict | None:
    """Активный аккаунт пользователя; при отсутствии флага — первый и помечаем его."""
    try:
        account = (
            UserAccountsTable.select()
            .where(
                (UserAccountsTable.user_id == user_id)
                & (UserAccountsTable.is_active == True)  # noqa: E712
            )
            .first()
        )
        if account:
            return _account_to_dict(account)

        first = (
            UserAccountsTable.select()
            .where(UserAccountsTable.user_id == user_id)
            .order_by(UserAccountsTable.id.asc())
            .first()
        )
        if not first:
            return None
        first.is_active = True
        first.save()
        return _account_to_dict(first)
    except Exception as e:
        logger.exception("get_active_account_error", error=e)
        return None


def set_active_account(user_id: int, account_id: int) -> dict | None:
    """Делает аккаунт активным (остальные пользователя — неактивны)."""
    try:
        account = (
            UserAccountsTable.select()
            .where(
                (UserAccountsTable.user_id == user_id)
                & (UserAccountsTable.id == account_id)
            )
            .first()
        )
        if not account:
            return None
        with db.atomic():
            UserAccountsTable.update(is_active=False).where(
                UserAccountsTable.user_id == user_id
            ).execute()
            account.is_active = True
            account.save()
        return _account_to_dict(account)
    except Exception as e:
        logger.exception("set_active_account_error", error=e)
        return None


def get_failover_account(user_id: int, exclude_ids: set[int] | None = None) -> dict | None:
    """Следующий аккаунт для failover (не из exclude_ids)."""
    exclude = exclude_ids or set()
    try:
        for account in (
            UserAccountsTable.select()
            .where(UserAccountsTable.user_id == user_id)
            .order_by(UserAccountsTable.is_active.desc(), UserAccountsTable.id.asc())
        ):
            if account.id in exclude:
                continue
            return _account_to_dict(account)
        return None
    except Exception as e:
        logger.exception("get_failover_account_error", error=e)
        return None


def delete_user_account(user_id: int, account_id: int) -> bool:
    """Удаляет аккаунт; если был активным — активирует другой."""
    try:
        account = (
            UserAccountsTable.select()
            .where(
                (UserAccountsTable.user_id == user_id)
                & (UserAccountsTable.id == account_id)
            )
            .first()
        )
        if not account:
            return False
        was_active = bool(account.is_active)
        account.delete_instance()
        if was_active:
            next_acc = (
                UserAccountsTable.select()
                .where(UserAccountsTable.user_id == user_id)
                .order_by(UserAccountsTable.id.asc())
                .first()
            )
            if next_acc:
                next_acc.is_active = True
                next_acc.save()
        return True
    except Exception as e:
        logger.exception("delete_user_account_error", error=e)
        return False


"""Работа с аккаунтами"""


class Account(Model):
    """Модель аккаунта"""
    session_string = CharField(unique=True)  # уникальность для защиты от дубликатов
    phone_number = CharField()  # номер телефона аккаунта

    class Meta:
        database = db
        table_name = 'account'


class AccountFree(Model):
    """Свободные аккаунты для подключения, которые подключает администратор бота"""
    session_string = CharField(unique=True)  # Уникальность для защиты от дубликатов
    phone_number = CharField()  # Номер телефона аккаунта

    class Meta:
        database = db
        table_name = 'account_free'


def write_account_to_db(session_string, phone_number):
    """
    Запись аккаунта в базу данных
    :param phone_number: Номер телефона аккаунта
    :param session_string: Строка сессии
    """
    try:
        Account.insert(session_string=session_string, phone_number=phone_number).on_conflict(action='IGNORE').execute()
    except Exception as e:
        logger.exception("database_operation_error", error=e)


def getting_free_account():
    """
    Получение свободных аккаунтов для подключения
    :return: Список аккаунтов
    """
    records = []
    for record in AccountFree.select(AccountFree.session_string):
        records.append(record.session_string)

    return records


def getting_account():
    """
    Получение аккаунтов из базы данных
    :return: Список аккаунтов из базы данных
    """
    records = []
    for record in Account.select(Account.session_string):
        records.append(record.session_string)

    return records


async def delete_account_from_db(session_string: str) -> None:
    """
    Удаляет аккаунт из таблицы 'account' по session_string.
    Перед удалением извлекает и логирует номер телефона.

    :param session_string: Строка сессии аккаунта
    :return: None
    """
    try:
        # Ищем аккаунт по session_string
        account = Account.get(Account.session_string == session_string)
        phone_number = account.phone_number
        logger.info(f"Найден аккаунт для удаления: {phone_number}")
        # Удаляем запись
        account.delete_instance()
        logger.info(f"Аккаунт {phone_number} успешно удалён из базы данных.")
    except DoesNotExist:
        logger.info(f"Аккаунт с session_string='{session_string}' не найден в базе.")
    except Exception as e:
        logger.exception("Ошибка при удалении аккаунта")
        logger.info(f"Ошибка при удалении аккаунта: {e}")


class User(BaseModel):
    """
    Модель для хранения основных данных пользователя Telegram.

    Используется для регистрации пользователей при первом запуске бота (/start)
    и хранения их профиля и языка интерфейса. Таблица общая для всех пользователей.

    Attributes:
        user_id (IntegerField): Уникальный идентификатор пользователя Telegram (первичный ключ).
        username (CharField, optional): Telegram-ник пользователя (может быть None).
        first_name (CharField, optional): Имя пользователя.
        last_name (CharField, optional): Фамилия пользователя.
        language (CharField): Язык интерфейса бота ('ru', 'en' или 'unset' при первом запуске).

    Meta:
        table_name (str): Имя таблицы в базе данных — 'user' (по умолчанию от имени класса).
    """
    user_id = IntegerField(unique=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    language = CharField(default="ru")  # "ru" или "en"
    stars = IntegerField(default=0)
    last_free_download_at = DateTimeField(null=True)
    match_mode = CharField(default="smart")  # strict | smart | loose
    quiet_hours_enabled = BooleanField(default=False)
    quiet_hours_start = IntegerField(default=23)  # час 0–23
    quiet_hours_end = IntegerField(default=8)
    digest_enabled = BooleanField(default=False)
    digest_interval_min = IntegerField(default=60)
    chat_filter = CharField(default="all")  # all | channels | groups
    alert_template = CharField(default="full")  # full | compact | minimal
    alert_to_dm = BooleanField(default=True)
    alert_to_group = BooleanField(default=False)
    alert_chat_id = IntegerField(null=True)
    alert_thread_id = IntegerField(null=True)
    author_filter = CharField(default="humans")  # humans | humans_anon | all


def create_keywords_model(user_id):
    """
    Динамически создаёт модель Peewee для хранения ключевых слов конкретного пользователя.

    Модель используется для отслеживания слов или фраз, по которым пользователь хочет фильтровать сообщения в группах.
    Создаётся отдельная таблица для каждого пользователя по шаблону 'keywords_<user_id>'.

    :param user_id: (int) Уникальный идентификатор пользователя Telegram.
    :return peewee.Model: Класс модели Peewee с полями `id` и `user_keyword`.

    Model Fields:
        id (AutoField):
            Автоинкрементный первичный ключ.
        user_keyword (CharField):
            Уникальное ключевое слово для поиска в сообщениях.
    """

    class Keywords(BaseModel):
        id = AutoField()  # <-- добавляем первичный ключ (иначе всё пишется в одну строку)
        user_keyword = CharField(unique=True)  # Поле для хранения ключевого слова

        class Meta:
            table_name = f"{user_id}_keywords"  # Имя таблицы

    return Keywords  # Возвращаем класс модели


def create_group_model(user_id):
    """
    Динамически создаёт модель Peewee для хранения технической группы пользователя.

    Модель используется для сохранения одного Telegram-чата (группы или канала),
    куда бот будет пересылать найденные сообщения, содержащие ключевые слова.
    Создаётся отдельная таблица для каждого пользователя по шаблону 'group_<user_id>'.

    :param user_id: (int) Уникальный идентификатор пользователя Telegram.
    :return peewee.Model: Класс модели Peewee с полями `id` и `user_group`.

    Model Fields:
        id (AutoField):
            Автоинкрементный первичный ключ.
        user_group (CharField):
            Уникальное имя технической группы (например, @my_alerts_channel).
    """

    class Group(BaseModel):
        id = AutoField()  # <-- добавляем первичный ключ (иначе всё пишется в одну строку)
        user_group = CharField(unique=True)  # Поле для хранения технической группы

        class Meta:
            table_name = f"{user_id}_group"  # Имя таблицы

    return Group  # Возвращаем класс модели


"""
Работа с моделью TelegramGroup. База групп и каналов в Telegram.
"""


class TelegramGroup(BaseModel):
    """
    Модель для хранения данных о найденных Telegram-группах и каналах.

    Используется для централизованного хранения информации о группах,
    обнаруженных с помощью AI-поиска (через Groq). Позволяет избежать
    повторного поиска и дублирования. Таблица общая для всех пользователей.

    Attributes:
        telegram_id (IntegerField): Уникальный ID группы в Telegram (первичный ключ).
        group_hash (CharField): Уникальный хеш или ID группы, используется как ключ.
        name (CharField): Отображаемое название группы или канала.
        username (CharField, optional): Юзернейм (@username), может отсутствовать.
        description (TextField, optional): Описание группы из Telegram.
        participants (IntegerField): Количество участников, по умолчанию 0.
        category (CharField, optional): Категория, определённая ИИ (например, 'технологии').
        group_type (CharField): Тип чата — 'group', 'channel' или 'link'.
        language (CharField): Язык группы/канала — 'ru', 'en' или ''.
        link (CharField): Прямая ссылка на чат (https://t.me/...).
        availability (CharField): Статус активности группы
        date_added (DateTimeField): Дата и время добавления записи, по умолчанию — текущее время.

    Meta:
        table_name (str): Имя таблицы в базе данных — 'telegram_groups'.
    """
    telegram_id = IntegerField(null=True, unique=True)  # Новое поле: Telegram entity ID
    group_hash = CharField(null=True)  # ID группы или хеш username
    name = CharField()  # Название группы
    username = CharField(null=True)  # @username если есть
    description = TextField(null=True)  # Описание
    participants = IntegerField(default=0)  # Количество участников
    category = CharField(null=True)  # Категория (определяется AI)
    group_type = CharField()  # 'group', 'channel', 'link'
    language = CharField(null=True, default='')  # ru/en язык группы / канала
    link = CharField(null=True, default='')  # Ссылка на группу (может отсутствовать)
    availability = CharField(null=True)  # Статус активности
    date_added = DateTimeField(default=datetime.now)  # Дата добавления

    class Meta:
        table_name = 'telegram_groups'


def clean_telegram_id_duplicates():
    """Удаляет все дубликаты по telegram_id, оставляя самую свежую запись"""
    deleted_count = 0

    # Находим все telegram_id с дублями
    duplicates = (
        TelegramGroup
        .select(
            TelegramGroup.telegram_id,
            fn.COUNT(TelegramGroup.id).alias("cnt")
        )
        .where(TelegramGroup.telegram_id.is_null(False))
        .group_by(TelegramGroup.telegram_id)
        .having(fn.COUNT(TelegramGroup.id) > 1)
    )

    for dup in duplicates:
        tid = dup.telegram_id

        # Оставляем самую новую запись
        keep = (
            TelegramGroup
            .select(TelegramGroup.id)
            .where(TelegramGroup.telegram_id == tid)
            .order_by(TelegramGroup.date_added.desc())
            .limit(1)
            .get()
        )

        # Удаляем все остальные
        deleted = (
            TelegramGroup
            .delete()
            .where(
                (TelegramGroup.telegram_id == tid) &
                (TelegramGroup.id != keep.id)
            )
            .execute()
        )
        deleted_count += deleted

    logger.info(f"Очищено дубликатов по telegram_id: {deleted_count}")
    return deleted_count


async def get_groups_without_category() -> list[dict]:
    """Получает группы без категории (в отдельном потоке для БД)"""

    def _fetch():
        if db.is_closed():
            db.connect(reuse_if_open=True)

        groups = TelegramGroup.select().where(
            (TelegramGroup.username.is_null(False)) &
            (TelegramGroup.category == '')
        )

        return [
            {
                "telegram_id": group.telegram_id,
                "name": group.name,
                "username": group.username,
                "description": group.description,
                "group_type": group.group_type,
            }
            for group in groups
        ]

    try:
        return await sync_to_async(_fetch, thread_sensitive=True)()
    except Exception as e:
        logger.exception(f"❌ Ошибка получения групп: {e}")
        return []


def migrate_categories_to_lowercase():
    """
    Миграция: приводит все существующие категории к нижнему регистру.
    Запускать один раз после обновления логики.
    """
    if db.is_closed():
        db.connect(reuse_if_open=True)

    try:
        groups = TelegramGroup.select().where(
            TelegramGroup.category.is_null(False) &
            (TelegramGroup.category != '')
        )

        updated_count = 0
        for group in groups:
            if group.category != group.category.lower():
                group.category = group.category.lower()
                group.save()
                updated_count += 1

        logger.info(f"✅ Миграция категорий завершена: обновлено {updated_count} записей")
        return updated_count
    except Exception as e:
        logger.exception(f"❌ Ошибка миграции категорий: {e}")
        return 0


def getting_number_records_database():
    """Получает количество записей в базе данных о найденных группах пользователями"""
    return TelegramGroup.select().count()


def get_target_group_count(user_id: int) -> int:
    """
    Получает количество технических групп (куда пересылаются уведомления),
    подключённых конкретным пользователем.

    Ищет записи в таблице `group_{user_id}`.

    :param user_id: (int) ID пользователя Telegram.
    :return int: Количество записей (обычно 0 или 1, так как группа одна).
    """
    GroupModel = create_group_model(user_id)

    # Убедимся, что таблица существует, иначе count() вызовет ошибку
    if not GroupModel.table_exists():
        return 0

    return GroupModel.select().count()


def get_session_count(user_id: int) -> int:
    """
    Подсчитывает количество подключенных аккаунтов пользователя в базе данных.

    :param user_id: (int) ID пользователя Telegram.
    :return int: Количество сессий (0, если аккаунты отсутствуют).
    """
    try:
        return UserAccountsTable.select().where(UserAccountsTable.user_id == user_id).count()
    except Exception as e:
        logger.error(f"Ошибка при получении количества сессий пользователя {user_id}: {e}")
        return 0


def get_keywords_count(user_id: int):
    """Количество ключевых слов пользователя."""
    Keywords = create_keywords_model(user_id)
    if not Keywords.table_exists():
        return 0
    return Keywords.select().count()


def get_user_match_mode(user_id: int) -> str:
    from core.keyword_match import DEFAULT_MATCH_MODE, normalize_match_mode

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_MATCH_MODE
        return normalize_match_mode(getattr(user, "match_mode", None))
    except Exception as e:
        logger.exception("get_match_mode_error", error=e)
        return DEFAULT_MATCH_MODE


def set_user_match_mode(user_id: int, mode: str) -> str:
    from core.keyword_match import DEFAULT_MATCH_MODE, normalize_match_mode

    mode = normalize_match_mode(mode)
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_MATCH_MODE
        user.match_mode = mode
        user.save()
        return mode
    except Exception as e:
        logger.exception("set_match_mode_error", error=e)
        return DEFAULT_MATCH_MODE


def get_user_quiet_hours(user_id: int) -> dict:
    from core.quiet_hours import normalize_hour

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return {"enabled": False, "start": 23, "end": 8}
        return {
            "enabled": bool(getattr(user, "quiet_hours_enabled", False)),
            "start": normalize_hour(getattr(user, "quiet_hours_start", 23)),
            "end": normalize_hour(getattr(user, "quiet_hours_end", 8)),
        }
    except Exception as e:
        logger.exception("get_quiet_hours_error", error=e)
        return {"enabled": False, "start": 23, "end": 8}


def set_user_quiet_hours(
    user_id: int,
    *,
    enabled: bool | None = None,
    start: int | None = None,
    end: int | None = None,
) -> dict:
    from core.quiet_hours import normalize_hour

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return get_user_quiet_hours(user_id)
        if enabled is not None:
            user.quiet_hours_enabled = bool(enabled)
        if start is not None:
            user.quiet_hours_start = normalize_hour(start)
        if end is not None:
            user.quiet_hours_end = normalize_hour(end)
        user.save()
        return get_user_quiet_hours(user_id)
    except Exception as e:
        logger.exception("set_quiet_hours_error", error=e)
        return get_user_quiet_hours(user_id)


def is_user_in_quiet_hours(user_id: int) -> bool:
    from core.quiet_hours import current_local_hour, is_in_quiet_window

    cfg = get_user_quiet_hours(user_id)
    if not cfg["enabled"]:
        return False
    return is_in_quiet_window(current_local_hour(), cfg["start"], cfg["end"])


def get_user_digest_settings(user_id: int) -> dict:
    from core.digest import normalize_digest_interval

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return {"enabled": False, "interval_min": 60}
        return {
            "enabled": bool(getattr(user, "digest_enabled", False)),
            "interval_min": normalize_digest_interval(
                getattr(user, "digest_interval_min", 60)
            ),
        }
    except Exception as e:
        logger.exception("get_digest_settings_error", error=e)
        return {"enabled": False, "interval_min": 60}


def set_user_digest_settings(
    user_id: int,
    *,
    enabled: bool | None = None,
    interval_min: int | None = None,
) -> dict:
    from core.digest import normalize_digest_interval

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return get_user_digest_settings(user_id)
        if enabled is not None:
            user.digest_enabled = bool(enabled)
        if interval_min is not None:
            user.digest_interval_min = normalize_digest_interval(interval_min)
        user.save()
        return get_user_digest_settings(user_id)
    except Exception as e:
        logger.exception("set_digest_settings_error", error=e)
        return get_user_digest_settings(user_id)


def get_user_chat_filter(user_id: int) -> str:
    from core.chat_filter import DEFAULT_CHAT_FILTER, normalize_chat_filter

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_CHAT_FILTER
        return normalize_chat_filter(getattr(user, "chat_filter", None))
    except Exception as e:
        logger.exception("get_chat_filter_error", error=e)
        return DEFAULT_CHAT_FILTER


def set_user_chat_filter(user_id: int, mode: str) -> str:
    from core.chat_filter import DEFAULT_CHAT_FILTER, normalize_chat_filter

    mode = normalize_chat_filter(mode)
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_CHAT_FILTER
        user.chat_filter = mode
        user.save()
        return mode
    except Exception as e:
        logger.exception("set_chat_filter_error", error=e)
        return DEFAULT_CHAT_FILTER


def get_user_author_filter(user_id: int) -> str:
    from core.author_kind import DEFAULT_AUTHOR_FILTER, normalize_author_filter

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_AUTHOR_FILTER
        return normalize_author_filter(getattr(user, "author_filter", None))
    except Exception as e:
        logger.exception("get_author_filter_error", error=e)
        return DEFAULT_AUTHOR_FILTER


def set_user_author_filter(user_id: int, mode: str) -> str:
    from core.author_kind import DEFAULT_AUTHOR_FILTER, normalize_author_filter

    mode = normalize_author_filter(mode)
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_AUTHOR_FILTER
        user.author_filter = mode
        user.save()
        return mode
    except Exception as e:
        logger.exception("set_author_filter_error", error=e)
        return DEFAULT_AUTHOR_FILTER


def get_user_alert_template(user_id: int) -> str:
    from core.alert_template import DEFAULT_ALERT_TEMPLATE, normalize_alert_template

    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_ALERT_TEMPLATE
        return normalize_alert_template(getattr(user, "alert_template", None))
    except Exception as e:
        logger.exception("get_alert_template_error", error=e)
        return DEFAULT_ALERT_TEMPLATE


def set_user_alert_template(user_id: int, template: str) -> str:
    from core.alert_template import DEFAULT_ALERT_TEMPLATE, normalize_alert_template

    template = normalize_alert_template(template)
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return DEFAULT_ALERT_TEMPLATE
        user.alert_template = template
        user.save()
        return template
    except Exception as e:
        logger.exception("set_alert_template_error", error=e)
        return DEFAULT_ALERT_TEMPLATE


def get_user_alert_destination(user_id: int) -> dict:
    """Настройки куда слать алерты: личка / группа / топик."""
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return {
                "alert_to_dm": True,
                "alert_to_group": False,
                "alert_chat_id": None,
                "alert_thread_id": None,
            }
        return {
            "alert_to_dm": bool(getattr(user, "alert_to_dm", True)),
            "alert_to_group": bool(getattr(user, "alert_to_group", False)),
            "alert_chat_id": getattr(user, "alert_chat_id", None),
            "alert_thread_id": getattr(user, "alert_thread_id", None),
        }
    except Exception as e:
        logger.exception("get_alert_destination_error", error=e)
        return {
            "alert_to_dm": True,
            "alert_to_group": False,
            "alert_chat_id": None,
            "alert_thread_id": None,
        }


def set_user_alert_to_dm(user_id: int, enabled: bool) -> bool:
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return False
        user.alert_to_dm = bool(enabled)
        user.save()
        return bool(user.alert_to_dm)
    except Exception as e:
        logger.exception("set_alert_to_dm_error", error=e)
        return enabled


def set_user_alert_to_group(user_id: int, enabled: bool) -> bool:
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return False
        user.alert_to_group = bool(enabled)
        if not enabled:
            user.alert_chat_id = None
            user.alert_thread_id = None
        user.save()
        return bool(user.alert_to_group)
    except Exception as e:
        logger.exception("set_alert_to_group_error", error=e)
        return enabled


def set_user_alert_group_bind(
    user_id: int,
    *,
    chat_id: int,
    thread_id: int | None = None,
) -> None:
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return
        user.alert_to_group = True
        user.alert_chat_id = int(chat_id)
        user.alert_thread_id = int(thread_id) if thread_id is not None else None
        user.save()
    except Exception as e:
        logger.exception("set_alert_group_bind_error", error=e)


def clear_user_alert_group_bind(user_id: int) -> None:
    try:
        user = User.get_or_none(User.user_id == user_id)
        if not user:
            return
        user.alert_chat_id = None
        user.alert_thread_id = None
        user.save()
    except Exception as e:
        logger.exception("clear_alert_group_bind_error", error=e)


def find_alert_group_owner(chat_id: int, thread_id: int | None = None) -> int | None:
    """Владелец, привязавший этот чат/топик для алертов (если есть)."""
    try:
        query = User.select().where(
            (User.alert_to_group == True)  # noqa: E712
            & (User.alert_chat_id == int(chat_id))
        )
        for user in query:
            bound_thread = getattr(user, "alert_thread_id", None)
            if bound_thread is None:
                if thread_id is None or thread_id in (None, 0, 1):
                    return int(user.user_id)
            elif thread_id is not None and int(bound_thread) == int(thread_id):
                return int(user.user_id)
        return None
    except Exception as e:
        logger.exception("find_alert_group_owner_error", error=e)
        return None


class StopWord(BaseModel):
    """Стоп-слова пользователя: при наличии в тексте алерт не отправляется."""

    id = AutoField()
    user_id = IntegerField(index=True)
    word = CharField(max_length=512)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "stopwords"
        indexes = ((("user_id", "word"), True),)


def get_user_stopwords(user_id: int) -> list[str]:
    try:
        rows = (
            StopWord.select()
            .where(StopWord.user_id == user_id)
            .order_by(StopWord.id.asc())
        )
        return [row.word for row in rows if row.word]
    except Exception as e:
        logger.exception("get_stopwords_error", error=e)
        return []


def get_stopwords_count(user_id: int) -> int:
    try:
        return StopWord.select().where(StopWord.user_id == user_id).count()
    except Exception as e:
        logger.exception("get_stopwords_count_error", error=e)
        return 0


def add_stopwords(user_id: int, words: list[str]) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    added: list[str] = []
    skipped: list[str] = []
    errors: list[tuple[str, str]] = []
    for raw in words:
        word = (raw or "").strip()
        if not word:
            continue
        try:
            StopWord.create(user_id=user_id, word=word)
            added.append(word)
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                skipped.append(word)
            else:
                errors.append((word, str(e)))
                logger.error("stopword_add_error", word=word, error=e)
    return added, skipped, errors


def list_stopwords(
    user_id: int, *, page: int = 0, page_size: int = 10
) -> tuple[list[tuple[int, str]], int, int]:
    total = get_stopwords_count(user_id)
    page = max(0, page)
    rows = (
        StopWord.select()
        .where(StopWord.user_id == user_id)
        .order_by(StopWord.id.asc())
        .offset(page * page_size)
        .limit(page_size)
    )
    items = [(row.id, row.word) for row in rows]
    return items, total, page


def delete_stopword(user_id: int, stopword_id: int) -> str | None:
    row = (
        StopWord.select()
        .where((StopWord.user_id == user_id) & (StopWord.id == stopword_id))
        .first()
    )
    if not row:
        return None
    text = row.word
    row.delete_instance()
    return text


class Lead(BaseModel):
    """Сохранённые совпадения по ключевым словам (история матчей)."""

    id = AutoField()
    owner_user_id = IntegerField(index=True)
    author_tg_id = IntegerField(null=True)
    author_username = CharField(null=True, max_length=255)
    author_name = CharField(null=True, max_length=512)
    chat_id = IntegerField()
    chat_title = CharField(null=True, max_length=512)
    chat_username = CharField(null=True, max_length=255)
    message_id = IntegerField()
    message_link = TextField(null=True)
    message_text = TextField()
    matched_keyword = CharField(max_length=512)
    matched_at = DateTimeField(default=datetime.now, index=True)
    unique_key = CharField(unique=True, max_length=128)
    author_kind = CharField(default="anonymous", max_length=32)  # user|bot|channel|anonymous|forward_channel

    class Meta:
        table_name = "leads"
        indexes = (
            (("owner_user_id", "matched_at"), False),
        )


def make_lead_unique_key(owner_user_id: int, chat_id: int, message_id: int) -> str:
    return f"{owner_user_id}:{chat_id}:{message_id}"


def lead_exists(owner_user_id: int, chat_id: int, message_id: int) -> bool:
    key = make_lead_unique_key(owner_user_id, chat_id, message_id)
    return Lead.select().where(Lead.unique_key == key).exists()


def save_lead(
    *,
    owner_user_id: int,
    chat_id: int,
    message_id: int,
    message_text: str,
    matched_keyword: str,
    chat_title: str | None = None,
    chat_username: str | None = None,
    message_link: str | None = None,
    author_tg_id: int | None = None,
    author_username: str | None = None,
    author_name: str | None = None,
    author_kind: str | None = None,
) -> bool:
    """
    UPSERT по unique_key. Возвращает True, если запись создана или уже была.
    Ошибки БД логируются, наружу не пробрасываются.
    """
    from core.author_kind import normalize_author_kind

    unique_key = make_lead_unique_key(owner_user_id, chat_id, message_id)
    kind = normalize_author_kind(author_kind)
    try:
        existing = Lead.get_or_none(Lead.unique_key == unique_key)
        if existing:
            return True

        Lead.create(
            owner_user_id=owner_user_id,
            author_tg_id=author_tg_id,
            author_username=(author_username or None),
            author_name=(author_name or None),
            author_kind=kind,
            chat_id=chat_id,
            chat_title=chat_title,
            chat_username=chat_username,
            message_id=message_id,
            message_link=message_link,
            message_text=message_text,
            matched_keyword=matched_keyword,
            unique_key=unique_key,
        )
        return True
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return True
        logger.exception("lead_save_error", owner=owner_user_id, error=e)
        return False


def get_leads_count(owner_user_id: int) -> int:
    try:
        return Lead.select().where(Lead.owner_user_id == owner_user_id).count()
    except Exception as e:
        logger.exception("leads_count_error", error=e)
        return 0


def list_leads(owner_user_id: int, *, page: int = 0, page_size: int = 8) -> tuple[list[Lead], int, int]:
    total = get_leads_count(owner_user_id)
    max_page = max(0, (total - 1) // page_size) if total else 0
    page = max(0, min(page, max_page))
    rows = list(
        Lead.select()
        .where(Lead.owner_user_id == owner_user_id)
        .order_by(Lead.matched_at.desc())
        .offset(page * page_size)
        .limit(page_size)
    )
    return rows, total, page


def get_all_leads_for_export(owner_user_id: int) -> list[Lead]:
    return get_leads_for_export(owner_user_id)


def get_leads_for_export(
    owner_user_id: int,
    date_from=None,
    date_to=None,
) -> list[Lead]:
    """Лиды для выгрузки; date_from/date_to — date в TIMEZONE приложения."""
    from datetime import date as date_type, datetime, timedelta, time

    from core.config import TIMEZONE

    try:
        query = Lead.select().where(Lead.owner_user_id == owner_user_id)
        if date_from is not None or date_to is not None:
            try:
                from zoneinfo import ZoneInfo

                tz = ZoneInfo(TIMEZONE)
            except Exception:
                tz = None

            if date_from is not None:
                if isinstance(date_from, str):
                    date_from = date_type.fromisoformat(date_from)
                start = datetime.combine(date_from, time.min)
                if tz:
                    start = start.replace(tzinfo=tz).astimezone().replace(tzinfo=None)
                query = query.where(Lead.matched_at >= start)

            if date_to is not None:
                if isinstance(date_to, str):
                    date_to = date_type.fromisoformat(date_to)
                end = datetime.combine(date_to + timedelta(days=1), time.min)
                if tz:
                    end = end.replace(tzinfo=tz).astimezone().replace(tzinfo=None)
                query = query.where(Lead.matched_at < end)

        return list(query.order_by(Lead.matched_at.desc()))
    except Exception as e:
        logger.exception("leads_export_query_error", error=e)
        return []
