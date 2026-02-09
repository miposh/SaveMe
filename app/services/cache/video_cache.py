import hashlib
import logging

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


class VideoCacheService:

    def __init__(self, db: DB) -> None:
        self._db = db

    async def get_cached(self, url: str, quality: str) -> dict | None:
        h = url_hash(url)
        result = await self._db.video_cache.get_cached(h, quality)
        row = result.as_dict()
        if row:
            logger.info("Cache hit: url_hash=%s, quality=%s", h, quality)
            return row
        return None

    async def get_cached_msg_ids(self, url: str, quality: str) -> list[int] | None:
        cached = await self.get_cached(url, quality)
        if not cached:
            return None

        msg_ids = cached.get("telegram_msg_ids")
        if isinstance(msg_ids, list) and msg_ids:
            return [int(mid) for mid in msg_ids]

        file_id = cached.get("telegram_file_id")
        if file_id:
            return None

        return None

    async def save(
        self,
        url: str,
        quality: str,
        telegram_file_id: str,
        telegram_msg_ids: list[int] | None = None,
        title: str | None = None,
        duration_sec: int | None = None,
        file_size_bytes: int | None = None,
    ) -> None:
        h = url_hash(url)
        try:
            await self._db.video_cache.save_cache(
                url_hash=h,
                quality=quality,
                telegram_file_id=telegram_file_id,
                telegram_msg_ids=telegram_msg_ids,
                title=title,
                duration_sec=duration_sec,
                file_size_bytes=file_size_bytes,
            )
            logger.info("Saved to cache: url_hash=%s, quality=%s", h, quality)
        except Exception as e:
            logger.error("Failed to save cache: %s", e)

    async def save_playlist_entry(
        self,
        playlist_url: str,
        video_url: str,
        quality: str,
        telegram_file_id: str,
        telegram_msg_ids: list[int] | None = None,
        title: str | None = None,
        playlist_index: int | None = None,
    ) -> None:
        h = url_hash(video_url)
        try:
            await self._db.video_cache.save_cache(
                url_hash=h,
                quality=quality,
                telegram_file_id=telegram_file_id,
                telegram_msg_ids=telegram_msg_ids,
                title=title,
                is_playlist=True,
                playlist_url=playlist_url,
                playlist_index=playlist_index,
            )
            logger.info(
                "Saved playlist entry: url_hash=%s, index=%s, quality=%s",
                h, playlist_index, quality,
            )
        except Exception as e:
            logger.error("Failed to save playlist cache entry: %s", e)

    async def get_playlist_cache(self, playlist_url: str) -> list[dict]:
        result = await self._db.video_cache.get_playlist_cache(playlist_url)
        rows = result.as_dicts()
        return rows if rows else []

    async def invalidate(self, url: str, quality: str | None = None) -> int:
        h = url_hash(url)
        try:
            count = await self._db.video_cache.invalidate(h, quality)
            logger.info("Invalidated cache: url_hash=%s, quality=%s", h, quality)
            return count
        except Exception as e:
            logger.error("Failed to invalidate cache: %s", e)
            return 0
