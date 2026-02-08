import logging

from psycopg import AsyncConnection

from app.infrastructure.database.models.download import DownloadModel

logger = logging.getLogger(__name__)


class DownloadsTable:
    def __init__(self, connection: AsyncConnection) -> None:
        self._conn = connection

    async def add(
        self,
        user_id: int,
        video_url: str,
        video_title: str,
        download_type: str,
        quality: str | None = None,
    ) -> DownloadModel | None:
        query = """
            INSERT INTO downloads (user_id, video_url, video_title, download_type, quality)
            VALUES (%(user_id)s, %(video_url)s, %(video_title)s, %(download_type)s, %(quality)s)
            RETURNING *
        """
        result = await self._conn.execute(
            query,
            {
                "user_id": user_id,
                "video_url": video_url,
                "video_title": video_title,
                "download_type": download_type,
                "quality": quality,
            },
        )
        row = await result.fetchone()
        if row:
            return DownloadModel(**row)
        return None

    async def update_status(
        self,
        download_id: int,
        status: str,
        file_size: int | None = None,
    ) -> None:
        if file_size is not None:
            query = """
                UPDATE downloads
                SET status = %(status)s, file_size = %(file_size)s
                WHERE id = %(id)s
            """
            await self._conn.execute(
                query,
                {"id": download_id, "status": status, "file_size": file_size},
            )
        else:
            query = "UPDATE downloads SET status = %(status)s WHERE id = %(id)s"
            await self._conn.execute(
                query, {"id": download_id, "status": status}
            )

    async def get_user_downloads(
        self, user_id: int, limit: int = 20
    ) -> list[DownloadModel]:
        query = """
            SELECT * FROM downloads
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        result = await self._conn.execute(
            query, {"user_id": user_id, "limit": limit}
        )
        rows = await result.fetchall()
        return [DownloadModel(**row) for row in rows]
