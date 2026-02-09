import logging
from datetime import datetime

from aiogram import Bot

from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


class BroadcastScheduler:

    def __init__(self, bot: Bot, db: DB) -> None:
        self._bot = bot
        self._db = db
        self._running = False

    async def create_broadcast(
        self,
        admin_id: int,
        text: str,
        media_file_id: str | None = None,
        segment: str = "all",
        scheduled_at: datetime | None = None,
    ) -> int | None:
        try:
            result = await self._db.broadcasts.create(
                admin_id=admin_id,
                text=text,
                media_file_id=media_file_id,
                segment=segment,
                status="scheduled" if scheduled_at else "pending",
                scheduled_at=scheduled_at,
            )
            row = result.as_dict()
            return row.get("id") if row else None
        except Exception as e:
            logger.error("Failed to create broadcast: %s", e)
            return None

    async def execute_broadcast(self, broadcast_id: int) -> dict:
        stats = {"sent": 0, "failed": 0, "blocked": 0}

        try:
            result = await self._db.users.get_active_users(days=30)
            users = result.as_dicts() or []
        except Exception as e:
            logger.error("Failed to get users for broadcast: %s", e)
            return stats

        await self._db.broadcasts.update_status(broadcast_id, "sending")

        for user in users:
            user_id = user.get("id")
            if not user_id:
                continue

            try:
                broadcast_result = await self._db.broadcasts.get_scheduled()
                rows = broadcast_result.as_dicts() or []
                broadcast_data = next(
                    (r for r in rows if r.get("id") == broadcast_id), None,
                )
                if not broadcast_data:
                    break

                text = broadcast_data.get("text", "")
                media_file_id = broadcast_data.get("media_file_id")

                if media_file_id:
                    await self._bot.send_photo(
                        chat_id=user_id,
                        photo=media_file_id,
                        caption=text,
                    )
                else:
                    await self._bot.send_message(
                        chat_id=user_id,
                        text=text,
                    )
                stats["sent"] += 1
            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "deactivated" in error_str:
                    stats["blocked"] += 1
                else:
                    stats["failed"] += 1
                    logger.warning("Broadcast to %d failed: %s", user_id, e)

        await self._db.broadcasts.update_stats(
            broadcast_id,
            total_recipients=stats["sent"] + stats["failed"] + stats["blocked"],
            sent_count=stats["sent"],
            failed_count=stats["failed"],
            blocked_count=stats["blocked"],
        )

        logger.info(
            "Broadcast %d completed: sent=%d, failed=%d, blocked=%d",
            broadcast_id, stats["sent"], stats["failed"], stats["blocked"],
        )
        return stats

    async def get_scheduled(self) -> list[dict]:
        try:
            result = await self._db.broadcasts.get_scheduled()
            return result.as_dicts() or []
        except Exception as e:
            logger.error("Failed to get scheduled broadcasts: %s", e)
            return []
