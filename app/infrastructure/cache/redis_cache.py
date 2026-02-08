import json
import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None

VIDEO_INFO_TTL = 600
DOWNLOAD_LOCK_TTL = 300


async def get_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 1,
    password: str = "",
) -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=host,
            port=port,
            db=db,
            password=password or None,
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class VideoInfoCache:
    def __init__(self, client: aioredis.Redis) -> None:
        self._redis = client

    def _key(self, video_url: str) -> str:
        return f"saveme:video_info:{video_url}"

    async def get(self, video_url: str) -> dict[str, Any] | None:
        data = await self._redis.get(self._key(video_url))
        if data:
            return json.loads(data)
        return None

    async def set(self, video_url: str, info: dict[str, Any]) -> None:
        await self._redis.setex(
            self._key(video_url),
            VIDEO_INFO_TTL,
            json.dumps(info, ensure_ascii=False),
        )

    async def delete(self, video_url: str) -> None:
        await self._redis.delete(self._key(video_url))


class DownloadLock:
    def __init__(self, client: aioredis.Redis) -> None:
        self._redis = client

    def _key(self, chat_id: int, video_url: str) -> str:
        return f"saveme:download_lock:{chat_id}:{video_url}"

    async def acquire(self, chat_id: int, video_url: str) -> bool:
        key = self._key(chat_id, video_url)
        result = await self._redis.set(key, "1", ex=DOWNLOAD_LOCK_TTL, nx=True)
        return result is not None

    async def release(self, chat_id: int, video_url: str) -> None:
        await self._redis.delete(self._key(chat_id, video_url))
