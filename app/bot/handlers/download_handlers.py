import asyncio
import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.cache.video_cache import VideoCacheService
from app.services.downloader.download_manager import DownloadManager, url_hash
from app.services.downloader.progress import ProgressTracker
from app.services.nsfw.detector import is_porn
from app.services.uploader.sender import send_files

logger = logging.getLogger(__name__)

download_router = Router()
download_router.message.filter(F.chat.type == "private")

RANGE_PATTERN = re.compile(r"(\d+)\s*-\s*(\d+)")


def _extract_url_and_range(text: str) -> tuple[str, str | None]:
    parts = text.split(maxsplit=2)
    if len(parts) < 2:
        return "", None
    url = parts[1].strip()
    playlist_range = None
    if len(parts) > 2:
        match = RANGE_PATTERN.search(parts[2])
        if match:
            playlist_range = f"{match.group(1)}-{match.group(2)}"
    return url, playlist_range


async def _process_download(
    message: Message,
    bot: Bot,
    db: DB,
    url: str,
    media_type: str = "video",
    playlist_range: str | None = None,
) -> None:
    config = get_config()
    user_id = message.from_user.id

    status_msg = await message.answer("Processing...")
    progress = ProgressTracker(bot, message.chat.id, status_msg.message_id)

    try:
        cache_service = VideoCacheService(db)
        nsfw = is_porn(url)

        if not nsfw and media_type == "video":
            cached = await cache_service.get_cached_msg_ids(url, "best")
            if cached:
                await progress.update("Found in cache, forwarding...")
                channel_id = config.channels.logs_video_channel_id
                for msg_id in cached:
                    try:
                        await bot.forward_message(
                            chat_id=message.chat.id,
                            from_chat_id=channel_id,
                            message_id=msg_id,
                        )
                    except Exception as e:
                        logger.warning("Cache forward failed for msg %d: %s", msg_id, e)
                await progress.stop("Done!")
                await db.downloads.add(
                    user_id=user_id, url=url, url_hash=url_hash(url),
                    title="(cached)", quality="best", media_type=media_type,
                )
                await db.users.increment_downloads(user_id, media_type)
                return

        await progress.start(f"Downloading {media_type}")

        manager = DownloadManager(config)

        if media_type == "audio":
            result = await manager.download_audio(url, user_id=user_id)
        elif media_type == "playlist":
            result = await manager.download_playlist(
                url, indices=playlist_range, user_id=user_id
            )
        else:
            result = await manager.download_video(url, user_id=user_id)

        if not result.success:
            await progress.stop(f"Download failed: {result.error}")
            return

        await progress.update("Uploading...")

        sent_type = "audio" if media_type == "audio" else "video"
        caption = f"<b>{result.title}</b>" if result.title else ""

        msg_ids = await send_files(
            bot=bot,
            chat_id=message.chat.id,
            files=result.files,
            caption=caption,
            media_type=sent_type,
        )

        if msg_ids and not nsfw:
            log_channel = config.channels.logs_video_channel_id
            if log_channel:
                log_msg_ids = []
                for filepath in result.files:
                    try:
                        fwd = await send_files(
                            bot=bot,
                            chat_id=log_channel,
                            files=[filepath],
                            caption=caption,
                            media_type=sent_type,
                        )
                        log_msg_ids.extend(fwd)
                    except Exception as e:
                        logger.warning("Log forward failed: %s", e)
                if log_msg_ids:
                    await cache_service.save(
                        url=url, quality="best",
                        telegram_file_id="", telegram_msg_ids=log_msg_ids,
                        title=result.title,
                    )

        await db.downloads.add(
            user_id=user_id, url=url, url_hash=url_hash(url),
            title=result.title, quality="best", media_type=media_type,
            file_size_bytes=result.file_size, duration_sec=result.duration,
            is_nsfw=nsfw,
        )
        await db.users.increment_downloads(user_id, media_type)

        await progress.stop(f"Done! {len(msg_ids)} file(s) sent.")

        manager.cleanup_files(result.files)

    except Exception as e:
        logger.error("Download process error for %s: %s", url, e, exc_info=True)
        await progress.stop(f"Error: {e}")


@download_router.message(Command("vid"))
async def cmd_vid(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    url, _ = _extract_url_and_range(message.text)
    if not url:
        await message.answer(
            "Usage: /vid <code>URL</code>\n"
            "Or just send a URL directly."
        )
        return

    asyncio.create_task(_process_download(message, bot, db, url, "video"))


@download_router.message(Command("audio"))
async def cmd_audio(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    url, _ = _extract_url_and_range(message.text)
    if not url:
        await message.answer("Usage: /audio <code>URL</code>")
        return

    asyncio.create_task(_process_download(message, bot, db, url, "audio"))


@download_router.message(Command("playlist"))
async def cmd_playlist(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    url, playlist_range = _extract_url_and_range(message.text)
    if not url:
        await message.answer("Usage: /playlist <code>URL</code> [range]")
        return

    asyncio.create_task(
        _process_download(message, bot, db, url, "playlist", playlist_range)
    )


@download_router.message(Command("link"))
async def cmd_link(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /link <code>URL</code>")
        return

    url = parts[1].strip()
    status_msg = await message.answer("Extracting direct link...")

    try:
        from app.services.url_parser.extractor import extract_info

        info = await extract_info(url)
        if not info:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="Could not extract info from this URL.",
            )
            return

        direct_url = info.get("url") or info.get("webpage_url", url)
        title = info.get("title", "Unknown")
        text = (
            f"<b>{title}</b>\n\n"
            f"<code>{direct_url}</code>"
        )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=text,
        )
    except Exception as e:
        logger.error("Link extraction failed for %s: %s", url, e)
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"Failed to extract link: {e}",
        )
