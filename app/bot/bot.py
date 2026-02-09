import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs

from app.core.config import get_config
from app.core.logging import setup_logging
from app.infrastructure.database import get_pg_pool, PsycopgConnection, DatabaseSchema

logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Help"),
        BotCommand(command="vid", description="Download video"),
        BotCommand(command="audio", description="Download audio"),
        BotCommand(command="img", description="Download images"),
        BotCommand(command="playlist", description="Download playlist"),
        BotCommand(command="format", description="Select format"),
        BotCommand(command="settings", description="Settings"),
        BotCommand(command="link", description="Get direct link"),
        BotCommand(command="subs", description="Download subtitles"),
        BotCommand(command="split", description="Split settings"),
        BotCommand(command="tags", description="Tags"),
        BotCommand(command="search", description="Search"),
        BotCommand(command="clean", description="Clean temp files"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands set successfully")


async def on_startup(bot: Bot, db_pool) -> None:
    logger.info("Bot starting...")
    logger.info("Initializing database schema...")

    async with db_pool.connection() as raw_connection:
        connection = PsycopgConnection(raw_connection)
        schema = DatabaseSchema(connection)
        await schema.create_tables()

    logger.info("Database initialized")
    await set_bot_commands(bot)


async def on_shutdown(bot: Bot, db_pool=None) -> None:
    logger.info("Bot shutting down...")

    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


async def start_polling(dp: Dispatcher, bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    allowed_updates = dp.resolve_used_update_types()
    logger.info("Starting polling with allowed_updates: %s", allowed_updates)
    await dp.start_polling(bot, allowed_updates=allowed_updates)


async def main() -> None:
    config = get_config()

    setup_logging(config.log_level)
    logger.info("Logging configured: level=%s", config.log_level)

    session = None
    local_api = config.bot.local_api
    if local_api.enabled:
        api_server = TelegramAPIServer.from_base(
            local_api.base_url,
            is_local=True,
        )
        session = AiohttpSession(api=api_server, timeout=1800)
        logger.info(
            "Using Local Bot API: %s", local_api.base_url,
        )

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    db_pool = await get_pg_pool(
        db_name=config.postgres.db,
        host=config.postgres.host,
        port=config.postgres.port,
        user=config.postgres.user,
        password=config.postgres.password,
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    from app.bot.middlewares.error_handler import ErrorHandlerMiddleware
    from app.bot.middlewares.database import DataBaseMiddleware
    from app.bot.middlewares.chat_type import ChatTypeMiddleware
    from app.bot.middlewares.user_registration import UserRegistrationMiddleware
    from app.bot.middlewares.block_check import BlockCheckMiddleware
    from app.bot.middlewares.rate_limiter import RateLimiterMiddleware
    from app.bot.middlewares.command_limiter import CommandLimiterMiddleware

    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DataBaseMiddleware())
    dp.message.middleware(UserRegistrationMiddleware())
    dp.message.middleware(BlockCheckMiddleware())
    dp.message.middleware(ChatTypeMiddleware())
    dp.message.middleware(RateLimiterMiddleware(config.limits))
    dp.message.middleware(CommandLimiterMiddleware(config.limits))

    from app.bot.handlers import routers
    dp.include_routers(*routers)

    setup_dialogs(dp)

    try:
        dp["db_pool"] = db_pool
        dp["config"] = config
        await on_startup(bot, db_pool)
        await start_polling(dp, bot)
    finally:
        await on_shutdown(bot, db_pool)
        await bot.session.close()
