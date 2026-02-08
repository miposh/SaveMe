import logging

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.flows.download.states import DownloadSG
from app.bot.filters.url_filter import YouTubeURLFilter
from app.infrastructure.database.db import DB
from app.services.youtube.downloader import YouTubeService

logger = logging.getLogger(__name__)

user_router = Router(name="user_router")


@user_router.message(CommandStart())
async def command_start_handler(
    message: Message,
    **kwargs: dict,
) -> None:
    await message.answer(
        "<b>Save Me Bot</b>\n\n"
        "Отправьте ссылку на YouTube видео, "
        "и я помогу его скачать в нужном качестве.\n\n"
        "Поддерживаемые ссылки:\n"
        "- youtube.com/watch?v=...\n"
        "- youtu.be/...\n"
        "- youtube.com/shorts/..."
    )


@user_router.message(YouTubeURLFilter())
async def youtube_url_handler(
    message: Message,
    dialog_manager: DialogManager,
    bot: Bot,
    youtube_url: str,
    **kwargs: dict,
) -> None:
    status_msg = await message.answer("Получаю информацию о видео...")

    try:
        video_info = await YouTubeService.get_video_info(youtube_url)
    except Exception as e:
        logger.error("Failed to fetch video info for %s: %s", youtube_url, e)
        await status_msg.edit_text(
            "Не удалось получить информацию о видео.\n"
            "Проверьте ссылку и попробуйте ещё раз."
        )
        return

    await status_msg.delete()

    await dialog_manager.start(
        DownloadSG.preview,
        mode=StartMode.RESET_STACK,
        data={
            "video_url": youtube_url,
            "video_id": video_info["video_id"],
            "title": video_info["title"],
            "channel": video_info["channel"],
            "thumbnail_url": video_info["thumbnail_url"],
            "duration": video_info["duration"],
            "formats": video_info["formats"],
        },
    )
