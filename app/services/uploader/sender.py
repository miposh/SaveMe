import asyncio
import logging
import os

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.utils.media_group import MediaGroupBuilder

logger = logging.getLogger(__name__)

MEDIA_GROUP_LIMIT = 10
TELEGRAM_FILE_LIMIT_MB = 2048


def _is_chat_not_found(exc: Exception) -> bool:
    return "chat not found" in str(exc).lower()


async def send_files(
    bot: Bot,
    chat_id: int,
    files: list[str],
    caption: str = "",
    media_type: str = "video",
) -> list[int]:
    if not files:
        return []

    message_ids = []

    chunks = [files[i:i + MEDIA_GROUP_LIMIT] for i in range(0, len(files), MEDIA_GROUP_LIMIT)]

    for chunk_idx, chunk in enumerate(chunks):
        chunk_caption = caption if chunk_idx == 0 else ""

        if len(chunk) == 1:
            msg_id = await _send_single(bot, chat_id, chunk[0], chunk_caption, media_type)
            if msg_id:
                message_ids.append(msg_id)
        else:
            ids = await _send_media_group(bot, chat_id, chunk, chunk_caption, media_type)
            message_ids.extend(ids)

        if chunk_idx < len(chunks) - 1:
            await asyncio.sleep(1)

    return message_ids


async def _send_single(
    bot: Bot,
    chat_id: int,
    filepath: str,
    caption: str,
    media_type: str,
) -> int | None:
    if not os.path.exists(filepath):
        return None

    file = FSInputFile(filepath)
    thumb_path = None

    try:
        if media_type == "audio":
            msg = await bot.send_audio(chat_id=chat_id, audio=file, caption=caption)
        elif media_type == "image":
            msg = await bot.send_photo(chat_id=chat_id, photo=file, caption=caption)
        elif _is_image(filepath):
            msg = await bot.send_photo(chat_id=chat_id, photo=file, caption=caption)
        else:
            width, height, duration = await _get_video_meta(filepath)
            thumb_path = await _make_thumbnail(filepath)
            thumb_file = FSInputFile(thumb_path) if thumb_path else None
            msg = await bot.send_video(
                chat_id=chat_id,
                video=file,
                caption=caption,
                width=width or None,
                height=height or None,
                duration=int(duration) or None,
                thumbnail=thumb_file,
                supports_streaming=True,
            )
        return msg.message_id
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await _send_single(bot, chat_id, filepath, caption, media_type)
    except Exception as e:
        if _is_chat_not_found(e):
            logger.warning("Failed to send %s: %s", filepath, e)
            return None
        logger.error("Failed to send %s: %s", filepath, e)
        try:
            msg = await bot.send_document(chat_id=chat_id, document=file, caption=caption)
            return msg.message_id
        except Exception as e2:
            logger.error("Failed to send as document %s: %s", filepath, e2)
            return None
    finally:
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except OSError:
                pass


async def _send_media_group(
    bot: Bot,
    chat_id: int,
    files: list[str],
    caption: str,
    media_type: str,
) -> list[int]:
    existing_files = [filepath for filepath in files if os.path.exists(filepath)]
    if not existing_files:
        return []

    if len(existing_files) == 1:
        msg_id = await _send_single(bot, chat_id, existing_files[0], caption, media_type)
        return [msg_id] if msg_id else []

    builder = MediaGroupBuilder(caption=caption)

    for filepath in existing_files:
        file = FSInputFile(filepath)
        if media_type == "image" or _is_image(filepath):
            builder.add_photo(media=file)
        else:
            builder.add_video(media=file)

    try:
        messages = await bot.send_media_group(chat_id=chat_id, media=builder.build())
        return [m.message_id for m in messages]
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await _send_media_group(bot, chat_id, files, caption, media_type)
    except Exception as e:
        if _is_chat_not_found(e):
            logger.warning("Failed to send media group: %s", e)
            return []
        logger.error("Failed to send media group: %s", e)
        ids = []
        for f in existing_files:
            msg_id = await _send_single(bot, chat_id, f, "", media_type)
            if msg_id:
                ids.append(msg_id)
        return ids


def _is_image(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


async def _get_video_meta(filepath: str) -> tuple[int, int, float]:
    from app.services.media.ffmpeg import get_video_info

    try:
        return await get_video_info(filepath)
    except Exception as e:
        logger.warning("Failed to get video meta for %s: %s", filepath, e)
        return 0, 0, 0.0


async def _make_thumbnail(filepath: str) -> str | None:
    from app.services.media.ffmpeg import extract_thumbnail

    try:
        output_dir = os.path.dirname(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        _, thumb_path = await extract_thumbnail(
            filepath, output_dir, base_name, seek_sec=2,
        )
        if thumb_path and os.path.exists(thumb_path):
            return thumb_path
    except Exception as e:
        logger.warning("Failed to create thumbnail for %s: %s", filepath, e)
    return None
