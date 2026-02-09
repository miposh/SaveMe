import logging
import os
import time

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters.admin import IsAdmin
from app.core.config import get_config
from app.infrastructure.database.db import DB
from app.services.cookie.cookie_manager import CookieManager

logger = logging.getLogger(__name__)

cookie_router = Router()
cookie_router.message.filter(F.chat.type == "private", IsAdmin())


def _get_cookie_manager() -> CookieManager:
    return CookieManager(get_config())


@cookie_router.message(Command("cookie"))
async def cmd_cookie(message: Message) -> None:
    config = get_config()
    yt_urls = config.cookies.youtube_cookie_urls
    services = []
    if config.cookies.instagram_cookie_url:
        services.append("Instagram")
    if config.cookies.tiktok_cookie_url:
        services.append("TikTok")
    if config.cookies.facebook_cookie_url:
        services.append("Facebook")
    if config.cookies.twitter_cookie_url:
        services.append("Twitter")
    if config.cookies.vk_cookie_url:
        services.append("VK")

    text = (
        "<b>Cookie Management</b>\n\n"
        f"YouTube cookie sources: {len(yt_urls)}\n"
        f"YouTube rotation: {config.cookies.youtube_cookie_order}\n"
        f"Other services: {', '.join(services) or 'none'}\n\n"
        "/check_cookie - Validate YouTube cookies\n"
        "/save_as_cookie - Save file as cookie\n"
        "/clean_cookies - Remove expired cookies"
    )
    await message.answer(text)


@cookie_router.message(Command("check_cookie"))
async def cmd_check_cookie(message: Message) -> None:
    if not message.from_user:
        return

    status_msg = await message.answer("Checking YouTube cookies...")
    manager = _get_cookie_manager()

    try:
        cookie_path = await manager.get_or_download_youtube_cookie(message.from_user.id)
        if not cookie_path:
            await status_msg.edit_text("No YouTube cookie sources configured.")
            return

        if os.path.exists(cookie_path):
            size = os.path.getsize(cookie_path)
            age = int((time.time() - os.path.getmtime(cookie_path)) / 60)
            text = (
                "<b>YouTube Cookie Status</b>\n\n"
                f"Path: <code>{os.path.basename(cookie_path)}</code>\n"
                f"Size: {size} bytes\n"
                f"Age: {age} minutes\n"
                f"Status: Active"
            )
        else:
            text = "Failed to download YouTube cookie."

        await status_msg.edit_text(text)
    except Exception as e:
        logger.error("Cookie check failed: %s", e)
        await status_msg.edit_text(f"Cookie check failed: {e}")


@cookie_router.message(Command("save_as_cookie"))
async def cmd_save_as_cookie(message: Message, bot: Bot) -> None:
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.answer("Reply to a cookie .txt file with /save_as_cookie")
        return

    doc = message.reply_to_message.document
    if not doc.file_name or not doc.file_name.endswith(".txt"):
        await message.answer("Only .txt cookie files are supported.")
        return

    manager = _get_cookie_manager()
    await manager.ensure_cookie_dir()

    dest_path = os.path.join(manager._cookie_dir, doc.file_name)

    try:
        file = await bot.get_file(doc.file_id)
        if file.file_path:
            await bot.download_file(file.file_path, dest_path)
            size = os.path.getsize(dest_path)
            await message.answer(
                f"Cookie file saved: <code>{doc.file_name}</code> ({size} bytes)"
            )
        else:
            await message.answer("Could not access the file.")
    except Exception as e:
        logger.error("Failed to save cookie file: %s", e)
        await message.answer(f"Failed to save cookie: {e}")


@cookie_router.message(Command("clean_cookies"))
async def cmd_clean_cookies(message: Message) -> None:
    manager = _get_cookie_manager()
    removed = manager.cleanup_old_cookies(max_age_hours=24)
    await message.answer(f"Removed {removed} expired cookie file(s).")
