from typing import Optional

from fastapi import BackgroundTasks, Header, Request, Response
import structlog

logger = structlog.get_logger(__name__)

from core.config import BOT_MODE, WEBHOOK_PATH, WEBHOOK_SECRET


def register_telegram_webhook(app) -> None:
    """Регистрирует POST-эндпоинт для приёма обновлений Telegram (режим webhook)."""
    if BOT_MODE != "webhook":
        return

    from system.dispatcher import bot, dp

    @app.post(WEBHOOK_PATH)
    async def telegram_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        x_telegram_bot_api_secret_token: Optional[str] = Header(None),
    ):
        if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
            logger.warning("Webhook: отклонён запрос с неверным secret token")
            return Response(status_code=403)

        update_data = await request.json()
        background_tasks.add_task(dp.feed_raw_update, bot, update_data)
        return Response(status_code=200)

    logger.info(f"Webhook endpoint зарегистрирован: POST {WEBHOOK_PATH}")
