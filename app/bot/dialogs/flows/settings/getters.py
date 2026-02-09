from aiogram_dialog import DialogManager

from app.infrastructure.database.db import DB


async def get_settings_data(dialog_manager: DialogManager, **kwargs) -> dict:
    db: DB = dialog_manager.middleware_data.get("db")
    user_id = dialog_manager.dialog_data.get("user_id", 0)

    defaults = {
        "preferred_codec": "avc1",
        "split_size_mb": 2000,
        "subs_enabled": False,
        "nsfw_enabled": False,
        "language_code": "en",
        "custom_args": "",
        "tags_enabled": True,
    }

    if not db or not user_id:
        return defaults

    try:
        result = await db.users.get_user(user_id=user_id)
        user = result.as_dict()
        if not user:
            return defaults

        return {
            "preferred_codec": user.get("preferred_codec", "avc1"),
            "split_size_mb": user.get("split_size_mb", 2000),
            "subs_enabled": user.get("subs_enabled", False),
            "nsfw_enabled": user.get("nsfw_enabled", False),
            "language_code": user.get("language_code", "en"),
            "custom_args": str(user.get("custom_args", "") or ""),
            "tags_enabled": user.get("tags_enabled", True),
        }
    except Exception:
        return defaults


LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "ru", "name": "Russian"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
]

SPLIT_OPTIONS = [
    {"label": "50 MB (free)", "value": 50},
    {"label": "200 MB", "value": 200},
    {"label": "2 GB (premium)", "value": 2000},
    {"label": "4 GB (premium)", "value": 4000},
]


async def get_language_data(dialog_manager: DialogManager, **kwargs) -> dict:
    current = dialog_manager.dialog_data.get("language_code", "en")
    languages = []
    for lang in LANGUAGES:
        is_active = lang["code"] == current
        languages.append({
            **lang,
            "active": is_active,
            "display": f">> {lang['name']}" if is_active else lang["name"],
        })
    return {"languages": languages, "current_language": current}


async def get_split_data(dialog_manager: DialogManager, **kwargs) -> dict:
    current = dialog_manager.dialog_data.get("split_size_mb", 2000)
    return {"current_split": current}
