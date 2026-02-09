import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

URL_REGEX = re.compile(r"https?://\S+")


class HasURL(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return bool(URL_REGEX.search(message.text))
