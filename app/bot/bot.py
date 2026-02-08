import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs

from app.bot.dialogs.flows.download import download_dialog
from app.bot.handlers.error_handlers import error_router
from app.bot.handlers.user_handlers import user_router
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.get_user import GetUserMiddleware
from app.bot.middlewares.update_context import UpdateContextMiddleware
from app.config.config import settings
from app.infrastructure.cache.redis_cache import close_redis
from app.infrastructure.database.connection.connect_to_pg import get_pg_pool
from app.infrastructure.database.schema import DatabaseSchema
from app.logger.logging import setup_logging

logger = logging.getLogger(__name__)

session = AiohttpSession(
    api=TelegramAPIServer.from_base("http://localhost:8081", is_local=True)
)


def _build_redis_url() -> str:
    host = settings.redis_host
    port = settings.redis_port
    db = settings.get("redis_database", 1)
    password = settings.get("redis_password", "")
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


async def main() -> None:
    setup_logging(log_level=settings.get("log_level", "DEBUG"))
    logger.info("Starting Save Me Bot...")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    db_pool = await get_pg_pool(
        db_name=settings.postgres_name,
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        min_size=settings.get("postgres_min_pool", 1),
        max_size=settings.get("postgres_max_pool", 5),
    )

    async with db_pool.connection() as conn:
        schema = DatabaseSchema(connection=conn)
        await schema.create_tables()
        await schema.verify_tables()

    redis_url = _build_redis_url()
    storage = RedisStorage.from_url(
        redis_url,
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )

    dp = Dispatcher(storage=storage)

    dp.update.middleware(UpdateContextMiddleware())
    dp.update.middleware(DatabaseMiddleware(pool=db_pool))
    dp.update.middleware(GetUserMiddleware())

    dp.include_router(error_router)
    dp.include_router(user_router)
    dp.include_router(download_dialog)

    setup_dialogs(dp)

    logger.info("Bot is ready, starting polling...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            session=session,
        )
    finally:
        logger.info("Shutting down...")
        await close_redis()
        await storage.close()
        await db_pool.close()
        await bot.session.close()
        logger.info("Bot stopped")
