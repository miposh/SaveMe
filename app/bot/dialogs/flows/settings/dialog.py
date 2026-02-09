from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.flows.settings.getters import (
    get_language_data,
    get_settings_data,
    get_split_data,
)
from app.bot.dialogs.flows.settings.handlers import (
    custom_args_check,
    on_close,
    on_custom_args_error,
    on_custom_args_success,
    on_go_back,
    on_go_to_custom_args,
    on_go_to_language,
    on_go_to_split,
    on_go_to_subs,
    on_go_to_tags,
    on_select_codec,
    on_select_language,
    on_select_split,
    on_toggle_nsfw,
    on_toggle_subs,
    on_toggle_tags,
)
from app.bot.dialogs.flows.settings.states import SettingsSG

settings_dialog = Dialog(
    # Main settings menu
    Window(
        Format(
            "<b>Settings</b>\n\n"
            "Codec: <b>{preferred_codec}</b>\n"
            "Split: <b>{split_size_mb} MB</b>\n"
            "Subtitles: <b>{subs_enabled}</b>\n"
            "NSFW: <b>{nsfw_enabled}</b>\n"
            "Tags: <b>{tags_enabled}</b>\n"
            "Language: <b>{language_code}</b>\n"
            "Custom args: <code>{custom_args}</code>"
        ),
        Column(
            Row(
                Button(Const("AVC1"), id="codec_avc1", on_click=on_select_codec),
                Button(Const("AV01"), id="codec_av01", on_click=on_select_codec),
                Button(Const("VP9"), id="codec_vp9", on_click=on_select_codec),
            ),
            Button(Const("Split size"), id="split", on_click=on_go_to_split),
            Row(
                Button(Const("Subtitles"), id="subs", on_click=on_toggle_subs),
                Button(Const("NSFW"), id="nsfw", on_click=on_toggle_nsfw),
                Button(Const("Tags"), id="tags", on_click=on_toggle_tags),
            ),
            Button(Const("Language"), id="lang", on_click=on_go_to_language),
            Button(Const("Custom args"), id="args", on_click=on_go_to_custom_args),
            Button(Const("Close"), id="close", on_click=on_close),
        ),
        state=SettingsSG.main,
        getter=get_settings_data,
        parse_mode=ParseMode.HTML,
    ),
    # Split size selection
    Window(
        Format("<b>Select Split Size</b>\n\nCurrent: <b>{current_split} MB</b>"),
        Column(
            Button(Const("50 MB (free)"), id="split_50", on_click=on_select_split),
            Button(Const("200 MB"), id="split_200", on_click=on_select_split),
            Button(Const("2 GB (premium)"), id="split_2000", on_click=on_select_split),
            Button(Const("4 GB (premium)"), id="split_4000", on_click=on_select_split),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=SettingsSG.split_settings,
        getter=get_split_data,
        parse_mode=ParseMode.HTML,
    ),
    # Language selection
    Window(
        Const("<b>Select Language</b>"),
        Column(
            Button(Const("English"), id="lang_en", on_click=on_select_language),
            Button(Const("Russian"), id="lang_ru", on_click=on_select_language),
            Button(Const("Arabic"), id="lang_ar", on_click=on_select_language),
            Button(Const("Hindi"), id="lang_hi", on_click=on_select_language),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=SettingsSG.language,
        getter=get_language_data,
        parse_mode=ParseMode.HTML,
    ),
    # Subtitle settings (toggle handled in handler)
    Window(
        Const("<b>Subtitle Settings</b>\n\nTap to toggle subtitles on/off."),
        Column(
            Button(Const("Toggle subtitles"), id="toggle_subs", on_click=on_toggle_subs),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=SettingsSG.subs_settings,
        parse_mode=ParseMode.HTML,
    ),
    # Custom args input
    Window(
        Const("<b>Enter custom yt-dlp arguments:</b>\n\nSend empty to clear."),
        TextInput(
            id="custom_args_input",
            type_factory=custom_args_check,
            on_success=on_custom_args_success,
            on_error=on_custom_args_error,
        ),
        Button(Const("Back"), id="back", on_click=on_go_back),
        state=SettingsSG.custom_args,
        parse_mode=ParseMode.HTML,
    ),
    # Tags settings (toggle handled in handler)
    Window(
        Const("<b>Tags Settings</b>\n\nTap to toggle auto-tagging on/off."),
        Column(
            Button(Const("Toggle tags"), id="toggle_tags", on_click=on_toggle_tags),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=SettingsSG.tags_settings,
        parse_mode=ParseMode.HTML,
    ),
)
