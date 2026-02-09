import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, TelegramObject

from app.core.config import ChannelConfig

logger = logging.getLogger(__name__)


class SubscriptionCheckMiddleware(BaseMiddleware):
    def __init__(self, channel_config: ChannelConfig | None = None) -> None:
        self._channel_id = channel_config.subscribe_channel_id if channel_config else 0
        self._channel_url = channel_config.subscribe_channel_url if channel_config else ""
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not self._channel_id:
            return await handler(event, data)

        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        if data.get("is_admin"):
            return await handler(event, data)

        bot: Bot = data["bot"]
        user_id = event.from_user.id

        try:
            member = await bot.get_chat_member(self._channel_id, user_id)
            if member.status in ("member", "administrator", "creator"):
                return await handler(event, data)
        except TelegramAPIError as e:
            logger.warning("Subscription check failed for user %s: %s", user_id, e)
            return await handler(event, data)

        subscribe_text = "Please subscribe to our channel first."
        if self._channel_url:
            subscribe_text = f"Please subscribe to our channel first: {self._channel_url}"

        await event.answer(subscribe_text)
        return None
