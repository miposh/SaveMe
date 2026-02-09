import asyncio
import logging
import time
from collections import OrderedDict

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards.factories import PreviewAction
from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.cache.video_cache import VideoCacheService
from app.services.downloader.download_manager import DownloadManager, url_hash
from app.services.downloader.progress import ProgressTracker
from app.services.uploader.sender import send_files

logger = logging.getLogger(__name__)

preview_router = Router()

# In-memory URL store: url_hash -> (url, timestamp)
# Entries expire after 1 hour; max 10000 entries
_URL_STORE: OrderedDict[str, tuple[str, float]] = OrderedDict()
_STORE_MAX_SIZE = 10_000
_STORE_TTL = 3600


def store_url(h: str, url: str) -> None:
    now = time.monotonic()
    _URL_STORE[h] = (url, now)
    _URL_STORE.move_to_end(h)
    _evict_expired()


def get_url(h: str) -> str | None:
    entry = _URL_STORE.get(h)
    if entry is None:
        return None
    url, ts = entry
    if time.monotonic() - ts > _STORE_TTL:
        _URL_STORE.pop(h, None)
        return None
    return url


def _evict_expired() -> None:
    now = time.monotonic()
    while _URL_STORE:
        key, (_, ts) = next(iter(_URL_STORE.items()))
        if now - ts > _STORE_TTL or len(_URL_STORE) > _STORE_MAX_SIZE:
            _URL_STORE.pop(key)
        else:
            break


async def _download_and_send(
    callback: CallbackQuery,
    bot: Bot,
    db: DB,
    url: str,
    media_type: str,
    quality: str = "best",
) -> None:
    config = get_config()
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    status_msg = await bot.send_message(chat_id, "Processing...")
    progress = ProgressTracker(bot, chat_id, status_msg.message_id)

    try:
        cache_service = VideoCacheService(db)

        if media_type == "video":
            cached = await cache_service.get_cached_msg_ids(url, quality)
            if cached:
                await progress.update("Found in cache, forwarding...")
                channel_id = config.channels.logs_video_channel_id
                for msg_id in cached:
                    try:
                        await bot.forward_message(
                            chat_id=chat_id,
                            from_chat_id=channel_id,
                            message_id=msg_id,
                        )
                    except Exception as e:
                        logger.warning("Cache forward failed: %s", e)
                await progress.stop("Done!")
                await db.downloads.add(
                    user_id=user_id, url=url, url_hash=url_hash(url),
                    title="(cached)", quality=quality, media_type=media_type,
                )
                await db.users.increment_downloads(user_id, media_type)
                return

        await progress.start(f"Downloading {media_type}")
        manager = DownloadManager(config)

        if media_type == "audio":
            result = await manager.download_audio(url, user_id=user_id)
        else:
            result = await manager.download_video(url, quality=quality, user_id=user_id)

        if not result.success:
            await progress.stop(f"Download failed: {result.error}")
            return

        await progress.update("Uploading...")

        sent_type = "audio" if media_type == "audio" else "video"
        caption = f"<b>{result.title}</b>" if result.title else ""

        msg_ids = await send_files(
            bot=bot, chat_id=chat_id, files=result.files,
            caption=caption, media_type=sent_type,
        )

        if msg_ids:
            log_channel = config.channels.logs_video_channel_id
            if log_channel:
                log_msg_ids = []
                for filepath in result.files:
                    try:
                        fwd = await send_files(
                            bot=bot, chat_id=log_channel, files=[filepath],
                            caption=caption, media_type=sent_type,
                        )
                        log_msg_ids.extend(fwd)
                    except Exception as e:
                        logger.warning("Log forward failed: %s", e)
                if log_msg_ids:
                    await cache_service.save(
                        url=url, quality=quality,
                        telegram_file_id="", telegram_msg_ids=log_msg_ids,
                        title=result.title,
                    )

        await db.downloads.add(
            user_id=user_id, url=url, url_hash=url_hash(url),
            title=result.title, quality=quality, media_type=media_type,
            file_size_bytes=result.file_size, duration_sec=result.duration,
        )
        await db.users.increment_downloads(user_id, media_type)
        await progress.stop(f"Done! {len(msg_ids)} file(s) sent.")
        manager.cleanup_files(result.files)

    except Exception as e:
        logger.error("Preview download error for %s: %s", url, e, exc_info=True)
        await progress.stop(f"Error: {e}")


