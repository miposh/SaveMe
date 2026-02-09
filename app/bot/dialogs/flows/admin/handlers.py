import asyncio
import logging

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

from app.bot.dialogs.flows.admin.states import AdminSG
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


async def on_close_dialog(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await callback.message.delete()
    await manager.done()


async def on_go_to_stats(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.stats)


async def on_go_to_users(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.users)


async def on_go_to_user_info(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.user_info_input)


async def on_go_to_broadcast(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.broadcast_input)


async def on_go_to_manage_admins(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.manage_admins)


async def on_go_to_admin_list(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.admin_list)


async def on_go_to_add_admin(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.add_admin_input)


async def on_go_to_remove_admin(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.remove_admin_input)


async def on_go_back(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(AdminSG.main)


def user_info_check(text: str) -> str:
    stripped = text.strip()
    if stripped:
        return stripped
    raise ValueError("Enter user ID or username")


async def on_user_info_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    db: DB = dialog_manager.middleware_data.get("db")
    if not db:
        await message.answer("Database not available")
        return

    user_input = text.strip().lstrip("@")

    try:
        user_id = int(user_input)
        result = await db.users.get_user(user_id=user_id)
    except ValueError:
        result = await db.users.get_by_username(username=user_input)

    user_data = result.as_dict() if result and not result.is_empty() else None

    if not user_data:
        await message.answer(f"User not found: {user_input}")
        return

    dialog_manager.dialog_data.update({
        "user_id": user_data.get("id", "N/A"),
        "username": user_data.get("username", "N/A"),
        "first_name": user_data.get("first_name", "N/A"),
        "downloads": user_data.get("count_downloads", 0),
        "is_banned": user_data.get("is_banned", False),
        "language": user_data.get("language_code", "en"),
        "created_at": str(user_data.get("created_at", "N/A")),
    })
    await dialog_manager.switch_to(AdminSG.user_info_result)


async def on_user_info_error(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError,
) -> None:
    await message.answer("Invalid input. Enter user ID or @username.")


async def on_broadcast_text_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    dialog_manager.dialog_data["broadcast_text"] = text
    await dialog_manager.switch_to(AdminSG.broadcast_segment)


async def on_broadcast_text_error(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError,
) -> None:
    await message.answer("Enter broadcast text")


def broadcast_text_check(text: str) -> str:
    stripped = text.strip()
    if stripped:
        return stripped
    raise ValueError("Text cannot be empty")


async def on_select_segment_all(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["segment"] = "all"
    await manager.switch_to(AdminSG.broadcast_confirm)


async def on_select_segment_active(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["segment"] = "active"
    await manager.switch_to(AdminSG.broadcast_confirm)


async def on_send_broadcast(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    bot: Bot = manager.middleware_data.get("bot")
    db: DB = manager.middleware_data.get("db")
    if not bot or not db:
        return

    text = manager.dialog_data.get("broadcast_text", "")
    segment = manager.dialog_data.get("segment", "all")

    try:
        if segment == "active":
            result = await db.users.get_active_users(days=30)
        else:
            result = await db.users.get_active_users(days=9999)

        users = result.as_dicts() if result else []
        sent = 0
        failed = 0
        blocked = 0

        for user in users:
            uid = user.get("id")
            if not uid:
                continue
            try:
                await bot.send_message(chat_id=uid, text=text)
                sent += 1
                await asyncio.sleep(0.04)
            except Exception as e:
                if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                    blocked += 1
                else:
                    failed += 1

        manager.dialog_data.update({
            "sent": sent,
            "failed": failed,
            "blocked": blocked,
        })
        await manager.switch_to(
            AdminSG.broadcast_result, show_mode=ShowMode.DELETE_AND_SEND,
        )
    except Exception as e:
        logger.error("Broadcast error: %s", e)
        await callback.answer("Broadcast failed")


async def on_add_admin_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    db: DB = dialog_manager.middleware_data.get("db")
    if not db:
        return

    try:
        admin_id = int(text.strip())
        from_user = message.from_user
        added_by = from_user.id if from_user else 0
        await db.admins.add(admin_id=admin_id, username="", added_by=added_by)
        await message.answer(f"Admin {admin_id} added")
        await dialog_manager.switch_to(AdminSG.manage_admins)
    except ValueError:
        await message.answer("Enter a valid user ID")
    except Exception as e:
        await message.answer(f"Error: {e}")


async def on_remove_admin_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    db: DB = dialog_manager.middleware_data.get("db")
    if not db:
        return

    try:
        admin_id = int(text.strip())
        await db.admins.remove(admin_id=admin_id)
        await message.answer(f"Admin {admin_id} removed")
        await dialog_manager.switch_to(AdminSG.manage_admins)
    except ValueError:
        await message.answer("Enter a valid user ID")
    except Exception as e:
        await message.answer(f"Error: {e}")
