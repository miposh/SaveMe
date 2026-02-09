from .admin_handlers import admin_router
from .cookie_handlers import cookie_router
from .preview_handlers import preview_router
from .proxy_handlers import proxy_router
from .settings_handlers import settings_router
from .download_handlers import download_router
from .media_handlers import media_router
from .utility_handlers import utility_router
from .user_handlers import user_router
from .group_handlers import group_router
from app.bot.dialogs.flows.admin import admin_dialog
from app.bot.dialogs.flows.format_selection import format_selection_dialog
from app.bot.dialogs.flows.settings import settings_dialog
from app.bot.dialogs.flows.subtitle_selection import subtitle_selection_dialog

routers = [
    admin_router,
    admin_dialog,
    format_selection_dialog,
    settings_dialog,
    subtitle_selection_dialog,
    cookie_router,
    proxy_router,
    settings_router,
    download_router,
    preview_router,
    media_router,
    utility_router,
    user_router,
    group_router,
]
