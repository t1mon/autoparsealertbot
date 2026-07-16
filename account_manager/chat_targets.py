"""Разрешение ссылок на чаты в цели Telethon и проверка участия аккаунта."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)
from telethon import types, utils as tg_utils
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError, UserAlreadyParticipantError
from telethon.tl.functions.channels import GetParticipantRequest, JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import Channel, ChatInviteAlready, InputPeerSelf

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


async def join_chat_ref(client, ref: str) -> str:
    """
    Подписывает аккаунт на чат.
    :return: joined | already | error
    """
    canonical = normalize_telegram_chat_ref(ref) or ref

    if canonical.startswith("@"):
        try:
            await client(JoinChannelRequest(canonical))
            return "joined"
        except UserAlreadyParticipantError:
            return "already"
        except Exception as e:
            logger.warning(f"Не удалось подписаться на {canonical}: {e}")
            return "error"

    if canonical.startswith("invite:"):
        invite_hash = canonical[7:]
        try:
            await client(ImportChatInviteRequest(invite_hash))
            return "joined"
        except UserAlreadyParticipantError:
            return "already"
        except (InviteHashExpiredError, InviteHashInvalidError) as e:
            logger.warning(f"Invite недействителен {chat_ref_label(canonical)}: {e}")
            return "error"
        except Exception as e:
            logger.warning(f"Ошибка вступления по invite {chat_ref_label(canonical)}: {e}")
            return "error"

    if canonical.startswith("id:"):
        if await is_member_of_ref(client, canonical, set(), set()):
            return "already"
        logger.warning(
            f"Приватный чат {canonical} недоступен: аккаунт должен уже состоять в группе "
            f"или добавьте invite-ссылку"
        )
        return "error"

    return "error"
