import logging

from app.infrastructure.database.tables.base import BaseTable
from app.infrastructure.database.query.results import SingleQueryResult, MultipleQueryResult

logger = logging.getLogger(__name__)


class VideoCacheTable(BaseTable):

    async def get_cached(self, url_hash: str, quality: str) -> SingleQueryResult:
        return await self._connection.fetchone(
            sql="SELECT * FROM video_cache WHERE url_hash = %s AND quality = %s",
            params=(url_hash, quality),
        )

    async def save_cache(
        self,
        url_hash: str,
        quality: str,
        telegram_file_id: str,
        telegram_msg_ids: list[int] | None = None,
        title: str | None = None,
        duration_sec: int | None = None,
        file_size_bytes: int | None = None,
        is_playlist: bool = False,
        playlist_url: str | None = None,
        playlist_index: int | None = None,
    ) -> SingleQueryResult:
        return await self._connection.insert_and_fetchone(
            sql="""
                INSERT INTO video_cache (
                    url_hash, quality, telegram_file_id, telegram_msg_ids,
                    title, duration_sec, file_size_bytes,
                    is_playlist, playlist_url, playlist_index
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url_hash, quality) DO UPDATE SET
                    telegram_file_id = EXCLUDED.telegram_file_id,
                    telegram_msg_ids = EXCLUDED.telegram_msg_ids
                RETURNING *
            """,
            params=(
                url_hash, quality, telegram_file_id, telegram_msg_ids or [],
                title, duration_sec, file_size_bytes,
                is_playlist, playlist_url, playlist_index,
            ),
        )

    async def get_playlist_cache(self, playlist_url: str) -> MultipleQueryResult:
        return await self._connection.fetchmany(
            sql="""
                SELECT * FROM video_cache
                WHERE is_playlist = TRUE AND playlist_url = %s
                ORDER BY playlist_index
            """,
            params=(playlist_url,),
        )

    async def invalidate(self, url_hash: str, quality: str | None = None) -> int:
        if quality:
            return await self._connection.execute(
                sql="DELETE FROM video_cache WHERE url_hash = %s AND quality = %s",
                params=(url_hash, quality),
            )
        return await self._connection.execute(
            sql="DELETE FROM video_cache WHERE url_hash = %s",
            params=(url_hash,),
        )
