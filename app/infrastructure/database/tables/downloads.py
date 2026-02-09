import logging

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class DownloadsTable(BaseTable):

    async def add(
        self,
        user_id: int,
        url: str,
        url_hash: str,
        domain: str | None = None,
        title: str | None = None,
        duration_sec: int | None = None,
        file_size_bytes: int | None = None,
        quality: str | None = None,
        media_type: str = "video",
        telegram_file_id: str | None = None,
        telegram_msg_id: int | None = None,
        is_nsfw: bool = False,
        is_playlist: bool = False,
        playlist_index: int | None = None,
    ) -> SingleQueryResult:
        video_url = url if media_type == "video" else ""
        audio_url = url if media_type == "audio" else ""
        image_url = url if media_type == "image" else ""
        video_title = title or ""

        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO downloads (
                    user_id, url, url_hash, domain, title, duration_sec,
                    file_size_bytes, quality, media_type, telegram_file_id,
                    telegram_msg_id, is_nsfw, is_playlist, playlist_index,
                    video_url, audio_url, image_url, video_title, download_type, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """,
            params=(
                user_id, url, url_hash, domain, title, duration_sec,
                file_size_bytes, quality, media_type, telegram_file_id,
                telegram_msg_id, is_nsfw, is_playlist, playlist_index,
                video_url, audio_url, image_url, video_title, media_type, "pending",
            ),
        )

    async def get_by_user(self, user_id: int, limit: int = 50) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="SELECT * FROM downloads WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            params=(user_id, limit),
        )

    async def get_count_by_period(self, period: str) -> int:
        intervals = {"day": "1 day", "week": "7 days", "month": "30 days"}
        interval = intervals.get(period, "1 day")
        result = await self._connection.fetchone(
            sql=f"SELECT COUNT(*) as count FROM downloads WHERE created_at >= NOW() - INTERVAL '{interval}'",
        )
        return result.data.get("count", 0) if result else 0

    async def get_total_count(self) -> int:
        result = await self._connection.fetchone(
            sql="SELECT COUNT(*) as count FROM downloads",
        )
        return result.data.get("count", 0) if result else 0

    async def get_top_domains(self, limit: int = 10) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="""
                SELECT domain, COUNT(*) as count
                FROM downloads
                WHERE domain IS NOT NULL
                GROUP BY domain
                ORDER BY count DESC
                LIMIT %s
            """,
            params=(limit,),
        )
