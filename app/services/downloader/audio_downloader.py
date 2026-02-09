import asyncio
import logging
import os

from app.core.config import AppConfig
from app.services.downloader.download_manager import DownloadResult

logger = logging.getLogger(__name__)


class AudioDownloader:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._save_dir = config.save_dir

    async def download(
        self,
        url: str,
        format_id: str = "mp3",
        quality: str = "192",
        user_id: int = 0,
    ) -> DownloadResult:
        opts = {
            "outtmpl": os.path.join(self._save_dir, "%(title).100s_%(id)s.%(ext)s"),
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": format_id,
                "preferredquality": quality,
            }],
        }

        try:
            result = await asyncio.to_thread(self._sync_download, url, opts)
            return DownloadResult(
                **{**result.__dict__, "media_type": "audio"}
            )
        except Exception as e:
            logger.error("Audio download error for %s: %s", url, e)
            return DownloadResult(error=str(e), media_type="audio")

    def _sync_download(self, url: str, opts: dict) -> DownloadResult:
        from yt_dlp import YoutubeDL

        downloaded_files = []

        def progress_hook(d):
            if d["status"] == "finished":
                filepath = d.get("filename", "")
                if filepath:
                    downloaded_files.append(filepath)

        opts["progress_hooks"] = [progress_hook]

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            return DownloadResult(error="No info extracted")

        title = info.get("title", "")

        if not downloaded_files:
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            for ext in [".mp3", ".m4a", ".opus", ".ogg", ".flac", ".wav"]:
                candidate = base + ext
                if os.path.exists(candidate):
                    downloaded_files.append(candidate)
                    break

        total_size = sum(os.path.getsize(f) for f in downloaded_files if os.path.exists(f))

        return DownloadResult(
            success=bool(downloaded_files),
            files=downloaded_files,
            title=title,
            file_size=total_size,
        )
