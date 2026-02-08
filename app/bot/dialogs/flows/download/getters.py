import logging

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment

logger = logging.getLogger(__name__)


def _format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None or size_bytes == 0:
        return "~ N/A"
    mb = size_bytes / (1024 * 1024)
    if mb >= 1024:
        return f"~{mb / 1024:.1f} GB"
    return f"~{mb:.0f} MB"


async def video_info_getter(
    dialog_manager: DialogManager,
    **kwargs: dict,
) -> dict:
    start_data = dialog_manager.start_data

    title = start_data["title"]
    thumbnail_url = start_data["thumbnail_url"]
    duration = start_data.get("duration", 0)
    formats_data = start_data.get("formats", [])

    thumbnail = MediaAttachment(
        ContentType.PHOTO,
        url=thumbnail_url,
    )

    # Сортируем форматы по высоте (от меньшего к большему)
    sorted_formats = sorted(formats_data, key=lambda x: x["height"])

    formats_text_lines = []
    format_items = []

    for fmt in sorted_formats:
        height = fmt["height"]
        size = _format_size(fmt.get("filesize"))
        formats_text_lines.append(f"✅    {height}p:    {size}")
        format_items.append((f"{height}p", str(height)))

    duration_str = _format_duration(duration) if duration else ""

    info_text = (
        f"🎬 <b>{title}</b>\n"
        f"👤 <a href='#'>#{start_data.get('channel', 'Unknown')}</a>\n\n"
        + "\n".join(formats_text_lines)
    )

    return {
        "thumbnail": thumbnail,
        "info_text": info_text,
        "formats": format_items,
        "formats_count": len(format_items),
        "duration_str": duration_str,
    }

