# -*- coding: utf-8 -*-
import asyncio
import os

import structlog
import uvicorn

from account_manager.tracking_restore import restore_active_tracking
from core.config import BOT_MODE, LOG_LEVEL, PORT, REDIS_URL, validate_config, WEBHOOK_SECRET, WEBHOOK_URL
from core.logging_config import configure_stdlib_logging, setup_logging
from core.redis_client import close_redis, connect_redis
from database.database import init_database, migrate_categories_to_lowercase
from handlers.admin.admin import router as admin
from handlers.admin.tracking import router as admin_tracking
from handlers.admin.checking_accounts import router as checking_accounts
from handlers.admin.checking_group_for_ai import router as checking_group_for_ai
from handlers.admin.connecting_account import router as connecting_account
from handlers.admin.language_detection import router as language_detection
from handlers.admin.post_log import router as post_log
from handlers.user.access_gate import router as access_gate
from handlers.user.connect_account import router as connect_account
from handlers.user.alert_actions import router as alert_actions
from handlers.user.channels import router as channels
from handlers.user.quiet_hours import router as quiet_hours
from handlers.user.digest import router as digest
from handlers.user.chat_filter import router as chat_filter
from handlers.user.author_filter import router as author_filter
from handlers.user.alert_template import router as alert_template
from handlers.user.alert_destination import group_router as alert_destination_group
from handlers.user.alert_destination import router as alert_destination
from handlers.user.alert_group_commands import router as alert_group_commands
from handlers.user.group_chat_gate import router as group_chat_gate
from handlers.user.stopwords import router as stopwords
from handlers.user.delete_group_from_database import router as delete_group_from_database
from handlers.user.entering_keyword import router as entering_keyword
from handlers.user.get_dada import router as get_dada
from handlers.user.handlers import router as handlers
from handlers.user.leads import router as leads
from handlers.user.pars_ai import router as pars_ai
from handlers.user.post_doc import router as post_doc
from handlers.user.stop_tracking import router as stop_tracking
from system.dispatcher import bot, dp
from system.filters import IsAdmin, IsAllowedUser, IsPrivateChat
from web.server import app
from web.telegram_webhook import register_telegram_webhook

ADMIN_ROUTERS = (
    admin,
    admin_tracking,
    post_log,
    checking_group_for_ai,
    checking_accounts,
    language_detection,
    connecting_account,
)


GROUP_MESSAGE_ROUTERS = (
    alert_group_commands,
    alert_destination_group,
)

PRIVATE_USER_ROUTERS = (
    handlers,
    entering_keyword,
    channels,
    leads,
    get_dada,
    stop_tracking,
    pars_ai,
    post_doc,
    connect_account,
    alert_actions,
    quiet_hours,
    digest,
    chat_filter,
    author_filter,
    alert_template,
    alert_destination,
    stopwords,
    delete_group_from_database,
)


def register_routers() -> None:
    dp.include_router(access_gate)

    allowed_filter = IsAllowedUser()
    private_filter = IsPrivateChat()

    for router in GROUP_MESSAGE_ROUTERS:
        router.message.filter(allowed_filter)
        dp.include_router(router)

    for router in PRIVATE_USER_ROUTERS:
        router.message.filter(allowed_filter)
        router.message.filter(private_filter)
        router.callback_query.filter(allowed_filter)
        if router is not alert_actions:
            router.callback_query.filter(private_filter)
        dp.include_router(router)

    dp.include_router(group_chat_gate)

    admin_filter = IsAdmin()
    for router in ADMIN_ROUTERS:
        router.message.filter(admin_filter)
        router.callback_query.filter(admin_filter)
        dp.include_router(router)


async def main() -> None:
    logger = structlog.get_logger(__name__)
    try:
        init_database()
        register_routers()
        register_telegram_webhook(app)

        logger.info("Запуск миграции категорий в нижнем регистре...")
        updated = migrate_categories_to_lowercase()
        if updated:
            logger.info("Обновлено категорий на нижний регистр", count=updated)

        await connect_redis()

        logger.info("Starting FastAPI Web Server", host="0.0.0.0", port=PORT)
        # http=h11 — без зависимости httptools; loop уже создан asyncio.run
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=PORT,
            loop="asyncio",
            http="h11",
        )
        server = uvicorn.Server(config)

        async def _restore_after_boot() -> None:
            # После старта polling/uvicorn, иначе create_task до serve() может быть сброшен
            await asyncio.sleep(0.5)
            await restore_active_tracking()

        try:
            if BOT_MODE == "webhook":
                await bot.set_webhook(
                    url=WEBHOOK_URL,
                    secret_token=WEBHOOK_SECRET or None,
                    drop_pending_updates=True,
                )
                logger.info("Режим webhook", url=WEBHOOK_URL)
                await asyncio.gather(server.serve(), _restore_after_boot())
            else:
                await bot.delete_webhook(drop_pending_updates=True)
                logger.info("Режим polling: webhook снят")
                await asyncio.gather(
                    dp.start_polling(bot),
                    server.serve(),
                    _restore_after_boot(),
                )
        finally:
            await close_redis()

    except Exception as e:
        logger.exception("fatal_error", error=e)


if __name__ == "__main__":
    validate_config()
    os.makedirs("logs", exist_ok=True)
    file_formatter, console_formatter = setup_logging()
    configure_stdlib_logging(file_formatter, console_formatter)
    structlog.get_logger(__name__).info("Logging configured", level=LOG_LEVEL, redis_url=bool(REDIS_URL))
    asyncio.run(main())
