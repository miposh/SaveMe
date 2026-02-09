from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.core.config import get_config


class AllowedGroup(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        config = get_config()
        allowed_ids = config.admin.allowed_group_ids
        if not allowed_ids:
            return True
        return message.chat.id in allowed_ids
