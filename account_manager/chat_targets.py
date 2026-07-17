"""Разрешение ссылок на чаты в цели Telethon и проверка участия аккаунта."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)
from telethon import types, utils as tg_utils
from telethon.errors import (
    ChannelPrivateError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    InviteRequestSentError,
    UserAlreadyParticipantError,
)
from telethon.tl.functions.channels import GetParticipantRequest, JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import Channel, ChatInviteAlready, InputPeerSelf

from account_manager.join_result import JoinResult
from core.membership_status import (
    REASON_CHECK_FAILED,
    REASON_INVALID_REF,
    REASON_INVITE_EXPIRED,
    REASON_NOT_MEMBER,
    REASON_PENDING_APPROVAL,
    REASON_PRIVATE,
    REASON_UNKNOWN,
)
from core.telegram_utils import chat_ref_label, normalize_telegram_chat_ref


async def get_subscribed_refs(client) -> tuple[set[str], set[int]]:
    """@username и peer_id чатов из диалогов подключённого аккаунта."""
    usernames: set[str] = set()
    peer_ids: set[int] = set()

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, types.User):
            continue
        username = getattr(entity, "username", None)
        if username:
            usernames.add(f"@{username.lower()}")
        try:
            peer_ids.add(tg_utils.get_peer_id(entity))
        except Exception:
            if getattr(entity, "id", None) is not None:
                peer_ids.add(entity.id)

    return usernames, peer_ids


async def resolve_chat_ref(client, ref: str) -> str | int | None:
    """
    Преобразует каноническую ссылку в цель для events.NewMessage(chats=...).
    """
    canonical = normalize_telegram_chat_ref(ref) or ref

    if canonical.startswith("@"):
        return canonical

    if canonical.startswith("invite:"):
        invite_hash = canonical[7:]
        try:
            checked = await client(CheckChatInviteRequest(invite_hash))
            if isinstance(checked, ChatInviteAlready) and getattr(checked, "chat", None) is not None:
                return tg_utils.get_peer_id(checked.chat)
            chat = getattr(checked, "chat", None)
            if chat is not None:
                return tg_utils.get_peer_id(chat)
        except UserAlreadyParticipantError:
            pass
        except Exception:
            try:
                updates = await client(ImportChatInviteRequest(invite_hash))
                chats = getattr(updates, "chats", None) or []
                if chats:
                    return tg_utils.get_peer_id(chats[0])
            except UserAlreadyParticipantError:
                try:
                    checked = await client(CheckChatInviteRequest(invite_hash))
                    if isinstance(checked, ChatInviteAlready) and getattr(checked, "chat", None) is not None:
                        return tg_utils.get_peer_id(checked.chat)
                except Exception as e:
                    logger.warning(f"Не удалось получить чат по invite {chat_ref_label(canonical)}: {e}")
                    return None
            except (InviteHashExpiredError, InviteHashInvalidError) as e:
                logger.warning(f"Невалидная invite-ссылка {chat_ref_label(canonical)}: {e}")
                return None
            except Exception as e:
                logger.warning(f"Не удалось вступить по invite {chat_ref_label(canonical)}: {e}")
                return None

        logger.warning(f"Не удалось разрешить invite {chat_ref_label(canonical)}")
        return None

    if canonical.startswith("id:"):
        chat_id = int(canonical[3:])
        try:
            entity = await client.get_entity(chat_id)
            return tg_utils.get_peer_id(entity)
        except Exception as e:
            logger.warning(f"Не удалось получить чат {chat_id}: {e}")
            return None

    return None


async def resolve_tracking_targets(client, refs: list[str]) -> list[str | int]:
    targets: list[str | int] = []
    seen: set[tuple] = set()

    for ref in refs:
        canonical = normalize_telegram_chat_ref(ref) or ref
        target = await resolve_chat_ref(client, canonical)
        if target is None:
            logger.warning(f"⚠️ Пропущен чат (не разрешён): {chat_ref_label(canonical)}")
            continue

        key = ("int", target) if isinstance(target, int) else ("str", target.lower())
        if key in seen:
            continue
        seen.add(key)
        targets.append(target)

    return targets


async def is_member_of_ref(client, ref: str, subscribed_usernames: set[str], subscribed_peer_ids: set[int]) -> bool:
    canonical = normalize_telegram_chat_ref(ref) or ref

    if canonical.startswith("@"):
        key = canonical.lower()
        if key in subscribed_usernames:
            return True
        try:
            entity = await client.get_entity(canonical)
            if not isinstance(entity, Channel):
                return tg_utils.get_peer_id(entity) in subscribed_peer_ids
            await client(GetParticipantRequest(entity, InputPeerSelf()))
            return True
        except Exception:
            return False

    if canonical.startswith("id:"):
        chat_id = int(canonical[3:])
        if chat_id in subscribed_peer_ids:
            return True
        try:
            entity = await client.get_entity(chat_id)
            await client(GetParticipantRequest(entity, InputPeerSelf()))
            return True
        except Exception:
            return False

    if canonical.startswith("invite:"):
        invite_hash = canonical[7:]
        try:
            checked = await client(CheckChatInviteRequest(invite_hash))
            if getattr(checked, "chat", None) is not None:
                return True
            return False
        except UserAlreadyParticipantError:
            return True
        except Exception:
            return False

    return False


async def probe_missing_reason(client, ref: str) -> str:
    """
    Уточняет причину «не в канале» без повторного JoinChannel.
    """
    canonical = normalize_telegram_chat_ref(ref) or ref

    if canonical.startswith("@"):
        try:
            entity = await client.get_entity(canonical)
            if isinstance(entity, Channel) and getattr(entity, "join_request", False):
                return REASON_PENDING_APPROVAL
            return REASON_NOT_MEMBER
        except ChannelPrivateError:
            return REASON_PRIVATE
        except Exception:
            return REASON_NOT_MEMBER

    if canonical.startswith("invite:"):
        invite_hash = canonical[7:]
        try:
            checked = await client(CheckChatInviteRequest(invite_hash))
            if getattr(checked, "request_needed", False):
                return REASON_PENDING_APPROVAL
            return REASON_NOT_MEMBER
        except (InviteHashExpiredError, InviteHashInvalidError):
            return REASON_INVITE_EXPIRED
        except UserAlreadyParticipantError:
            return REASON_NOT_MEMBER
        except Exception:
            return REASON_NOT_MEMBER

    if canonical.startswith("id:"):
        try:
            entity = await client.get_entity(int(canonical[3:]))
            await client(GetParticipantRequest(entity, InputPeerSelf()))
            return REASON_NOT_MEMBER
        except ChannelPrivateError:
            return REASON_PRIVATE
        except Exception:
            return REASON_NOT_MEMBER

    return REASON_UNKNOWN


async def check_channels_membership(
    client,
    channels: list[str],
    *,
    delay_sec: float = 0.15,
) -> dict:
    """
    Сверяет список каналов с подписками активного аккаунта.
    Возвращает: ok, missing, errors, reasons (каноническая ссылка → код причины).
    """
    import asyncio

    subscribed_usernames, subscribed_peer_ids = await get_subscribed_refs(client)
    ok: list[str] = []
    missing: list[str] = []
    errors: list[str] = []
    reasons: dict[str, str] = {}

    for raw in channels:
        canonical = normalize_telegram_chat_ref(raw) or (raw or "").strip()
        if not canonical:
            errors.append(str(raw))
            reasons[str(raw)] = REASON_INVALID_REF
            continue
        try:
            if await is_member_of_ref(
                client, canonical, subscribed_usernames, subscribed_peer_ids
            ):
                ok.append(canonical)
            else:
                missing.append(canonical)
                reasons[canonical] = await probe_missing_reason(client, canonical)
        except Exception as e:
            logger.warning(
                "membership_check_error",
                channel=chat_ref_label(canonical),
                error=str(e),
            )
            errors.append(canonical)
            reasons[canonical] = REASON_CHECK_FAILED
        if delay_sec > 0:
            await asyncio.sleep(delay_sec)

    return {"ok": ok, "missing": missing, "errors": errors, "reasons": reasons}


async def join_chat_ref(client, ref: str) -> JoinResult:
    """
    Подписывает аккаунт на чат.
  """
    canonical = normalize_telegram_chat_ref(ref) or ref

    if canonical.startswith("@"):
        try:
            await client(JoinChannelRequest(canonical))
            return JoinResult("joined")
        except UserAlreadyParticipantError:
            return JoinResult("already")
        except InviteRequestSentError:
            return JoinResult("error", REASON_PENDING_APPROVAL)
        except ChannelPrivateError:
            return JoinResult("error", REASON_PRIVATE)
        except Exception as e:
            logger.warning(f"Не удалось подписаться на {canonical}: {e}")
            return JoinResult("error", REASON_UNKNOWN)

    if canonical.startswith("invite:"):
        invite_hash = canonical[7:]
        try:
            await client(ImportChatInviteRequest(invite_hash))
            return JoinResult("joined")
        except UserAlreadyParticipantError:
            return JoinResult("already")
        except InviteRequestSentError:
            return JoinResult("error", REASON_PENDING_APPROVAL)
        except (InviteHashExpiredError, InviteHashInvalidError) as e:
            logger.warning(f"Invite недействителен {chat_ref_label(canonical)}: {e}")
            return JoinResult("error", REASON_INVITE_EXPIRED)
        except Exception as e:
            logger.warning(f"Ошибка вступления по invite {chat_ref_label(canonical)}: {e}")
            return JoinResult("error", REASON_UNKNOWN)

    if canonical.startswith("id:"):
        if await is_member_of_ref(client, canonical, set(), set()):
            return JoinResult("already")
        logger.warning(
            f"Приватный чат {canonical} недоступен: аккаунт должен уже состоять в группе "
            f"или добавьте invite-ссылку"
        )
        return JoinResult("error", REASON_PRIVATE)

    return JoinResult("error", REASON_INVALID_REF)
