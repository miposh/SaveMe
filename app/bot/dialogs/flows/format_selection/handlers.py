import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.bot.dialogs.flows.format_selection.states import FormatSG

logger = logging.getLogger(__name__)


async def on_close(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await callback.message.delete()
    await manager.done()


async def on_select_best(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["quality"] = "best"
    await manager.switch_to(FormatSG.confirm)


async def on_select_4k(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["quality"] = "2160"
    await manager.switch_to(FormatSG.confirm)


async def on_select_fhd(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["quality"] = "1080"
    await manager.switch_to(FormatSG.confirm)


async def on_go_to_quality_grid(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(FormatSG.quality_grid)


async def on_go_to_codec(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(FormatSG.codec_select)


async def on_go_back_to_main(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.switch_to(FormatSG.main)


async def on_select_quality(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    quality_value = button.widget_id.replace("q_", "")
    manager.dialog_data["quality"] = quality_value
    await manager.switch_to(FormatSG.confirm)


async def on_select_codec(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    codec_value = button.widget_id.replace("codec_", "")
    manager.dialog_data["codec"] = codec_value
    await manager.switch_to(FormatSG.main)


async def on_confirm_download(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    from app.bot.dialogs.flows.format_selection.getters import build_format_string

    data = manager.dialog_data
    quality = data.get("quality", "best")
    codec = data.get("codec", "avc1")
    format_str = build_format_string(quality, codec)

    manager.dialog_data["format_str"] = format_str
    manager.dialog_data["confirmed"] = True

    await callback.message.delete()
    await manager.done()
