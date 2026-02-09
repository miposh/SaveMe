from aiogram_dialog import DialogManager


COMMON_SUBTITLE_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "ru", "name": "Russian"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh", "name": "Chinese"},
    {"code": "tr", "name": "Turkish"},
    {"code": "it", "name": "Italian"},
    {"code": "id", "name": "Indonesian"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "th", "name": "Thai"},
]


async def get_subtitle_main_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    current_lang = data.get("subs_lang", "OFF")
    return {
        "current_lang": current_lang,
        "subs_enabled": current_lang != "OFF",
    }


async def get_language_list_data(dialog_manager: DialogManager, **kwargs) -> dict:
    current_lang = dialog_manager.dialog_data.get("subs_lang", "OFF")
    languages = []
    for lang in COMMON_SUBTITLE_LANGUAGES:
        is_active = lang["code"] == current_lang
        languages.append({
            **lang,
            "active": is_active,
            "display": f">> {lang['name']}" if is_active else lang["name"],
        })
    return {"languages": languages, "current_lang": current_lang}


async def get_confirm_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    lang_code = data.get("subs_lang", "OFF")
    lang_name = lang_code
    for lang in COMMON_SUBTITLE_LANGUAGES:
        if lang["code"] == lang_code:
            lang_name = lang["name"]
            break
    return {
        "lang_code": lang_code,
        "lang_name": lang_name,
    }
