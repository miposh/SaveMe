import asyncio
import logging
import os
import subprocess

from app.core.config import AppConfig
from app.services.downloader.download_manager import DownloadResult

logger = logging.getLogger(__name__)


class GalleryDlDownloader:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._save_dir = config.save_dir

    async def download(
        self,
        url: str,
        max_count: int = 0,
        user_id: int = 0,
    ) -> DownloadResult:
        if max_count <= 0:
            max_count = self._config.limits.max_img_files

        try:
            result = await asyncio.to_thread(
                self._sync_download, url, max_count
            )
            return result
        except Exception as e:
            logger.error("gallery-dl error for %s: %s", url, e)
            return DownloadResult(error=str(e), media_type="image")

    def _sync_download(self, url: str, max_count: int) -> DownloadResult:
        output_dir = os.path.join(self._save_dir, "gallery_dl")
        os.makedirs(output_dir, exist_ok=True)

        cmd = [
            "gallery-dl",
            "--dest", output_dir,
            "--range", f"1-{max_count}",
            "--no-mtime",
            url,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.limits.max_img_total_wait_time,
            )
        except subprocess.TimeoutExpired:
            return DownloadResult(error="Download timed out", media_type="image")

        downloaded_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                fp = os.path.join(root, f)
                downloaded_files.append(fp)

        downloaded_files.sort()

        if max_count > 0:
            downloaded_files = downloaded_files[:max_count]

        total_size = sum(os.path.getsize(f) for f in downloaded_files if os.path.exists(f))

        return DownloadResult(
            success=bool(downloaded_files),
            files=downloaded_files,
            file_size=total_size,
            media_type="image",
            error="" if downloaded_files else "No files downloaded",
        )
