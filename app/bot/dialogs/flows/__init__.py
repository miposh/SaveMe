from app.bot.dialogs.flows.admin import admin_dialog
from app.bot.dialogs.flows.format_selection import format_selection_dialog
from app.bot.dialogs.flows.settings import settings_dialog
from app.bot.dialogs.flows.subtitle_selection import subtitle_selection_dialog

dialogs = [
    admin_dialog,
    format_selection_dialog,
    settings_dialog,
    subtitle_selection_dialog,
]

__all__ = ["dialogs"]
