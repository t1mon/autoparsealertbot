from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import BOT_TOKEN, PROXY_USER, PROXY_PASSWORD, PROXY_IP, PROXY_PORT, REDIS_URL

if REDIS_URL:
    from aiogram.fsm.storage.redis import RedisStorage

    storage = RedisStorage.from_url(REDIS_URL)
else:
    storage = MemoryStorage()

_session_kwargs = {}
if PROXY_IP and PROXY_PORT:
    auth = ""
    if PROXY_USER and PROXY_PASSWORD:
        auth = f"{PROXY_USER}:{PROXY_PASSWORD}@"
    _session_kwargs["proxy"] = f"http://{auth}{PROXY_IP}:{PROXY_PORT}"

session = AiohttpSession(**_session_kwargs)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(),
    session=session,
)

dp = Dispatcher(storage=storage)
