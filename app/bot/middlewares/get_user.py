import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class GetUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        db: DB = data.get("db")
        if db is None:
            return await handler(event, data)

        user = None
        if isinstance(event, Update) and event.event and hasattr(event.event, "from_user"):
            tg_user = event.event.from_user
            if tg_user:
                user = await db.users.add(
                    user_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    language_code=tg_user.language_code,
                )

        data["user_row"] = user
        return await handler(event, data)
