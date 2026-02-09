import logging
import os
import shutil

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_config

logger = logging.getLogger(__name__)

utility_router = Router()
utility_router.message.filter(F.chat.type == "private")


@utility_router.message(Command("clean"))
async def cmd_clean(message: Message) -> None:
    config = get_config()
    save_dir = config.save_dir

    if not os.path.exists(save_dir):
        await message.answer("Download directory is clean.")
        return

    try:
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(save_dir):
            for f in files:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                file_count += 1

        if file_count == 0:
            await message.answer("Download directory is clean.")
            return

        shutil.rmtree(save_dir, ignore_errors=True)
        os.makedirs(save_dir, exist_ok=True)

        size_mb = total_size / (1024 * 1024)
        await message.answer(f"Cleaned {file_count} files ({size_mb:.1f} MB).")
    except Exception as e:
        logger.error("Failed to clean downloads: %s", e)
        await message.answer("Failed to clean downloads.")


@utility_router.message(Command("search"))
async def cmd_search(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /search <code>query</code>")
        return

    query = parts[1].strip()
    # TODO: Integrate with search service
    await message.answer(f"Searching: {query}")


@utility_router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    # TODO: Integrate with list service
    await message.answer("List management will be available here.")


@utility_router.message(Command("keyboard"))
async def cmd_keyboard(message: Message) -> None:
    from app.bot.keyboards.reply import main_reply_keyboard
    await message.answer("Keyboard toggled.", reply_markup=main_reply_keyboard())
