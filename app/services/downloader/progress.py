import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter

logger = logging.getLogger(__name__)

ANIMATION_FRAMES = [".", "..", "...", "....", "...."]


class ProgressTracker:
    def __init__(self, bot: Bot, chat_id: int, message_id: int) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._message_id = message_id
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_text = ""

    async def start(self, prefix: str = "Downloading") -> None:
        self._running = True
        self._task = asyncio.create_task(self._animate(prefix))

    async def stop(self, final_text: str = "Done!") -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self._safe_edit(final_text)

    async def update(self, text: str) -> None:
        await self._safe_edit(text)

    async def _animate(self, prefix: str) -> None:
        frame_idx = 0
        try:
            while self._running:
                frame = ANIMATION_FRAMES[frame_idx % len(ANIMATION_FRAMES)]
                text = f"{prefix}{frame}"
                await self._safe_edit(text)
                frame_idx += 1
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    async def _safe_edit(self, text: str) -> None:
        if text == self._last_text:
            return
        self._last_text = text

        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=text,
            )
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except Exception:
            pass
