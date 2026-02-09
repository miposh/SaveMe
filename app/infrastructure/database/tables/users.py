import json
import logging
from datetime import datetime

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class UsersTable(BaseTable):

    async def sync_telegram_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None = None,
        language_code: str = "en",
        is_premium: bool = False,
    ) -> SingleQueryResult:
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO users (id, username, first_name, last_name, language_code, is_premium, last_activity)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    language_code = EXCLUDED.language_code,
                    is_premium = EXCLUDED.is_premium,
                    last_activity = NOW()
                RETURNING *
            """,
            params=(user_id, username, first_name, last_name, language_code, is_premium),
        )

    async def get_user(self, user_id: int) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM users WHERE id = %s",
            params=(user_id,),
        )

    async def get_by_username(self, username: str) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM users WHERE username = %s",
            params=(username,),
        )

    async def get_all_users(self) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM users ORDER BY created_at DESC",
        )

    async def get_users_count(self) -> int:
        result = await self._connection.fetchone(
            sql="SELECT COUNT(*) as count FROM users",
        )
        return result.data.get("count", 0) if result else 0

    async def get_users_by_period(self, period: str) -> int:
        intervals = {"day": "1 day", "week": "7 days", "month": "30 days"}
        interval = intervals.get(period, "1 day")
        result = await self._connection.fetchone(
            sql=f"SELECT COUNT(*) as count FROM users WHERE created_at >= NOW() - INTERVAL '{interval}'",
        )
        return result.data.get("count", 0) if result else 0

    async def ban_user(self, user_id: int, reason: str | None = None, until: datetime | None = None) -> SingleQueryResult:
        return await self._connection.update_and_fetchone(
            sql="""
                UPDATE users SET is_banned = TRUE, ban_reason = %s, ban_until = %s
                WHERE id = %s RETURNING *
            """,
            params=(reason, until, user_id),
        )

    async def unban_user(self, user_id: int) -> SingleQueryResult:
        return await self._connection.update_and_fetchone(
            sql="""
                UPDATE users SET is_banned = FALSE, ban_reason = NULL, ban_until = NULL
                WHERE id = %s RETURNING *
            """,
            params=(user_id,),
        )

    async def is_banned(self, user_id: int) -> bool:
        result = await self._connection.fetchone(
            sql="SELECT is_banned, ban_until FROM users WHERE id = %s",
            params=(user_id,),
        )
        if not result or result.is_empty():
            return False
        if result.data.get("ban_until"):
            ban_until = result.data["ban_until"]
            if isinstance(ban_until, datetime) and ban_until < datetime.now(ban_until.tzinfo):
                await self.unban_user(user_id)
                return False
        return result.data.get("is_banned", False)

    async def increment_downloads(self, user_id: int, media_type: str = "video") -> None:
        column_map = {
            "video": "count_downloads",
            "audio": "count_audio",
            "image": "count_images",
            "playlist": "count_playlists",
        }
        column = column_map.get(media_type, "count_downloads")
        await self._connection.execute(
            sql=f"UPDATE users SET {column} = {column} + 1 WHERE id = %s",
            params=(user_id,),
        )

    async def update_preferences(self, user_id: int, **kwargs) -> SingleQueryResult:
        if not kwargs:
            return await self.get_user(user_id)

        set_clauses = []
        params = []
        for key, value in kwargs.items():
            if key == "custom_args":
                set_clauses.append(f"{key} = %s::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        params.append(user_id)
        set_sql = ", ".join(set_clauses)

        return await self._connection.update_and_fetchone(
            sql=f"UPDATE users SET {set_sql} WHERE id = %s RETURNING *",
            params=tuple(params),
        )

    async def get_active_users(self, days: int = 7) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM users WHERE last_activity >= NOW() - INTERVAL '%s days' AND is_banned = FALSE",
            params=(days,),
        )

    async def get_all_user_ids(self) -> list[int]:
        result = await self._connection.fetchmany(
            sql="SELECT id FROM users WHERE is_banned = FALSE",
        )
        return [row["id"] for row in result.data] if result else []
