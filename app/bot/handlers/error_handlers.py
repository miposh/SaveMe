import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

error_router = Router(name="error_router")


@error_router.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    logger.error(
        "Unhandled error in update %s: %s",
        event.update.update_id if event.update else "unknown",
        event.exception,
        exc_info=event.exception,
    )

    if event.update and event.update.message:
        try:
            await event.update.message.answer(
                "Произошла ошибка. Попробуйте ещё раз позже."
            )
        except Exception:
            pass

    return True
