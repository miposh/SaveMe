import logging
from datetime import datetime, timedelta

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class StatsService:

    def __init__(self, db: DB) -> None:
        self._db = db

    async def record_event(
        self,
        user_id: int,
        event_type: str,
        url: str | None = None,
        domain: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            await self._db.statistics.record_event(
                user_id=user_id,
                event_type=event_type,
                url=url,
                domain=domain,
                metadata=metadata,
            )
        except Exception as e:
            logger.error("Failed to record event: %s", e)

    async def record_download(
        self,
        user_id: int,
        url: str,
        domain: str,
        quality: str | None = None,
        media_type: str = "video",
    ) -> None:
        await self.record_event(
            user_id=user_id,
            event_type="download",
            url=url,
            domain=domain,
            metadata={
                "quality": quality,
                "media_type": media_type,
            },
        )

    async def record_command(self, user_id: int, command: str) -> None:
        await self.record_event(
            user_id=user_id,
            event_type="command",
            metadata={"command": command},
        )

    async def get_total_downloads(self, days: int | None = None) -> int:
        try:
            result = await self._db.statistics.get_events_by_type("download")
            rows = result.as_dicts()
            if not rows:
                return 0
            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                return sum(
                    1 for r in rows
                    if r.get("created_at") and r["created_at"] >= cutoff
                )
            return len(rows)
        except Exception as e:
            logger.error("Failed to get download count: %s", e)
            return 0

    async def get_top_domains(self, limit: int = 10) -> list[dict]:
        try:
            result = await self._db.downloads.get_top_domains(limit=limit)
            return result.as_dicts() or []
        except Exception as e:
            logger.error("Failed to get top domains: %s", e)
            return []

    async def get_active_users_count(self, days: int = 7) -> int:
        try:
            result = await self._db.users.get_active_users(days=days)
            rows = result.as_dicts()
            return len(rows) if rows else 0
        except Exception as e:
            logger.error("Failed to get active users count: %s", e)
            return 0
