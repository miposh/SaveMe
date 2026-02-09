import asyncio
import logging
import os

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.downloader.download_manager import DownloadManager, url_hash
from app.services.downloader.progress import ProgressTracker
from app.services.media.ffmpeg import get_media_info_dict
from app.services.uploader.sender import send_files

logger = logging.getLogger(__name__)

media_router = Router()
media_router.message.filter(F.chat.type == "private")


@media_router.message(Command("img"))
async def cmd_img(message: Message, bot: Bot, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "Usage: /img <code>URL</code> [count]\n"
            "Example: /img https://instagram.com/user 50"
        )
        return

    url = parts[1].strip()
    max_count = 0
    if len(parts) > 2:
        try:
            max_count = int(parts[2].strip())
        except ValueError:
            pass

    status_msg = await message.answer("Downloading images...")
    progress = ProgressTracker(bot, message.chat.id, status_msg.message_id)

    async def _download_images() -> None:
        try:
            config = get_config()
            await progress.start("Downloading images")

            manager = DownloadManager(config)
            result = await manager.download_images(
                url, count=max_count, user_id=message.from_user.id
            )

            if not result.success:
                await progress.stop(f"Download failed: {result.error}")
                return

            await progress.update(f"Uploading {len(result.files)} images...")

            msg_ids = await send_files(
                bot=bot,
                chat_id=message.chat.id,
                files=result.files,
                caption=f"Images from {url}",
                media_type="image",
            )

            log_channel = config.channels.logs_img_channel_id
            if log_channel and msg_ids:
                try:
                    await send_files(
                        bot=bot,
                        chat_id=log_channel,
                        files=result.files[:10],
                        caption=f"User {message.from_user.id}: {url}",
                        media_type="image",
                    )
                except Exception as e:
                    logger.warning("Image log forward failed: %s", e)

            await db.downloads.add(
                user_id=message.from_user.id, url=url,
                url_hash=url_hash(url),
                title=f"{len(result.files)} images", quality="original",
                media_type="image", file_size_bytes=result.file_size,
            )
            await db.users.increment_downloads(message.from_user.id, "image")

            await progress.stop(f"Done! {len(result.files)} image(s) sent.")
            manager.cleanup_files(result.files)

        except Exception as e:
            logger.error("Image download error for %s: %s", url, e, exc_info=True)
            await progress.stop(f"Error: {e}")

    asyncio.create_task(_download_images())


@media_router.message(Command("mediainfo"))
async def cmd_mediainfo(message: Message, bot: Bot) -> None:
    if not message.reply_to_message:
        await message.answer("Reply to a video/audio message with /mediainfo")
        return

    reply = message.reply_to_message
    media = reply.video or reply.audio or reply.document
    if not media:
        await message.answer("Reply to a video, audio, or document message.")
        return

    status_msg = await message.answer("Analyzing media...")

    try:
        file = await bot.get_file(media.file_id)
        if not file.file_path:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="Could not access file.",
            )
            return

        tmp_path = f"/tmp/mediainfo_{media.file_id}"
        await bot.download_file(file.file_path, tmp_path)

        info = await get_media_info_dict(tmp_path)

        lines = ["<b>Media Info</b>\n"]
        for key, value in info.items():
            lines.append(f"<b>{key}:</b> {value}")

        text = "\n".join(lines)
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=text,
        )

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    except Exception as e:
        logger.error("Mediainfo failed: %s", e)
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"Failed to analyze media: {e}",
        )


@media_router.message(Command("nsfw"))
async def cmd_nsfw(message: Message, db: DB) -> None:
    if not message.from_user:
        return

    user_result = await db.users.get_user(message.from_user.id)
    if user_result.is_empty():
        await message.answer("Send /start first.")
        return

    current = user_result.data.get("nsfw_enabled", False)
    new_value = not current

    await db.users.update_preferences(message.from_user.id, nsfw_enabled=new_value)

    status = "enabled" if new_value else "disabled"
    await message.answer(f"NSFW filter {status}.")
