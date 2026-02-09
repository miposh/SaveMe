import asyncio
import logging
import os
import tempfile

from app.core.config import AppConfig
from app.services.downloader.download_manager import DownloadResult

logger = logging.getLogger(__name__)


class YtdlpDownloader:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._save_dir = config.save_dir

    def _build_opts(
        self,
        quality: str = "best",
        audio_only: bool = False,
        playlist_indices: str | None = None,
    ) -> dict:
        output_template = os.path.join(self._save_dir, "%(title).100s_%(id)s.%(ext)s")

        opts = {
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "merge_output_format": "mp4",
            "socket_timeout": 60,
            "retries": 5,
            "fragment_retries": 5,
        }

        if audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        elif quality == "best":
            opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            opts["format"] = f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best"

        if playlist_indices:
            opts["playlist_items"] = playlist_indices

        timeout = self._config.limits.download_timeout
        if timeout:
            opts["socket_timeout"] = min(timeout, 600)

        return opts

    async def download(
        self,
        url: str,
        quality: str = "best",
        user_id: int = 0,
    ) -> DownloadResult:
        opts = self._build_opts(quality=quality)
        opts["noplaylist"] = True

        return await self._run_ytdlp(url, opts)

    async def download_playlist(
        self,
        url: str,
        indices: str | None = None,
        user_id: int = 0,
    ) -> DownloadResult:
        max_count = self._config.limits.max_playlist_count
        opts = self._build_opts(playlist_indices=indices)
        opts["playlistend"] = max_count

        result = await self._run_ytdlp(url, opts)
        return DownloadResult(
            **{**result.__dict__, "is_playlist": True, "media_type": "playlist"}
        )

    async def _run_ytdlp(self, url: str, opts: dict) -> DownloadResult:
        try:
            result = await asyncio.to_thread(self._sync_download, url, opts)
            return result
        except Exception as e:
            logger.error("yt-dlp error for %s: %s", url, e)
            return DownloadResult(error=str(e))

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
        duration = info.get("duration", 0) or 0

        # After merge, intermediate files are deleted by yt-dlp.
        # Find the actual final file(s) on disk.
        final_files = self._resolve_final_files(ydl, info, downloaded_files)

        total_size = sum(os.path.getsize(f) for f in final_files)

        return DownloadResult(
            success=bool(final_files),
            files=final_files,
            title=title,
            duration=duration,
            file_size=total_size,
            error="" if final_files else "No files downloaded",
        )

    def _resolve_final_files(
        self, ydl, info: dict, hook_files: list[str],
    ) -> list[str]:
        # First try: the expected merged output filename
        filename = ydl.prepare_filename(info)
        if os.path.exists(filename):
            return [filename]

        # Try common extensions (merge_output_format may change the ext)
        base, _ = os.path.splitext(filename)
        for ext in (".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".opus", ".ogg"):
            candidate = base + ext
            if os.path.exists(candidate):
                return [candidate]

        # Fallback: filter hook-captured files to those still on disk
        existing = [f for f in hook_files if os.path.exists(f)]
        if existing:
            return existing

        return []
