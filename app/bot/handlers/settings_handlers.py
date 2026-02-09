import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode

from app.bot.dialogs.flows.format_selection.states import FormatSG
from app.bot.dialogs.flows.settings.states import SettingsSG
from app.bot.dialogs.flows.subtitle_selection.states import SubtitleSG
from app.bot.keyboards.factories import LangAction, SettingsAction
from app.bot.keyboards.inline import language_keyboard, settings_main_keyboard
from app.infrastructure.database.db import DB

logger = logging.getLogger(__name__)

settings_router = Router()
settings_router.message.filter(F.chat.type == "private")


@settings_router.message(Command("settings"))
async def cmd_settings(message: Message, dialog_manager: DialogManager) -> None:
    if not message.from_user:
        return
    await dialog_manager.start(
        SettingsSG.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": message.from_user.id},
    )
    await message.delete()


@settings_router.message(Command("format"))
async def cmd_format(message: Message, dialog_manager: DialogManager) -> None:
    if not message.from_user:
        return
    await dialog_manager.start(
        FormatSG.main,
        mode=StartMode.RESET_STACK,
    )
    await message.delete()


@settings_router.message(Command("split"))
async def cmd_split(message: Message, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    parts = message.text.split()
    if len(parts) < 2:
        user_result = await db.users.get_user(message.from_user.id)
        current = user_result.data.get("split_size_mb", 0) if user_result else 0
        status = f"{current} MB" if current > 0 else "disabled"
        await message.answer(
            f"Current split: {status}\n\n"
            "Usage: /split <code>size_mb</code>\n"
            "Set to 0 to disable."
        )
        return

    try:
        size = int(parts[1])
    except ValueError:
        await message.answer("Invalid size. Use a number (MB).")
        return

    await db.users.update_preferences(message.from_user.id, split_size_mb=max(0, size))
    status = f"{size} MB" if size > 0 else "disabled"
    await message.answer(f"Split set to: {status}")


@settings_router.message(Command("tags"))
async def cmd_tags(message: Message) -> None:
    # TODO: Integrate with tags service
    await message.answer("Tags management will be available here.")


@settings_router.message(Command("subs"))
async def cmd_subs(message: Message, dialog_manager: DialogManager) -> None:
    if not message.from_user:
        return
    await dialog_manager.start(
        SubtitleSG.main,
        mode=StartMode.RESET_STACK,
        data={"user_id": message.from_user.id},
    )
    await message.delete()


@settings_router.message(Command("args"))
async def cmd_args(message: Message, db: DB) -> None:
    if not message.from_user or not message.text:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        user_result = await db.users.get_user(message.from_user.id)
        custom_args = user_result.data.get("custom_args", {}) if user_result else {}
        await message.answer(
            f"<b>Custom Args</b>\n\n"
            f"Current: <code>{custom_args or 'none'}</code>\n\n"
            f"Usage: /args <code>key=value</code>"
        )
        return

    # TODO: Parse and save custom args
    await message.answer("Args updated.")


@settings_router.message(Command("lang"))
async def cmd_lang(message: Message) -> None:
    await message.answer(
        "Select your language:",
        reply_markup=language_keyboard().as_markup(),
    )


@settings_router.callback_query(LangAction.filter())
async def on_lang_select(callback: CallbackQuery, callback_data: LangAction, db: DB) -> None:
    if not callback.from_user:
        return

    lang_names = {"en": "English", "ru": "Русский", "ar": "العربية", "hi": "हिन्दी"}
    lang = callback_data.code

    await db.users.update_preferences(callback.from_user.id, language_code=lang)
    await callback.message.edit_text(f"Language set to: {lang_names.get(lang, lang)}")
    await callback.answer()


@settings_router.callback_query(SettingsAction.filter(F.menu == "main"))
async def on_settings_action(callback: CallbackQuery, callback_data: SettingsAction, db: DB) -> None:
    action = callback_data.action

    if action == "close":
        await callback.message.delete()
        await callback.answer()
        return

    if action == "language":
        await callback.message.edit_text(
            "Select your language:",
            reply_markup=language_keyboard().as_markup(),
        )
        await callback.answer()
        return

    # TODO: Handle other settings actions
    await callback.answer(f"Settings: {action} (coming soon)")
