import logging
from datetime import datetime

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult

logger = logging.getLogger(__name__)


class RateLimitsTable(BaseTable):

    async def get_rate_limit(self, user_id: int, period: str) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM rate_limits WHERE user_id = %s AND period = %s",
            params=(user_id, period),
        )

    async def increment_or_create(self, user_id: int, period: str, window_seconds: int) -> SingleQueryResult:
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO rate_limits (user_id, period, request_count, window_start)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (user_id, period) DO UPDATE SET
                    request_count = CASE
                        WHEN rate_limits.window_start + INTERVAL '1 second' * %s < NOW()
                        THEN 1
                        ELSE rate_limits.request_count + 1
                    END,
                    window_start = CASE
                        WHEN rate_limits.window_start + INTERVAL '1 second' * %s < NOW()
                        THEN NOW()
                        ELSE rate_limits.window_start
                    END
                RETURNING *
            """,
            params=(user_id, period, window_seconds, window_seconds),
        )

    async def set_cooldown(self, user_id: int, period: str, cooldown_until: datetime) -> SingleQueryResult:
        return await self._connection.update_and_fetchone(
            sql="""
                UPDATE rate_limits SET cooldown_until = %s
                WHERE user_id = %s AND period = %s
                RETURNING *
            """,
            params=(cooldown_until, user_id, period),
        )

    async def is_on_cooldown(self, user_id: int, period: str) -> bool:
        result = await self._connection.fetchone(
            sql="""
                SELECT cooldown_until FROM rate_limits
                WHERE user_id = %s AND period = %s AND cooldown_until > NOW()
            """,
            params=(user_id, period),
        )
        return bool(result) and not result.is_empty()

    async def clear_cooldown(self, user_id: int, period: str) -> None:
        await self._connection.execute(
            sql="UPDATE rate_limits SET cooldown_until = NULL WHERE user_id = %s AND period = %s",
            params=(user_id, period),
        )
