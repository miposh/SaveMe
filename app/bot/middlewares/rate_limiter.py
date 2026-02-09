import logging
import re
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.core.config import LimitsConfig
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://\S+")


class RateLimiterMiddleware(BaseMiddleware):
    def __init__(self, limits: LimitsConfig) -> None:
        self.limits = limits
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        if not URL_PATTERN.search(event.text):
            return await handler(event, data)

        if not event.from_user:
            return await handler(event, data)

        db: DB | None = data.get("db")
        if db is None:
            return await handler(event, data)

        user_id = event.from_user.id
        is_group = data.get("is_group", False)
        multiplier = self.limits.group_multiplier if is_group else 1

        checks = [
            ("minute", 60, self.limits.rate_limit_per_minute // multiplier),
            ("hour", 3600, self.limits.rate_limit_per_hour // multiplier),
            ("day", 86400, self.limits.rate_limit_per_day // multiplier),
        ]

        for period, window, limit in checks:
            if await db.rate_limits.is_on_cooldown(user_id, period):
                await event.answer(f"Rate limited. Please wait before sending more URLs.")
                return None

            result = await db.rate_limits.increment_or_create(user_id, period, window)
            if result and not result.is_empty():
                count = result.data.get("request_count", 0)
                if count > limit:
                    cooldowns = {
                        "minute": self.limits.rate_limit_cooldown_minute,
                        "hour": self.limits.rate_limit_cooldown_hour,
                        "day": self.limits.rate_limit_cooldown_day,
                    }
                    from datetime import datetime, timedelta, timezone
                    cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=cooldowns[period])
                    await db.rate_limits.set_cooldown(user_id, period, cooldown_until)
                    await event.answer(f"Too many URLs. Cooldown: {cooldowns[period] // 60} min.")
                    return None

        return await handler(event, data)
