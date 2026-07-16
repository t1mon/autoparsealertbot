# -*- coding: utf-8 -*-
import asyncio
import os

import structlog
import uvicorn

from account_manager.tracking_restore import restore_active_tracking
from core.config import BOT_MODE, LOG_LEVEL, PORT, REDIS_URL, validate_config, WEBHOOK_SECRET, WEBHOOK_URL
from core.logging_config import configure_stdlib_logging, setup_logging
from core.redis_client import close_redis, connect_redis
from database.database import clean_telegram_id_duplicates, init_database, migrate_categories_to_lowercase
from handlers.admin.admin import router as admin
from handlers.admin.checking_accounts import router as checking_accounts
from handlers.admin.checking_group_for_ai import router as checking_group_for_ai
from handlers.admin.connecting_account import router as connecting_account
from handlers.admin.language_detection import router as language_detection
from handlers.admin.post_log import router as post_log
from handlers.user.checking_group_for_keywords import router as checking_group_for_keywords
from handlers.user.connect_account import router as connect_account
from handlers.user.connect_group import router as connect_group
from handlers.user.delete_group_from_database import router as delete_group_from_database
from handlers.user.entering_keyword import router as entering_keyword
from handlers.user.get_dada import router as get_dada
from handlers.user.handlers import router as handlers
from handlers.user.pars_ai import router as pars_ai
from handlers.user.post_doc import router as post_doc
from handlers.user.stop_tracking import router as stop_tracking
from handlers.user.transfer_rights import router as transfer_settings
from system.dispatcher import bot, dp
from system.filters import IsAdmin
from web.server import app
from web.telegram_webhook import register_telegram_webhook

ADMIN_ROUTERS = (
    admin,
    post_log,
    checking_group_for_ai,
    checking_accounts,
    language_detection,
    connecting_account,
)


def register_routers() -> None:
    dp.include_router(handlers)
    dp.include_router(entering_keyword)
    dp.include_router(connect_group)
    dp.include_router(get_dada)
    dp.include_router(stop_tracking)
    dp.include_router(pars_ai)
    dp.include_router(post_doc)
    dp.include_router(connect_account)
    dp.include_router(checking_group_for_keywords)
    dp.include_router(delete_group_from_database)
    dp.include_router(transfer_settings)

    admin_filter = IsAdmin()
    for router in ADMIN_ROUTERS:
        router.message.filter(admin_filter)
        router.callback_query.filter(admin_filter)
        dp.include_router(router)


async def main() -> None:
    logger = structlog.get_logger(__name__)
    try:
        init_database()
        clean_telegram_id_duplicates()
        register_routers()
        register_telegram_webhook(app)

        logger.info("Запуск миграции категорий в нижнем регистре...")
        updated = migrate_categories_to_lowercase()
        if updated:
            logger.info("Обновлено категорий на нижний регистр", count=updated)

        await connect_redis()
        await restore_active_tracking()

        logger.info("Starting FastAPI Web Server", host="0.0.0.0", port=PORT)
        config = uvicorn.Config(app, host="0.0.0.0", port=PORT, loop="asyncio")
        server = uvicorn.Server(config)

        try:
            if BOT_MODE == "webhook":
                await bot.set_webhook(
                    url=WEBHOOK_URL,
                    secret_token=WEBHOOK_SECRET or None,
                    drop_pending_updates=True,
                )
                logger.info("Режим webhook", url=WEBHOOK_URL)
                await server.serve()
            else:
                await bot.delete_webhook(drop_pending_updates=True)
                logger.info("Режим polling: webhook снят")
                await asyncio.gather(
                    dp.start_polling(bot),
                    server.serve(),
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
