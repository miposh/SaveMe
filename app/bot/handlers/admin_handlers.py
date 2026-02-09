import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.flows.admin.states import AdminSG
from app.bot.filters.admin import IsAdmin
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)

admin_router = Router()
admin_router.message.filter(F.chat.type == "private", IsAdmin())


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(AdminSG.main, mode=StartMode.RESET_STACK)
    await message.delete()


@admin_router.message(Command("block_user"))
async def cmd_block_user(message: Message, db: DB) -> None:
    if not message.text:
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /block_user <code>user_id</code> [reason]")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid user ID")
        return

    reason = " ".join(parts[2:]) if len(parts) > 2 else None
    result = await db.users.ban_user(target_id, reason=reason)

    if result and not result.is_empty():
        await message.answer(f"User {target_id} blocked.")
    else:
        await message.answer(f"User {target_id} not found.")


@admin_router.message(Command("unblock_user"))
async def cmd_unblock_user(message: Message, db: DB) -> None:
    if not message.text:
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /unblock_user <code>user_id</code>")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid user ID")
        return

    result = await db.users.unban_user(target_id)
    if result and not result.is_empty():
        await message.answer(f"User {target_id} unblocked.")
    else:
        await message.answer(f"User {target_id} not found.")


@admin_router.message(Command("all"))
async def cmd_all_stats(message: Message, db: DB) -> None:
    total = await db.users.get_users_count()
    day = await db.users.get_users_by_period("day")
    week = await db.users.get_users_by_period("week")
    month = await db.users.get_users_by_period("month")

    downloads_day = await db.downloads.get_count_by_period("day")
    downloads_week = await db.downloads.get_count_by_period("week")
    downloads_total = await db.downloads.get_total_count()

    text = (
        f"<b>Statistics</b>\n\n"
        f"<b>Users:</b>\n"
        f"Total: {total}\n"
        f"Today: +{day}\n"
        f"Week: +{week}\n"
        f"Month: +{month}\n\n"
        f"<b>Downloads:</b>\n"
        f"Total: {downloads_total}\n"
        f"Today: {downloads_day}\n"
        f"Week: {downloads_week}"
    )
    await message.answer(text)


@admin_router.message(Command("log"))
async def cmd_user_log(message: Message, db: DB) -> None:
    if not message.text:
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Usage: /log <code>user_id</code>")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid user ID")
        return

    user_result = await db.users.get_user(target_id)
    if user_result.is_empty():
        await message.answer(f"User {target_id} not found.")
        return

    downloads = await db.downloads.get_by_user(target_id, limit=10)
    user_data = user_result.data

    text = (
        f"<b>User Info</b>\n\n"
        f"ID: <code>{user_data['id']}</code>\n"
        f"Username: @{user_data.get('username', 'N/A')}\n"
        f"Name: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
        f"Banned: {'Yes' if user_data.get('is_banned') else 'No'}\n"
        f"Downloads: {user_data.get('count_downloads', 0)}\n\n"
    )

    if downloads and not downloads.is_empty():
        text += "<b>Recent downloads:</b>\n"
        for dl in downloads.data[:10]:
            text += f"- {dl.get('domain', '?')}: {dl.get('title', dl.get('url', '?'))[:50]}\n"

    await message.answer(text)


@admin_router.message(Command("run_time"))
async def cmd_run_time(message: Message) -> None:
    import time
    import psutil

    process = psutil.Process()
    uptime = time.time() - process.create_time()
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    memory = process.memory_info().rss / 1024 / 1024

    await message.answer(
        f"<b>System Info</b>\n\n"
        f"Uptime: {hours}h {minutes}m\n"
        f"Memory: {memory:.1f} MB"
    )
