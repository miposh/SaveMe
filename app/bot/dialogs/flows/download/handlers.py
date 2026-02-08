import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from app.config.config import settings
from app.worker.tasks import download_video_task, download_audio_task, download_thumbnail_task

logger = logging.getLogger(__name__)


async def on_quality_selected(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    start_data = dialog_manager.start_data
    video_url = start_data["video_url"]
    title = start_data["title"]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    status_msg = await callback.message.answer(
        f"Скачивание <b>{item_id}p</b>...\nПожалуйста, подождите."
    )

    await dialog_manager.done()

    await download_video_task.kiq(
        bot_token=settings.bot_token,
        chat_id=chat_id,
        status_message_id=status_msg.message_id,
        video_url=video_url,
        format_height=int(item_id),
        title=title,
        user_id=user_id,
    )


async def on_mp3_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    start_data = dialog_manager.start_data
    video_url = start_data["video_url"]
    title = start_data["title"]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    status_msg = await callback.message.answer(
        "Скачивание <b>MP3</b>...\nПожалуйста, подождите."
    )

    await dialog_manager.done()

    await download_audio_task.kiq(
        bot_token=settings.bot_token,
        chat_id=chat_id,
        status_message_id=status_msg.message_id,
        video_url=video_url,
        title=title,
        user_id=user_id,
    )


async def on_thumbnail_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    start_data = dialog_manager.start_data
    video_url = start_data["video_url"]
    title = start_data["title"]
    thumbnail_url = start_data["thumbnail_url"]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    status_msg = await callback.message.answer(
        "Скачивание <b>превью</b>..."
    )

    await dialog_manager.done()

    await download_thumbnail_task.kiq(
        bot_token=settings.bot_token,
        chat_id=chat_id,
        status_message_id=status_msg.message_id,
        thumbnail_url=thumbnail_url,
        title=title,
        user_id=user_id,
        video_url=video_url,
    )
