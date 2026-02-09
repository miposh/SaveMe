import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramRetryAfter as e:
            logger.warning("Rate limited, retry after %s seconds", e.retry_after)
            return None
        except TelegramForbiddenError as e:
            if "bot was kicked" in str(e) or "bot was blocked" in str(e):
                chat = getattr(event, "chat", None)
                chat_id = getattr(chat, "id", "unknown") if chat else "unknown"
                logger.warning("Bot blocked/kicked in chat %s", chat_id)
                return None
            raise
        except Exception as e:
            logger.exception("Unhandled error in handler: %s", e)
            raise
