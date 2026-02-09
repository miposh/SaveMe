import asyncio
import logging
import re

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, URLInputFile

from app.bot.filters.url_pattern import HasURL
from app.bot.handlers.preview_handlers import store_url
from app.bot.keyboards.inline import youtube_preview_keyboard
from app.bot.keyboards.reply import main_reply_keyboard
from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.cache.video_cache import VideoCacheService
from app.services.downloader.download_manager import DownloadManager, url_hash
from app.services.downloader.progress import ProgressTracker
from app.services.nsfw.detector import is_porn
from app.services.uploader.sender import send_files
from app.services.url_parser.youtube import is_youtube_url
from app.services.url_parser.youtube_info import build_preview_text, fetch_youtube_info

logger = logging.getLogger(__name__)

user_router = Router()
user_router.message.filter(F.chat.type == "private")

URL_REGEX = re.compile(r"https?://\S+")

_background_tasks: set[asyncio.Task] = set()


@user_router.message(CommandStart())
async def cmd_start(message: Message, db: DB) -> None:
    user = message.from_user
    if not user:
        return

    await db.users.sync_telegram_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
        last_name=user.last_name,
        language_code=user.language_code or "en",
        is_premium=bool(user.is_premium),
    )

    text = (
        f"Welcome, <b>{user.first_name}</b>!\n\n"
        "Send me a URL to download video, audio, or images from 1500+ platforms.\n\n"
        "Use /help for more info."
    )
    await message.answer(text, reply_markup=main_reply_keyboard())


@user_router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>Available commands:</b>\n\n"
        "/vid <code>URL</code> - Download video\n"
        "/audio <code>URL</code> - Download audio\n"
        "/img <code>URL</code> - Download images\n"
        "/playlist <code>URL</code> - Download playlist\n"
        "/link <code>URL</code> - Get direct link\n"
        "/format - Set preferred format\n"
        "/subs - Subtitle settings\n"
        "/split - Split settings\n"
        "/tags - Manage tags\n"
        "/settings - All settings\n"
        "/search <code>query</code> - Search\n"
        "/clean - Clean temp files\n\n"
        "Or just send a URL directly!"
    )
    await message.answer(text)


@user_router.message(Command("profile"))
async def cmd_profile(message: Message, db: DB) -> None:
    if not message.from_user:
        return

    result = await db.users.get_user(message.from_user.id)
    if result.is_empty():
        await message.answer("Profile not found. Send /start first.")
        return

    user_data = result.data
    text = (
        f"<b>Profile</b>\n\n"
        f"ID: <code>{user_data['id']}</code>\n"
        f"Username: @{user_data.get('username', 'N/A')}\n"
        f"Language: {user_data.get('language_code', 'en')}\n"
        f"Premium: {'Yes' if user_data.get('is_premium') else 'No'}\n\n"
        f"<b>Downloads:</b>\n"
        f"Videos: {user_data.get('count_downloads', 0)}\n"
        f"Audio: {user_data.get('count_audio', 0)}\n"
        f"Images: {user_data.get('count_images', 0)}\n"
        f"Playlists: {user_data.get('count_playlists', 0)}\n\n"
        f"<b>Settings:</b>\n"
        f"Codec: {user_data.get('preferred_codec', 'avc1')}\n"
        f"Split: {user_data.get('split_size_mb', 0)} MB\n"
        f"Subtitles: {'On' if user_data.get('subs_enabled') else 'Off'}\n"
        f"NSFW: {'On' if user_data.get('nsfw_enabled') else 'Off'}"
    )
    await message.answer(text)


@user_router.message(HasURL())
async def handle_url(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    match = URL_REGEX.search(message.text)
    if not match:
        return

    url = match.group(0)

    if is_youtube_url(url):
        task = asyncio.create_task(_process_youtube_preview(message, bot, url))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return

    task = asyncio.create_task(_process_url_download(message, bot, db, url))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _process_youtube_preview(message: Message, bot: Bot, url: str) -> None:
    status_msg = await message.answer("Loading info...")

    try:
        info = await fetch_youtube_info(url)

        if info.has_error:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"Failed to load info: {info.error}",
            )
            return

        h = url_hash(url)
        store_url(h, url)

        preview_text = build_preview_text(info)
        available_qualities = [str(f.height) for f in info.formats]
        keyboard = youtube_preview_keyboard(h, available_qualities)

        # Delete "Loading..." and send photo with thumbnail + caption + buttons
        await bot.delete_message(
            chat_id=message.chat.id, message_id=status_msg.message_id,
        )

        if info.thumbnail:
            try:
                photo = URLInputFile(info.thumbnail)
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo,
                    caption=preview_text,
                    reply_markup=keyboard.as_markup(),
                )
                return
            except Exception as photo_err:
                logger.warning("Failed to send thumbnail photo: %s", photo_err)

        # Fallback: text-only if thumbnail unavailable
        await bot.send_message(
            chat_id=message.chat.id,
            text=preview_text,
            reply_markup=keyboard.as_markup(),
        )
    except Exception as e:
        logger.error("YouTube preview error for %s: %s", url, e, exc_info=True)
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"Error: {e}",
            )
        except Exception:
            await message.answer(f"Error: {e}")


async def _process_url_download(
    message: Message, bot: Bot, db: DB, url: str,
) -> None:
    config = get_config()
    status_msg = await message.answer("Processing...")
    progress = ProgressTracker(bot, message.chat.id, status_msg.message_id)

    try:
        cache_service = VideoCacheService(db)
        nsfw = is_porn(url)

        if not nsfw:
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
                        logger.warning("Cache forward failed: %s", e)
                await progress.stop("Done!")
                await db.downloads.add(
                    user_id=message.from_user.id, url=url,
                    url_hash=url_hash(url), title="(cached)",
                    quality="best", media_type="video",
                )
                await db.users.increment_downloads(message.from_user.id, "video")
                return

        await progress.start("Downloading")

        manager = DownloadManager(config)
        result = await manager.download_video(url, user_id=message.from_user.id)

        if not result.success:
            await progress.stop(f"Download failed: {result.error}")
            return

        await progress.update("Uploading...")

        caption = f"<b>{result.title}</b>" if result.title else ""
        msg_ids = await send_files(
            bot=bot,
            chat_id=message.chat.id,
            files=result.files,
            caption=caption,
            media_type="video",
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
                            media_type="video",
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
            user_id=message.from_user.id, url=url,
            url_hash=url_hash(url), title=result.title,
            quality="best", media_type="video",
            file_size_bytes=result.file_size, duration_sec=result.duration,
            is_nsfw=nsfw,
        )
        await db.users.increment_downloads(message.from_user.id, "video")

        await progress.stop(f"Done! {len(msg_ids)} file(s) sent.")
        manager.cleanup_files(result.files)

    except Exception as e:
        logger.error("URL download error for %s: %s", url, e, exc_info=True)
        await progress.stop(f"Error: {e}")


@user_router.message()
async def echo_fallback(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer("Send me a URL to download media, or use /help for commands.")
