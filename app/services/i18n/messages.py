import logging
from typing import Any

logger = logging.getLogger(__name__)

_LANGUAGE_CACHE: dict[str, Any] = {}


class Messages:
    def __init__(self, language_code: str = "en") -> None:
        self._lang = language_code
        self._messages = _load_language(language_code)

    def __getattr__(self, name: str) -> str:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._messages.get(name, f"[{name}]")

    def get(self, key: str, default: str = "") -> str:
        return self._messages.get(key, default or f"[{key}]")


def _load_language(code: str) -> dict[str, str]:
    if code in _LANGUAGE_CACHE:
        return _LANGUAGE_CACHE[code]

    try:
        if code == "ru":
            from app.services.i18n.locales.ru import MESSAGES
        elif code == "ar":
            from app.services.i18n.locales.ar import MESSAGES
        elif code == "hi":
            from app.services.i18n.locales.hi import MESSAGES
        else:
            from app.services.i18n.locales.en import MESSAGES

        _LANGUAGE_CACHE[code] = MESSAGES
        return MESSAGES
    except ImportError:
        logger.warning("Language %s not found, falling back to en", code)
        from app.services.i18n.locales.en import MESSAGES
        _LANGUAGE_CACHE[code] = MESSAGES
        return MESSAGES


def get_messages(language_code: str = "en") -> Messages:
    return Messages(language_code)
