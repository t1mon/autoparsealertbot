"""Остановка tracking для пользователей без доступа."""

from __future__ import annotations

import structlog

from core.access import is_user_allowed
from core import tracking_store

logger = structlog.get_logger(__name__)


async def purge_disallowed_tracking() -> None:
    """Снимает tracking в Redis/памяти для user_id вне allowlist."""
    from account_manager.parser import active_clients, stop_flags, _safe_disconnect
    from core.metrics import clear_tracking_started

    active_ids = await tracking_store.list_active()
    if not active_ids:
        return

    removed = 0
    for user_id in active_ids:
        if is_user_allowed(int(user_id)):
            continue
        uid = str(user_id)
        logger.info("purge_tracking_disallowed", user_id=user_id)
        await tracking_store.unmark_active(user_id)
        clear_tracking_started(user_id)
        ev = stop_flags.pop(uid, None)
        if ev is not None:
            ev.set()
        client = active_clients.pop(uid, None)
        if client is not None:
            await _safe_disconnect(client)
        removed += 1

    if removed:
        logger.info("purge_tracking_disallowed_done", count=removed)
