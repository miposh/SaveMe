from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.flows.format_selection.getters import (
    get_codec_data,
    get_confirm_data,
    get_main_data,
)
from app.bot.dialogs.flows.format_selection.handlers import (
    on_close,
    on_confirm_download,
    on_go_back_to_main,
    on_go_to_codec,
    on_go_to_quality_grid,
    on_select_4k,
    on_select_best,
    on_select_codec,
    on_select_fhd,
    on_select_quality,
)
from app.bot.dialogs.flows.format_selection.states import FormatSG

format_selection_dialog = Dialog(
    # Main menu: presets + navigation
    Window(
        Format(
            "<b>Select Format</b>\n\n"
            "Codec: <b>{current_codec}</b>\n"
            "Quality: <b>{current_quality}</b>"
        ),
        Column(
            Button(Const("Best Video"), id="best", on_click=on_select_best),
            Button(Const("4K PC (2160p)"), id="4k", on_click=on_select_4k),
            Button(Const("Full HD Mobile (1080p)"), id="fhd", on_click=on_select_fhd),
        ),
        Row(
            Button(Const("All qualities"), id="grid", on_click=on_go_to_quality_grid),
            Button(Const("Codec"), id="codec", on_click=on_go_to_codec),
        ),
        Button(Const("Close"), id="close", on_click=on_close),
        state=FormatSG.main,
        getter=get_main_data,
        parse_mode=ParseMode.HTML,
    ),
    # Quality grid
    Window(
        Const("<b>Select Quality</b>"),
        Row(
            Button(Const("144p"), id="q_144", on_click=on_select_quality),
            Button(Const("240p"), id="q_240", on_click=on_select_quality),
            Button(Const("360p"), id="q_360", on_click=on_select_quality),
        ),
        Row(
            Button(Const("480p"), id="q_480", on_click=on_select_quality),
            Button(Const("720p"), id="q_720", on_click=on_select_quality),
            Button(Const("1080p"), id="q_1080", on_click=on_select_quality),
        ),
        Row(
            Button(Const("1440p"), id="q_1440", on_click=on_select_quality),
            Button(Const("2160p"), id="q_2160", on_click=on_select_quality),
            Button(Const("4320p"), id="q_4320", on_click=on_select_quality),
        ),
        Button(Const("Back"), id="back", on_click=on_go_back_to_main),
        state=FormatSG.quality_grid,
        parse_mode=ParseMode.HTML,
    ),
    # Codec selection
    Window(
        Const("<b>Select Codec</b>"),
        Column(
            Button(Const("AVC1 (H.264)"), id="codec_avc1", on_click=on_select_codec),
            Button(Const("AV01 (AV1)"), id="codec_av01", on_click=on_select_codec),
            Button(Const("VP9"), id="codec_vp9", on_click=on_select_codec),
        ),
        Button(Const("Back"), id="back", on_click=on_go_back_to_main),
        state=FormatSG.codec_select,
        getter=get_codec_data,
        parse_mode=ParseMode.HTML,
    ),
    # Confirmation
    Window(
        Format(
            "<b>Confirm Download</b>\n\n"
            "Quality: <b>{quality_label}</b>\n"
            "Codec: <b>{codec}</b>\n"
            "Format: <code>{format_str}</code>"
        ),
        Row(
            Button(Const("Back"), id="back", on_click=on_go_back_to_main),
            Button(Const("Download"), id="confirm", on_click=on_confirm_download),
        ),
        state=FormatSG.confirm,
        getter=get_confirm_data,
        parse_mode=ParseMode.HTML,
    ),
)
