import logging

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class AdminsTable(BaseTable):

    async def add(self, admin_id: int, username: str | None = None, added_by: int | None = None) -> SingleQueryResult:
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO admins (id, username, added_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
                RETURNING *
            """,
            params=(admin_id, username, added_by),
        )

    async def remove(self, admin_id: int) -> int:
        return await self._connection.execute(
            sql="DELETE FROM admins WHERE id = %s",
            params=(admin_id,),
        )

    async def get_admin(self, admin_id: int) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM admins WHERE id = %s",
            params=(admin_id,),
        )

    async def is_admin(self, user_id: int) -> bool:
        result = await self._connection.fetchone(
            sql="SELECT EXISTS(SELECT 1 FROM admins WHERE id = %s) as is_admin",
            params=(user_id,),
        )
        return result.data.get("is_admin", False) if result else False

    async def get_all(self) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM admins ORDER BY added_at DESC",
        )
