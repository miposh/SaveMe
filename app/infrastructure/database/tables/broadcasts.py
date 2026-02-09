import logging
from datetime import datetime

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class BroadcastsTable(BaseTable):

    async def create(
        self,
        admin_id: int,
        text: str,
        media_file_id: str | None = None,
        media_type: str | None = None,
        url_buttons: str | None = None,
        segment: str = "all",
        scheduled_at: datetime | None = None,
        is_ab_test: bool = False,
        ab_variant: str | None = None,
        ab_parent_id: int | None = None,
    ) -> SingleQueryResult:
        status = "scheduled" if scheduled_at else "draft"
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO broadcasts (
                    admin_id, text, media_file_id, media_type, url_buttons,
                    segment, scheduled_at, status, is_ab_test, ab_variant, ab_parent_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """,
            params=(
                admin_id, text, media_file_id, media_type, url_buttons,
                segment, scheduled_at, status, is_ab_test, ab_variant, ab_parent_id,
            ),
        )

    async def get_scheduled(self) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="""
                SELECT * FROM broadcasts
                WHERE status = 'scheduled' AND scheduled_at <= NOW()
                ORDER BY scheduled_at
            """,
        )

    async def update_status(self, broadcast_id: int, status: str) -> SingleQueryResult:
        return await self._connection.update_and_fetchone(
            sql="UPDATE broadcasts SET status = %s WHERE id = %s RETURNING *",
            params=(status, broadcast_id),
        )

    async def update_stats(
        self,
        broadcast_id: int,
        total_recipients: int = 0,
        sent_count: int = 0,
        failed_count: int = 0,
        blocked_count: int = 0,
    ) -> SingleQueryResult:
        return await self._connection.update_and_fetchone(
            sql="""
                UPDATE broadcasts SET
                    total_recipients = %s, sent_count = %s,
                    failed_count = %s, blocked_count = %s,
                    completed_at = NOW(), status = 'completed'
                WHERE id = %s RETURNING *
            """,
            params=(total_recipients, sent_count, failed_count, blocked_count, broadcast_id),
        )

    async def get_history(self, limit: int = 20) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM broadcasts ORDER BY created_at DESC LIMIT %s",
            params=(limit,),
        )

    async def get_by_id(self, broadcast_id: int) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM broadcasts WHERE id = %s",
            params=(broadcast_id,),
        )
