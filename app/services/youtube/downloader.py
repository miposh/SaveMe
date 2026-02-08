import asyncio
import logging
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

from app.config.config import settings
from app.services.youtube.models import VideoFormat, VideoInfo

logger = logging.getLogger(__name__)

PREFERRED_RESOLUTIONS = [2160, 1440, 1080, 720, 480, 360, 240, 144]

DOMAIN_COOKIE_MAP = {
    "youtube.com": "youtube.txt",
    "youtu.be": "youtube.txt",
    "instagram.com": "instagram.txt",
    "tiktok.com": "tiktok.txt",
    "twitter.com": "twitter.txt",
    "x.com": "twitter.txt",
    "vk.com": "vk.txt",
    "rutube.ru": "rutube.txt",
}


def _get_js_runtime_opts() -> dict:
    """Получает опции JS runtime для yt-dlp.
    
    Приоритет: node > deno > bun (node наиболее распространён).
    """
    for runtime in ("node", "deno", "bun"):
        if shutil.which(runtime):
            logger.debug("Using JS runtime: %s", runtime)
            return {"js_runtimes": {runtime: {}}}
    logger.warning("No JS runtime found, YouTube extraction may be limited")
    return {}


def _get_cookie_opts(url: str) -> dict:
    """
    Получает опции cookies для yt_dlp.
    
    Примечание: YouTube cookies часто устаревают и создают проблемы.
    Без cookies yt_dlp обычно работает лучше для публичных видео.
    """
    cookies_dir = Path(settings.get("cookies_dir", "./cookies"))

    if cookies_dir.exists():
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        # Пропускаем YouTube — cookies часто мешают
        if "youtube" in hostname or "youtu.be" in hostname:
            logger.debug("Skipping cookies for YouTube (public access works better)")
            return {}

        for domain, cookie_file in DOMAIN_COOKIE_MAP.items():
            if hostname == domain or hostname.endswith(f".{domain}"):
                path = cookies_dir / cookie_file
                if path.is_file():
                    logger.debug("Using cookies file: %s", path)
                    return {"cookiefile": str(path)}

        generic = cookies_dir / "cookies.txt"
        if generic.is_file():
            return {"cookiefile": str(generic)}

    return {}


