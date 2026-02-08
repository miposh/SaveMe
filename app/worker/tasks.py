import asyncio
import json
import logging
import os
import subprocess
import tempfile

import aiohttp
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from app.config.config import settings
from app.services.youtube.downloader import YouTubeService
from app.worker.broker import broker

logger = logging.getLogger(__name__)


def _get_downloads_dir() -> str:
    downloads_dir = settings.get("downloads_dir", "./downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    return downloads_dir


def _create_bot(bot_token: str) -> Bot:
    """Создаёт бот для отправки сообщений."""
    return Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def _cleanup_file(file_path: str) -> None:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        logger.warning("Failed to cleanup file %s: %s", file_path, e)


async def _get_video_metadata(file_path: str) -> dict:
    """Получает метаданные видео через ffprobe.
    
    Returns:
        dict с ключами width, height, duration (или None если не удалось получить)
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-select_streams", "v:0",
            file_path
        ]
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True
        )
        
        if result.returncode != 0:
            logger.warning("ffprobe failed: %s", result.stderr)
            return {}
        
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if not streams:
            return {}
        
        stream = streams[0]
        duration_str = stream.get("duration")
        duration = int(float(duration_str)) if duration_str else None
        
        metadata = {
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": duration,
        }
        logger.debug("Video metadata: %s", metadata)
        return metadata
        
    except Exception as e:
        logger.warning("Failed to get video metadata: %s", e)
        return {}


@broker.task
async def download_video_task(
    bot_token: str,
    chat_id: int,
    status_message_id: int,
    video_url: str,
    format_height: int,
    title: str,
    user_id: int,
) -> None:
    bot = _create_bot(bot_token)
    file_path = None

    try:
        output_dir = _get_downloads_dir()
        file_path = await YouTubeService.download_video(
            video_url, format_height, output_dir
        )

        safe_title = "".join(
            c for c in title[:60] if c.isalnum() or c in " _-"
        ).strip()
        filename = f"{safe_title}_{format_height}p.mp4"

        # Получаем метаданные для корректного отображения в Telegram
        metadata = await _get_video_metadata(file_path)

        await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(file_path, filename=filename),
            caption=f"<b>{title}</b>\nКачество: {format_height}p",
            width=metadata.get("width"),
            height=metadata.get("height"),
            duration=metadata.get("duration"),
            supports_streaming=True,
        )

        await bot.delete_message(chat_id=chat_id, message_id=status_message_id)

    except Exception as e:
        logger.error("Download video failed: %s", e, exc_info=True)
        try:
            await bot.edit_message_text(
                text=f"Ошибка при скачивании: {e}",
                chat_id=chat_id,
                message_id=status_message_id,
            )
        except Exception:
            pass
    finally:
        if file_path:
            await _cleanup_file(file_path)
        await bot.session.close()


@broker.task
async def download_audio_task(
    bot_token: str,
    chat_id: int,
    status_message_id: int,
    video_url: str,
    title: str,
    user_id: int,
) -> None:
    bot = _create_bot(bot_token)
    file_path = None

    try:
        output_dir = _get_downloads_dir()
        file_path = await YouTubeService.download_audio(video_url, output_dir)

        safe_title = "".join(
            c for c in title[:60] if c.isalnum() or c in " _-"
        ).strip()
        filename = f"{safe_title}.mp3"

        await bot.send_audio(
            chat_id=chat_id,
            audio=FSInputFile(file_path, filename=filename),
            title=title[:64],
            caption=f"<b>{title}</b>",
        )

        await bot.delete_message(chat_id=chat_id, message_id=status_message_id)

    except Exception as e:
        logger.error("Download audio failed: %s", e, exc_info=True)
        try:
            await bot.edit_message_text(
                text=f"Ошибка при скачивании аудио: {e}",
                chat_id=chat_id,
                message_id=status_message_id,
            )
        except Exception:
            pass
    finally:
        if file_path:
            await _cleanup_file(file_path)
        await bot.session.close()


@broker.task
async def download_thumbnail_task(
    bot_token: str,
    chat_id: int,
    status_message_id: int,
    thumbnail_url: str,
    title: str,
    user_id: int,
    video_url: str,
) -> None:
    bot = _create_bot(bot_token)
    file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as tmp_file:
            file_path = tmp_file.name

            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail_url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            f"Failed to download thumbnail: HTTP {resp.status}"
                        )
                    data = await resp.read()
                    tmp_file.write(data)

        safe_title = "".join(
            c for c in title[:60] if c.isalnum() or c in " _-"
        ).strip()
        filename = f"{safe_title}_thumbnail.jpg"

        await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(file_path, filename=filename),
            caption=f"<b>{title}</b>\nПревью",
        )

        await bot.delete_message(chat_id=chat_id, message_id=status_message_id)

    except Exception as e:
        logger.error("Download thumbnail failed: %s", e, exc_info=True)
        try:
            await bot.edit_message_text(
                text=f"Ошибка при скачивании превью: {e}",
                chat_id=chat_id,
                message_id=status_message_id,
            )
        except Exception:
            pass
    finally:
        if file_path:
            await _cleanup_file(file_path)
        await bot.session.close()
