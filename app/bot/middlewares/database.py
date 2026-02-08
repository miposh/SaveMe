import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from psycopg_pool import AsyncConnectionPool

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, pool: AsyncConnectionPool) -> None:
        super().__init__()
        self._pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self._pool.connection() as conn:
            data["db"] = DB(connection=conn)
            return await handler(event, data)
