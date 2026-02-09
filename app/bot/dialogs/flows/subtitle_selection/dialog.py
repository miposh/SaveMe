from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.flows.subtitle_selection.getters import (
    get_confirm_data,
    get_language_list_data,
    get_subtitle_main_data,
)
from app.bot.dialogs.flows.subtitle_selection.handlers import (
    on_close,
    on_confirm,
    on_go_back,
    on_go_to_language_list,
    on_select_language,
    on_toggle_subs,
)
from app.bot.dialogs.flows.subtitle_selection.states import SubtitleSG

subtitle_selection_dialog = Dialog(
    # Main: current status + toggle
    Window(
        Format(
            "<b>Subtitle Settings</b>\n\n"
            "Current: <b>{current_lang}</b>"
        ),
        Column(
            Button(Const("Toggle ON/OFF"), id="toggle", on_click=on_toggle_subs),
            Button(Const("Select language"), id="lang_list", on_click=on_go_to_language_list),
            Button(Const("Close"), id="close", on_click=on_close),
        ),
        state=SubtitleSG.main,
        getter=get_subtitle_main_data,
        parse_mode=ParseMode.HTML,
    ),
    # Language list
    Window(
        Const("<b>Select Subtitle Language</b>"),
        Column(
            Row(
                Button(Const("English"), id="sub_lang_en", on_click=on_select_language),
                Button(Const("Russian"), id="sub_lang_ru", on_click=on_select_language),
            ),
            Row(
                Button(Const("Arabic"), id="sub_lang_ar", on_click=on_select_language),
                Button(Const("Hindi"), id="sub_lang_hi", on_click=on_select_language),
            ),
            Row(
                Button(Const("Spanish"), id="sub_lang_es", on_click=on_select_language),
                Button(Const("French"), id="sub_lang_fr", on_click=on_select_language),
            ),
            Row(
                Button(Const("German"), id="sub_lang_de", on_click=on_select_language),
                Button(Const("Portuguese"), id="sub_lang_pt", on_click=on_select_language),
            ),
            Row(
                Button(Const("Japanese"), id="sub_lang_ja", on_click=on_select_language),
                Button(Const("Korean"), id="sub_lang_ko", on_click=on_select_language),
            ),
            Row(
                Button(Const("Chinese"), id="sub_lang_zh", on_click=on_select_language),
                Button(Const("Turkish"), id="sub_lang_tr", on_click=on_select_language),
            ),
            Row(
                Button(Const("Italian"), id="sub_lang_it", on_click=on_select_language),
                Button(Const("Indonesian"), id="sub_lang_id", on_click=on_select_language),
            ),
            Row(
                Button(Const("Vietnamese"), id="sub_lang_vi", on_click=on_select_language),
                Button(Const("Thai"), id="sub_lang_th", on_click=on_select_language),
            ),
        ),
        Button(Const("Back"), id="back", on_click=on_go_back),
        state=SubtitleSG.language_list,
        getter=get_language_list_data,
        parse_mode=ParseMode.HTML,
    ),
    # Confirmation
    Window(
        Format(
            "<b>Confirm Subtitle Language</b>\n\n"
            "Language: <b>{lang_name}</b> ({lang_code})"
        ),
        Row(
            Button(Const("Back"), id="back", on_click=on_go_back),
            Button(Const("Confirm"), id="confirm", on_click=on_confirm),
        ),
        state=SubtitleSG.confirm,
        getter=get_confirm_data,
        parse_mode=ParseMode.HTML,
    ),
)