def _base_opts(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    opts.update(_get_js_runtime_opts())
    opts.update(_get_cookie_opts(url))
    return opts


def _extract_info_sync(url: str) -> dict:
    ydl_opts = {
        **_base_opts(url),
        "extract_flat": False,
        "ignore_no_formats_error": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        logger.debug(
            "Extracted info for '%s': %d formats found",
            info.get("title", "Unknown"),
            len(info.get("formats", [])),
        )
        return info


def _parse_formats(info: dict) -> list[VideoFormat]:
    """Парсит доступные форматы видео.
    
    Поддерживает как обычные горизонтальные видео, так и вертикальные Shorts.
    Для вертикальных видео (width < height) используется width как показатель качества.
    """
    raw_formats = info.get("formats", [])
    duration = info.get("duration", 0) or 0

    logger.debug("Parsing formats: %d raw formats, duration=%ds", len(raw_formats), duration)

    # Определяем ориентацию видео по первому формату с размерами
    is_vertical = False
    for fmt in raw_formats:
        width = fmt.get("width") or 0
        height = fmt.get("height") or 0
        if width > 0 and height > 0:
            is_vertical = width < height
            logger.debug("Video orientation: %s (width=%d, height=%d)", 
                        "vertical" if is_vertical else "horizontal", width, height)
            break

    best_by_resolution: dict[int, dict] = {}

    for fmt in raw_formats:
        height = fmt.get("height") or 0
        width = fmt.get("width") or 0
        
        # Для вертикальных видео используем width как показатель качества
        resolution = width if is_vertical else height
        
        if resolution < 144:
            continue

        vcodec = fmt.get("vcodec", "none")
        if vcodec == "none":
            continue

        existing = best_by_resolution.get(resolution)
        current_tbr = fmt.get("tbr") or 0
        existing_tbr = (existing.get("tbr") or 0) if existing else 0

        if existing is None or current_tbr > existing_tbr:
            best_by_resolution[resolution] = fmt

    logger.debug(
        "Found video formats for resolutions: %s (vertical=%s)",
        sorted(best_by_resolution.keys(), reverse=True),
        is_vertical,
    )

    best_audio_size = 0
    for fmt in raw_formats:
        acodec = fmt.get("acodec", "none")
        vcodec = fmt.get("vcodec", "none")
        if acodec != "none" and vcodec == "none":
            size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
            if size > best_audio_size:
                best_audio_size = size

    if best_audio_size == 0 and duration > 0:
        best_audio_size = int(128 * 1024 / 8 * duration)

    logger.debug("Best audio size: %d bytes", best_audio_size)

    result = []
    
    # Собираем форматы: сначала проверяем стандартные разрешения, потом остальные
    matched_resolutions = set()
    
    for target_res in PREFERRED_RESOLUTIONS:
        fmt = best_by_resolution.get(target_res)
        if fmt is None:
            continue
        
        matched_resolutions.add(target_res)
        video_size = fmt.get("filesize") or fmt.get("filesize_approx")
        if video_size is None and fmt.get("tbr") and duration > 0:
            video_size = int(fmt["tbr"] * 1024 / 8 * duration)

        total_size = None
        if video_size:
            total_size = video_size + best_audio_size

        result.append(
            VideoFormat(
                height=target_res,  # Используем resolution как "качество"
                ext=fmt.get("ext", "mp4"),
                filesize=total_size,
                format_note=fmt.get("format_note"),
            )
        )
    
    # Если не нашли стандартные разрешения (например, для Shorts),
    # добавляем все доступные форматы
    if not result:
        for resolution in sorted(best_by_resolution.keys(), reverse=True):
            if resolution in matched_resolutions:
                continue
                
            fmt = best_by_resolution[resolution]
            video_size = fmt.get("filesize") or fmt.get("filesize_approx")
            if video_size is None and fmt.get("tbr") and duration > 0:
                video_size = int(fmt["tbr"] * 1024 / 8 * duration)

            total_size = None
            if video_size:
                total_size = video_size + best_audio_size

            result.append(
                VideoFormat(
                    height=resolution,  # Для Shorts это будет width
                    ext=fmt.get("ext", "mp4"),
                    filesize=total_size,
                    format_note=fmt.get("format_note"),
                )
            )

    logger.info(
        "Parsed %d available formats: %s",
        len(result),
        [f"{f.height}p ({f.filesize or 'N/A'} bytes)" for f in result],
    )

    return result


def _get_best_thumbnail(info: dict) -> str:
    thumbnails = info.get("thumbnails", [])
    if thumbnails:
        best = max(
            thumbnails,
            key=lambda t: (t.get("width", 0) or 0) * (t.get("height", 0) or 0),
        )
        return best.get("url", "")
    return info.get("thumbnail", "")


def _download_video_sync(url: str, format_height: int, output_dir: str) -> str:
    """Скачивает видео в указанном качестве.
    
    Args:
        url: URL видео
        format_height: Желаемое разрешение (height для обычных видео, width для Shorts)
        output_dir: Директория для сохранения
        
    Returns:
        Путь к скачанному файлу
    """
    # Формат выбора: пробуем сначала по height, потом по width (для Shorts)
    # Это покрывает как горизонтальные, так и вертикальные видео
    format_str = (
        f"bestvideo[height<={format_height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[width<={format_height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={format_height}]+bestaudio/"
        f"bestvideo[width<={format_height}]+bestaudio/"
        f"best[height<={format_height}]/"
        f"best[width<={format_height}]/"
        f"best"
    )

    ydl_opts = {
        **_base_opts(url),
        "format": format_str,
        "outtmpl": os.path.join(output_dir, "%(id)s_%(height)sp.%(ext)s"),
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def _download_audio_sync(url: str, output_dir: str) -> str:
    ydl_opts = {
        **_base_opts(url),
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id", "audio")
        mp3_path = os.path.join(output_dir, f"{video_id}.mp3")
        if os.path.exists(mp3_path):
            return mp3_path

        base = ydl.prepare_filename(info)
        name_without_ext = os.path.splitext(base)[0]
        return f"{name_without_ext}.mp3"


class YouTubeService:
    @staticmethod
    async def get_video_info(url: str) -> dict:
        info = await asyncio.to_thread(_extract_info_sync, url)

        formats = _parse_formats(info)
        thumbnail_url = _get_best_thumbnail(info)

        return {
            "video_id": info.get("id", ""),
            "title": info.get("title", "Unknown"),
            "channel": info.get("uploader", info.get("channel", "Unknown")),
            "thumbnail_url": thumbnail_url,
            "duration": info.get("duration", 0) or 0,
            "formats": [
                {
                    "height": f.height,
                    "ext": f.ext,
                    "filesize": f.filesize,
                    "format_note": f.format_note,
                }
                for f in formats
            ],
        }

    @staticmethod
    async def download_video(
        url: str, format_height: int, output_dir: str
    ) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return await asyncio.to_thread(
            _download_video_sync, url, format_height, output_dir
        )

    @staticmethod
    async def download_audio(url: str, output_dir: str) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return await asyncio.to_thread(_download_audio_sync, url, output_dir)
