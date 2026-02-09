import asyncio
import logging
import re

from aiogram import Bot, F, Router
from aiogram.types import ChatMemberUpdated, Message

from app.bot.filters.allowed_group import AllowedGroup
from app.bot.filters.url_pattern import HasURL
from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.downloader.download_manager import DownloadManager, url_hash
from app.services.downloader.progress import ProgressTracker
from app.services.uploader.sender import send_files

logger = logging.getLogger(__name__)

group_router = Router()
group_router.message.filter(F.chat.type.in_({"group", "supergroup"}))

URL_REGEX = re.compile(r"https?://\S+")


@group_router.my_chat_member()
async def bot_membership_changed(event: ChatMemberUpdated) -> None:
    old_status = event.old_chat_member.status if event.old_chat_member else "left"
    new_status = event.new_chat_member.status

    if new_status in ("member", "administrator") and old_status in ("left", "kicked"):
        logger.info("Bot added to group %s (%s)", event.chat.title, event.chat.id)
        await event.answer(
            "Hello! Send me a URL and I'll download the media for you.\n"
            "Use /help for commands."
        )
    elif new_status in ("left", "kicked"):
        logger.info("Bot removed from group %s (%s)", event.chat.title, event.chat.id)


@group_router.message(AllowedGroup(), HasURL())
async def group_url_handler(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    match = URL_REGEX.search(message.text)
    if not match:
        return

    url = match.group(0)

    async def _process_group_url() -> None:
        config = get_config()
        status_msg = await message.reply("Processing...")
        progress = ProgressTracker(bot, message.chat.id, status_msg.message_id)

        try:
            await progress.start("Downloading")

            manager = DownloadManager(config)
            result = await manager.download_video(url, user_id=message.from_user.id)

            if not result.success:
                await progress.stop(f"Download failed: {result.error}")
                return

            await progress.update("Uploading...")

            caption = f"<b>{result.title}</b>" if result.title else ""
            await send_files(
                bot=bot,
                chat_id=message.chat.id,
                files=result.files,
                caption=caption,
                media_type="video",
            )

            await db.downloads.add(
                user_id=message.from_user.id, url=url,
                url_hash=url_hash(url), title=result.title,
                quality="best", media_type="video",
                file_size_bytes=result.file_size, duration_sec=result.duration,
            )
            await db.users.increment_downloads(message.from_user.id, "video")

            await progress.stop(f"Done! {len(result.files)} file(s) sent.")
            manager.cleanup_files(result.files)

        except Exception as e:
            logger.error("Group download error for %s: %s", url, e, exc_info=True)
            await progress.stop(f"Error: {e}")

    asyncio.create_task(_process_group_url())


@group_router.message(F.text.startswith("/"))
async def group_command_handler(message: Message) -> None:
    await message.answer("Please use commands in private chat with the bot.")
