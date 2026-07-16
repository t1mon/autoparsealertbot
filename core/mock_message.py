from __future__ import annotations

from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class MockMessage:
    """Заглушка aiogram Message для web API и восстановления отслеживания."""

    def __init__(self, user_id: int, username: Optional[str] = "web_user"):
        self.from_user = type("User", (), {
            "id": user_id,
            "username": username or "web_user",
            "first_name": "Web",
            "last_name": "User",
        })()
        self.chat = type("Chat", (), {"id": user_id})()

    async def answer(self, text: str, reply_markup=None, parse_mode=None, **kwargs):
        from system.dispatcher import bot

        try:
            await bot.send_message(
                chat_id=self.from_user.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except Exception as e:
            logger.error(f"Failed to send mock answer to {self.from_user.id}: {e}")

    async def answer_document(self, document, caption=None, parse_mode=None, **kwargs):
        from system.dispatcher import bot

        try:
            from aiogram.types import BufferedInputFile, FSInputFile

            if isinstance(document, (BufferedInputFile, FSInputFile)):
                await bot.send_document(
                    chat_id=self.from_user.id,
                    document=document,
                    caption=caption,
                    parse_mode=parse_mode,
                )
        except Exception as e:
            logger.error(f"Failed to send mock document to {self.from_user.id}: {e}")
