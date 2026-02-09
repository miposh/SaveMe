import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

from app.bot.dialogs.flows.settings.states import SettingsSG
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)


async def on_close(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await callback.message.delete()
    await manager.done()


async def on_go_back(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.main)


async def on_go_to_format(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.format_settings)


async def on_go_to_split(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.split_settings)


async def on_go_to_language(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.language)


async def on_go_to_subs(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.subs_settings)


async def on_go_to_custom_args(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.custom_args)


async def on_go_to_tags(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SettingsSG.tags_settings)


async def on_toggle_subs(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if not db or not user_id:
        return

    current = manager.dialog_data.get("subs_enabled", False)
    new_value = not current
    manager.dialog_data["subs_enabled"] = new_value

    try:
        await db.users.update_preferences(user_id, subs_enabled=new_value)
    except Exception as e:
        logger.error("Failed to update subs setting: %s", e)


async def on_toggle_nsfw(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if not db or not user_id:
        return

    current = manager.dialog_data.get("nsfw_enabled", False)
    new_value = not current
    manager.dialog_data["nsfw_enabled"] = new_value

    try:
        await db.users.update_preferences(user_id, nsfw_enabled=new_value)
    except Exception as e:
        logger.error("Failed to update nsfw setting: %s", e)


async def on_toggle_tags(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if not db or not user_id:
        return

    current = manager.dialog_data.get("tags_enabled", True)
    new_value = not current
    manager.dialog_data["tags_enabled"] = new_value

    try:
        await db.users.update_preferences(user_id, tags_enabled=new_value)
    except Exception as e:
        logger.error("Failed to update tags setting: %s", e)


async def on_select_codec(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    codec = button.widget_id.replace("codec_", "")
    manager.dialog_data["preferred_codec"] = codec

    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if db and user_id:
        try:
            await db.users.update_preferences(user_id, preferred_codec=codec)
        except Exception as e:
            logger.error("Failed to update codec: %s", e)

    await manager.switch_to(SettingsSG.main)


async def on_select_language(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    lang_code = button.widget_id.replace("lang_", "")
    manager.dialog_data["language_code"] = lang_code

    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if db and user_id:
        try:
            await db.users.update_preferences(user_id, language_code=lang_code)
        except Exception as e:
            logger.error("Failed to update language: %s", e)

    await manager.switch_to(SettingsSG.main)


async def on_select_split(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    size_str = button.widget_id.replace("split_", "")
    try:
        size_mb = int(size_str)
    except ValueError:
        return

    manager.dialog_data["split_size_mb"] = size_mb

    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)
    if db and user_id:
        try:
            await db.users.update_preferences(user_id, split_size_mb=size_mb)
        except Exception as e:
            logger.error("Failed to update split size: %s", e)

    await manager.switch_to(SettingsSG.main)


def custom_args_check(text: str) -> str:
    return text.strip()


async def on_custom_args_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    db: DB = dialog_manager.middleware_data.get("db")
    user_id = dialog_manager.dialog_data.get("user_id", 0)
    dialog_manager.dialog_data["custom_args"] = text

    if db and user_id:
        try:
            await db.users.update_preferences(user_id, custom_args=text)
        except Exception as e:
            logger.error("Failed to update custom args: %s", e)

    await dialog_manager.switch_to(SettingsSG.main)


async def on_custom_args_error(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError,
) -> None:
    await message.answer("Invalid input")
