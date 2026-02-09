from aiogram.filters.callback_data import CallbackData


class QualityAction(CallbackData, prefix="quality"):
    url_hash: str
    quality: str


class FormatAction(CallbackData, prefix="fmt"):
    url_hash: str
    format_id: str


class SettingsAction(CallbackData, prefix="settings"):
    menu: str
    action: str = ""


class AdminAction(CallbackData, prefix="admin"):
    menu: str
    action: str = ""
    target_id: int = 0


class SubtitleAction(CallbackData, prefix="subs"):
    action: str
    lang: str = ""


class ProxyAction(CallbackData, prefix="proxy"):
    action: str


class CookieAction(CallbackData, prefix="cookie"):
    action: str
    service: str = ""


class LangAction(CallbackData, prefix="lang"):
    code: str


class HelpAction(CallbackData, prefix="help"):
    action: str


class PreviewAction(CallbackData, prefix="prev"):
    action: str
    url_hash: str
    quality: str = ""
