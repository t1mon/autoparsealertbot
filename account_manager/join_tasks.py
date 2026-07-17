"""Реестр фоновых задач массового join из меню каналов."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

_tasks: dict[int, UserJoinTask] = {}


@dataclass
class UserJoinTask:
    user_id: int
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None
    chat_id: int | None = None
    message_id: int | None = None
    ui_attached: bool = True
    total: int = 0
    lang: str = "ru"


def get_join_task(user_id: int) -> UserJoinTask | None:
    entry = _tasks.get(user_id)
    if entry is None:
        return None
    if entry.task is not None and entry.task.done():
        _tasks.pop(user_id, None)
        return None
    return entry


def is_join_running(user_id: int) -> bool:
    entry = get_join_task(user_id)
    return entry is not None and entry.task is not None and not entry.task.done()


def detach_join_ui(user_id: int) -> None:
    entry = _tasks.get(user_id)
    if entry is not None:
        entry.ui_attached = False


def request_join_cancel(user_id: int) -> bool:
    entry = _tasks.get(user_id)
    if entry is None or entry.task is None or entry.task.done():
        return False
    entry.stop_event.set()
    return True


def register_join_task(
    user_id: int,
    task: asyncio.Task,
    *,
    chat_id: int,
    message_id: int,
    total: int,
    lang: str,
    stop_event: asyncio.Event,
) -> UserJoinTask:
    old = _tasks.get(user_id)
    if old is not None and old.task is not None and not old.task.done():
        old.stop_event.set()
        old.task.cancel()

    entry = UserJoinTask(
        user_id=user_id,
        stop_event=stop_event,
        task=task,
        chat_id=chat_id,
        message_id=message_id,
        total=total,
        lang=lang,
        ui_attached=True,
    )
    _tasks[user_id] = entry
    return entry


def clear_join_task(user_id: int, task: asyncio.Task) -> None:
    entry = _tasks.get(user_id)
    if entry is not None and entry.task is task:
        _tasks.pop(user_id, None)


async def safe_edit_join_message(
    entry: UserJoinTask,
    bot,
    text: str,
    reply_markup,
) -> bool:
    """Редактирует сообщение прогресса, если UI ещё привязан."""
    if not entry.ui_attached or entry.chat_id is None or entry.message_id is None:
        return False
    try:
        await bot.edit_message_text(
            chat_id=entry.chat_id,
            message_id=entry.message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return True
    except Exception as e:
        logger.debug("join_progress_edit_skipped", error=str(e), user_id=entry.user_id)
        return False
