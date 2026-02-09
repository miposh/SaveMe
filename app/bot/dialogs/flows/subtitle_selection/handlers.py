import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.bot.dialogs.flows.subtitle_selection.states import SubtitleSG
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
    await manager.switch_to(SubtitleSG.main)


async def on_toggle_subs(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    current = manager.dialog_data.get("subs_lang", "OFF")
    if current == "OFF":
        await manager.switch_to(SubtitleSG.language_list)
    else:
        manager.dialog_data["subs_lang"] = "OFF"
        db: DB = manager.middleware_data.get("db")
        user_id = manager.dialog_data.get("user_id", 0)
        if db and user_id:
            try:
                await db.users.update_preferences(user_id, subs_enabled=False)
            except Exception as e:
                logger.error("Failed to update subs: %s", e)


async def on_go_to_language_list(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(SubtitleSG.language_list)


async def on_select_language(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    lang_code = button.widget_id.replace("sub_lang_", "")
    manager.dialog_data["subs_lang"] = lang_code
    await manager.switch_to(SubtitleSG.confirm)


async def on_confirm(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    lang_code = manager.dialog_data.get("subs_lang", "OFF")
    db: DB = manager.middleware_data.get("db")
    user_id = manager.dialog_data.get("user_id", 0)

    if db and user_id:
        try:
            enabled = lang_code != "OFF"
            await db.users.update_preferences(
                user_id, subs_enabled=enabled,
            )
        except Exception as e:
            logger.error("Failed to save subtitle preference: %s", e)

    manager.dialog_data["confirmed"] = True
    await callback.message.delete()
    await manager.done()
