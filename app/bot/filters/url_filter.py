import re

from aiogram.filters import BaseFilter
from aiogram.types import Message

YOUTUBE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/|v/)|youtu\.be/)"
    r"[\w\-]{11}"
)


class YouTubeURLFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict:
        if not message.text:
            return False

        match = YOUTUBE_URL_PATTERN.search(message.text)
        if match:
            return {"youtube_url": match.group(0)}
        return False


def extract_youtube_url(text: str) -> str | None:
    match = YOUTUBE_URL_PATTERN.search(text)
    if match:
        return match.group(0)
    return None
