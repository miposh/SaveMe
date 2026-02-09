import json
import logging

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class StatisticsTable(BaseTable):

    async def record_event(
        self,
        event_type: str,
        user_id: int | None = None,
        url: str | None = None,
        domain: str | None = None,
        metadata: dict | None = None,
    ) -> SingleQueryResult:
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO statistics (user_id, event_type, url, domain, metadata)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                RETURNING *
            """,
            params=(user_id, event_type, url, domain, json.dumps(metadata or {})),
        )

    async def get_events_by_type(self, event_type: str, limit: int = 100) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM statistics WHERE event_type = %s ORDER BY created_at DESC LIMIT %s",
            params=(event_type, limit),
        )

    async def get_count_by_type_and_period(self, event_type: str, period: str) -> int:
        intervals = {"day": "1 day", "week": "7 days", "month": "30 days"}
        interval = intervals.get(period, "1 day")
        result = await self._connection.fetchone(
            sql=f"""
                SELECT COUNT(*) as count FROM statistics
                WHERE event_type = %s AND created_at >= NOW() - INTERVAL '{interval}'
            """,
            params=(event_type,),
        )
        return result.data.get("count", 0) if result else 0
