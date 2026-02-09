import asyncio
import logging
import os

from app.core.config import AppConfig
from app.services.downloader.download_manager import DownloadResult

logger = logging.getLogger(__name__)


class LiveStreamDownloader:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._save_dir = config.save_dir

    async def download(
        self,
        url: str,
        duration_limit: int = 0,
        user_id: int = 0,
    ) -> DownloadResult:
        if duration_limit <= 0:
            duration_limit = self._config.limits.max_video_duration

        opts = {
            "outtmpl": os.path.join(self._save_dir, "%(title).100s_%(id)s.%(ext)s"),
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "live_from_start": True,
            "match_filter": f"duration < {duration_limit}",
        }

        try:
            result = await asyncio.to_thread(self._sync_download, url, opts)
            return result
        except Exception as e:
            logger.error("Live stream download error for %s: %s", url, e)
            return DownloadResult(error=str(e))

    def _sync_download(self, url: str, opts: dict) -> DownloadResult:
        from yt_dlp import YoutubeDL

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            return DownloadResult(error="No info extracted")

        filename = ydl.prepare_filename(info)
        files = [filename] if os.path.exists(filename) else []

        return DownloadResult(
            success=bool(files),
            files=files,
            title=info.get("title", ""),
            duration=info.get("duration", 0) or 0,
        )
