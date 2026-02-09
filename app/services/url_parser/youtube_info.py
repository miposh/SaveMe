import asyncio
import html
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FormatInfo:
    format_id: str
    height: int
    width: int
    filesize: int
    ext: str
    vcodec: str = ""
    acodec: str = ""


@dataclass(frozen=True)
class YouTubeVideoInfo:
    video_id: str = ""
    title: str = ""
    channel: str = ""
    channel_follower_count: int = 0
    upload_date: str = ""
    duration: int = 0
    view_count: int = 0
    like_count: int = 0
    thumbnail: str = ""
    formats: tuple[FormatInfo, ...] = ()
    error: str = ""

    @property
    def has_error(self) -> bool:
        return bool(self.error)


def _format_subscriber_count(count: int) -> str:
    if count >= 1_000_000:
        value = f"{count / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{value}M"
    if count >= 1_000:
        return f"{count:,}"
    return str(count)


def _format_date(raw: str) -> str:
    if len(raw) == 8:
        return f"{raw[6:8]}.{raw[4:6]}.{raw[:4]}"
    return raw


def _format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "N/A"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h, {minutes:02d}m, {secs:02d}s"
    return f"{minutes}m, {secs:02d}s"


def _format_count(count: int) -> str:
    return f"{count:,}" if count else "N/A"


def _filesize_mb(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "?"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


def _extract_best_formats(raw_formats: list[dict]) -> tuple[FormatInfo, ...]:
    """Extract the best video-only format per unique height."""
    video_by_height: dict[int, FormatInfo] = {}

    for f in raw_formats:
        height = f.get("height") or 0
        width = f.get("width") or 0
        vcodec = f.get("vcodec") or "none"

        if height <= 0 or vcodec == "none":
            continue

        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        fmt = FormatInfo(
            format_id=f.get("format_id", ""),
            height=height,
            width=width,
            filesize=filesize,
            ext=f.get("ext", ""),
            vcodec=vcodec,
            acodec=f.get("acodec") or "",
        )

        existing = video_by_height.get(height)
        if existing is None or filesize > existing.filesize:
            video_by_height[height] = fmt

    return tuple(sorted(video_by_height.values(), key=lambda x: x.height))


async def fetch_youtube_info(url: str) -> YouTubeVideoInfo:
    def _sync_fetch(target_url: str) -> YouTubeVideoInfo:
        from yt_dlp import YoutubeDL

        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "noplaylist": True,
            "socket_timeout": 30,
        }
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
                if not info:
                    return YouTubeVideoInfo(error="No info extracted")

                raw_formats = info.get("formats") or []
                formats = _extract_best_formats(raw_formats)

                return YouTubeVideoInfo(
                    video_id=info.get("id", ""),
                    title=info.get("title", ""),
                    channel=info.get("channel", "") or info.get("uploader", ""),
                    channel_follower_count=info.get("channel_follower_count") or 0,
                    upload_date=info.get("upload_date", ""),
                    duration=info.get("duration") or 0,
                    view_count=info.get("view_count") or 0,
                    like_count=info.get("like_count") or 0,
                    thumbnail=info.get("thumbnail", ""),
                    formats=formats,
                )
        except Exception as e:
            logger.error("YouTube info fetch failed for %s: %s", target_url, e)
            return YouTubeVideoInfo(error=str(e))

    return await asyncio.to_thread(_sync_fetch, url)


def _sanitize_tag(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\u0400-\u04FF]", "", text.replace(" ", ""))


def build_preview_text(info: YouTubeVideoInfo) -> str:
    subs = _format_subscriber_count(info.channel_follower_count)
    date = _format_date(info.upload_date)
    dur = _format_duration(info.duration)
    views = _format_count(info.view_count)
    likes = _format_count(info.like_count)

    safe_channel = html.escape(info.channel)
    safe_title = html.escape(info.title)

    lines = [
        f"\U0001f4fa {safe_channel}",
        f"\U0001f465 {subs}",
        f"<b>{safe_title}</b>",
        f"\U0001f4c5 {date}  \u23f1\ufe0f {dur}",
        f"\U0001f441 {views}  \u2764\ufe0f {likes}",
    ]

    for fmt in info.formats:
        size = _filesize_mb(fmt.filesize)
        lines.append(f"\U0001f4f9{fmt.height}p:  {size} ({fmt.width}\u00d7{fmt.height})")

    channel_tag = _sanitize_tag(info.channel) if info.channel else "channel"
    lines.append(f"#youtube #{channel_tag}")

    return "\n".join(lines)
