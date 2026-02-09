import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return None

        db: DB | None = data.get("db")
        if db is None:
            return None

        is_admin = await db.admins.is_admin(event.from_user.id)
        if not is_admin:
            return None

        data["is_admin"] = True
        return await handler(event, data)
