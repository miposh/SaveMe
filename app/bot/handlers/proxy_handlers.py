import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_config

logger = logging.getLogger(__name__)

proxy_router = Router()
proxy_router.message.filter(F.chat.type == "private")


@proxy_router.message(Command("proxy"))
async def cmd_proxy(message: Message) -> None:
    config = get_config()

    proxy_1 = config.proxy.proxy_1_url
    proxy_2 = config.proxy.proxy_2_url
    select = config.proxy.proxy_select

    text = (
        "<b>Proxy Configuration</b>\n\n"
        f"Selection mode: {select}\n\n"
        f"Proxy 1: {'configured' if proxy_1 else 'not set'}\n"
        f"Proxy 2: {'configured' if proxy_2 else 'not set'}"
    )
    await message.answer(text)
