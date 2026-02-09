from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ChatTypeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            data["chat_type"] = event.chat.type
            data["is_private"] = event.chat.type == "private"
            data["is_group"] = event.chat.type in ("group", "supergroup")

        return await handler(event, data)
