from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.infrastructure.database.db import DB


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, db: DB) -> bool:
        if not message.from_user:
            return False
        return await db.admins.is_admin(message.from_user.id)
