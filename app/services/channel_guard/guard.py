import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.core.config import AppConfig

logger = logging.getLogger(__name__)


class ChannelGuard:

    def __init__(self, bot: Bot, config: AppConfig) -> None:
        self._bot = bot
        self._config = config

    @property
    def channel_id(self) -> int:
        return self._config.channels.subscribe_channel_id

    @property
    def channel_url(self) -> str:
        return self._config.channels.subscribe_channel_url

    @property
    def enabled(self) -> bool:
        return bool(self.channel_id)

    async def is_subscribed(self, user_id: int) -> bool:
        if not self.enabled:
            return True

        try:
            member = await self._bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=user_id,
            )
            return member.status in ("creator", "administrator", "member")
        except TelegramForbiddenError:
            logger.warning(
                "Bot is not a member of channel %d, skipping subscription check",
                self.channel_id,
            )
            return True
        except Exception as e:
            logger.error("Failed to check subscription for %d: %s", user_id, e)
            return True
