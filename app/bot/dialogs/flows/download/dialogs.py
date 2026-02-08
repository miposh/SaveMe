import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, Select
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.flows.download.getters import video_info_getter
from app.bot.dialogs.flows.download.handlers import (
    on_mp3_selected,
    on_quality_selected,
    on_thumbnail_selected,
)
from app.bot.dialogs.flows.download.states import DownloadSG

download_dialog = Dialog(
    Window(
        DynamicMedia("thumbnail"),
        Format("{info_text}"),
        Const("\n<b>Форматы для скачивания ↓</b>"),
        Group(
            Select(
                Format("📹 {item[0]}"),
                id="quality_select",
                item_id_getter=operator.itemgetter(1),
                items="formats",
                on_click=on_quality_selected,
            ),
            width=3,
        ),
        Row(
            Button(
                Const("🎵 MP3"),
                id="mp3_btn",
                on_click=on_mp3_selected,
            ),
            Button(
                Const("🖼️ Превью"),
                id="thumbnail_btn",
                on_click=on_thumbnail_selected,
            ),
        ),
        state=DownloadSG.preview,
        getter=video_info_getter,
    ),
)