@preview_router.callback_query(PreviewAction.filter(F.action == "dl"))
async def on_quality_download(
    callback: CallbackQuery, callback_data: PreviewAction, bot: Bot, db: DB,
) -> None:
    url = get_url(callback_data.url_hash)
    if not url:
        await callback.answer("Link expired. Send the URL again.", show_alert=True)
        return

    quality = callback_data.quality or "best"
    await callback.answer(f"Downloading {quality}p...")
    asyncio.create_task(_download_and_send(callback, bot, db, url, "video", quality))


@preview_router.callback_query(PreviewAction.filter(F.action == "audio"))
async def on_audio_download(
    callback: CallbackQuery, callback_data: PreviewAction, bot: Bot, db: DB,
) -> None:
    url = get_url(callback_data.url_hash)
    if not url:
        await callback.answer("Link expired. Send the URL again.", show_alert=True)
        return

    await callback.answer("Extracting audio...")
    asyncio.create_task(_download_and_send(callback, bot, db, url, "audio"))


@preview_router.callback_query(PreviewAction.filter(F.action == "codec"))
async def on_codec_select(
    callback: CallbackQuery, callback_data: PreviewAction,
) -> None:
    url = get_url(callback_data.url_hash)
    if not url:
        await callback.answer("Link expired. Send the URL again.", show_alert=True)
        return

    text = (
        "<b>Codec selection</b>\n\n"
        "Use the /format command to set your preferred codec before downloading.\n\n"
        "Available codecs:\n"
        "• AVC1 (H.264) — best compatibility\n"
        "• AV01 (AV1) — best compression\n"
        "• VP9 — good balance"
    )
    await callback.answer()
    await callback.message.answer(text)


@preview_router.callback_query(PreviewAction.filter(F.action == "link"))
async def on_direct_link(
    callback: CallbackQuery, callback_data: PreviewAction, bot: Bot,
) -> None:
    url = get_url(callback_data.url_hash)
    if not url:
        await callback.answer("Link expired. Send the URL again.", show_alert=True)
        return

    await callback.answer("Extracting direct link...")

    try:
        from app.services.url_parser.extractor import extract_info

        info = await extract_info(url)
        if not info:
            await callback.message.answer("Could not extract direct link.")
            return

        direct_url = info.get("url") or info.get("webpage_url", url)
        title = info.get("title", "Unknown")
        text = f"<b>{title}</b>\n\n<code>{direct_url}</code>"
        await callback.message.answer(text)
    except Exception as e:
        logger.error("Direct link extraction failed: %s", e)
        await callback.message.answer(f"Failed: {e}")


@preview_router.callback_query(PreviewAction.filter(F.action == "formats"))
async def on_show_formats(
    callback: CallbackQuery, callback_data: PreviewAction,
) -> None:
    url = get_url(callback_data.url_hash)
    if not url:
        await callback.answer("Link expired. Send the URL again.", show_alert=True)
        return

    await callback.answer("Loading formats...")

    try:
        from app.services.url_parser.extractor import extract_info

        info = await extract_info(url)
        if not info:
            await callback.message.answer("Could not extract formats.")
            return

        raw_formats = info.get("formats") or []
        lines = ["<b>Available formats:</b>\n"]

        for f in raw_formats:
            fmt_id = f.get("format_id", "?")
            ext = f.get("ext", "?")
            resolution = f.get("resolution", "?")
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            filesize = f.get("filesize") or f.get("filesize_approx") or 0
            size_str = f"{filesize / (1024 * 1024):.1f}MB" if filesize else "?"

            has_video = vcodec != "none"
            has_audio = acodec != "none"
            media_flag = "V+A" if has_video and has_audio else ("V" if has_video else "A")

            lines.append(
                f"<code>{fmt_id:>5}</code> | {ext:>4} | {resolution:>10} | "
                f"{media_flag:>3} | {size_str:>8}"
            )

        text = "\n".join(lines[:50])
        if len(lines) > 50:
            text += f"\n\n... and {len(lines) - 50} more formats"

        await callback.message.answer(text)
    except Exception as e:
        logger.error("Format listing failed: %s", e)
        await callback.message.answer(f"Failed: {e}")
