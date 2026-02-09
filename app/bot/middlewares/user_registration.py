import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class UserRegistrationMiddleware(BaseMiddleware):
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

        user = event.from_user
        try:
            await db.users.sync_telegram_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name or "",
                last_name=user.last_name,
                language_code=user.language_code or "en",
                is_premium=bool(user.is_premium),
            )
        except Exception as e:
            logger.error("Failed to sync user %s: %s", user.id, e)

        return await handler(event, data)
