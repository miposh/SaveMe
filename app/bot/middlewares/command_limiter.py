import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.core.config import LimitsConfig

logger = logging.getLogger(__name__)


class CommandLimiterMiddleware(BaseMiddleware):
    def __init__(self, limits: LimitsConfig) -> None:
        self.limits = limits
        self._user_commands: dict[int, list[float]] = {}
        self._user_cooldowns: dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        if not event.text or not event.text.startswith("/"):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()

        cooldown_until = self._user_cooldowns.get(user_id, 0)
        if now < cooldown_until:
            remaining = int(cooldown_until - now)
            await event.answer(f"Command spam detected. Wait {remaining}s.")
            return None

        timestamps = self._user_commands.get(user_id, [])
        timestamps = [t for t in timestamps if now - t < 60]
        timestamps.append(now)
        self._user_commands[user_id] = timestamps

        if len(timestamps) > self.limits.command_limit_per_minute:
            cooldown = self.limits.command_cooldown_initial
            self._user_cooldowns[user_id] = now + cooldown
            await event.answer(f"Too many commands. Cooldown: {cooldown}s.")
            return None

        return await handler(event, data)
