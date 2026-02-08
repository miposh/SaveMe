import logging

from psycopg import AsyncConnection

from app.infrastructure.database.models.user import UserModel

logger = logging.getLogger(__name__)


class UsersTable:
    def __init__(self, connection: AsyncConnection) -> None:
        self._conn = connection

    async def add(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> UserModel | None:
        query = """
            INSERT INTO users (id, username, first_name, last_name, language_code)
            VALUES (%(id)s, %(username)s, %(first_name)s, %(last_name)s, %(language_code)s)
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                last_activity = NOW()
            RETURNING *
        """
        result = await self._conn.execute(
            query,
            {
                "id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": language_code,
            },
        )
        row = await result.fetchone()
        if row:
            return UserModel(**row)
        return None

    async def get_user(self, user_id: int) -> UserModel | None:
        query = "SELECT * FROM users WHERE id = %(id)s"
        result = await self._conn.execute(query, {"id": user_id})
        row = await result.fetchone()
        if row:
            return UserModel(**row)
        return None

    async def increment_downloads(self, user_id: int) -> None:
        query = """
            UPDATE users
            SET downloads_count = downloads_count + 1,
                last_activity = NOW()
            WHERE id = %(id)s
        """
        await self._conn.execute(query, {"id": user_id})
