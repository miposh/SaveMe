import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class BlockCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        db: DB | None = data.get("db")
        if db is None:
            return await handler(event, data)

        try:
            is_banned = await db.users.is_banned(event.from_user.id)
            if is_banned:
                logger.info("Blocked user %s attempted access", event.from_user.id)
                return None
        except Exception as e:
            logger.error("Failed to check ban status for %s: %s", event.from_user.id, e)

        return await handler(event, data)
