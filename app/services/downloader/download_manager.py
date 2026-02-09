import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass, field

from app.core.config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    success: bool = False
    files: list[str] = field(default_factory=list)
    title: str = ""
    duration: int = 0
    file_size: int = 0
    error: str = ""
    media_type: str = "video"
    is_playlist: bool = False
    thumbnail: str | None = None


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


class DownloadManager:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._save_dir = config.save_dir
        os.makedirs(self._save_dir, exist_ok=True)

    async def download_video(
        self,
        url: str,
        quality: str = "best",
        user_id: int = 0,
    ) -> DownloadResult:
        try:
            from app.services.downloader.ytdlp_downloader import YtdlpDownloader

            downloader = YtdlpDownloader(self._config)
            return await downloader.download(url, quality=quality, user_id=user_id)
        except Exception as e:
            logger.error("Download failed for %s: %s", url, e)
            return DownloadResult(error=str(e))

    async def download_audio(
        self,
        url: str,
        user_id: int = 0,
    ) -> DownloadResult:
        try:
            from app.services.downloader.audio_downloader import AudioDownloader

            downloader = AudioDownloader(self._config)
            return await downloader.download(url, user_id=user_id)
        except Exception as e:
            logger.error("Audio download failed for %s: %s", url, e)
            return DownloadResult(error=str(e))

    async def download_images(
        self,
        url: str,
        count: int = 0,
        user_id: int = 0,
    ) -> DownloadResult:
        try:
            from app.services.downloader.gallery_dl_downloader import GalleryDlDownloader

            downloader = GalleryDlDownloader(self._config)
            return await downloader.download(url, max_count=count, user_id=user_id)
        except Exception as e:
            logger.error("Image download failed for %s: %s", url, e)
            return DownloadResult(error=str(e))

    async def download_playlist(
        self,
        url: str,
        indices: str | None = None,
        user_id: int = 0,
    ) -> DownloadResult:
        try:
            from app.services.downloader.ytdlp_downloader import YtdlpDownloader

            downloader = YtdlpDownloader(self._config)
            return await downloader.download_playlist(url, indices=indices, user_id=user_id)
        except Exception as e:
            logger.error("Playlist download failed for %s: %s", url, e)
            return DownloadResult(error=str(e))

    def cleanup_files(self, files: list[str]) -> None:
        for f in files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError as e:
                logger.warning("Failed to remove %s: %s", f, e)
