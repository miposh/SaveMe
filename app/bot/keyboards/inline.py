from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.factories import (
    HelpAction,
    LangAction,
    PreviewAction,
    SettingsAction,
)


def close_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Close", callback_data=HelpAction(action="close"))
    return builder


def language_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    languages = [
        ("English", "en"),
        ("Русский", "ru"),
        ("العربية", "ar"),
        ("हिन्दी", "hi"),
    ]
    for name, code in languages:
        builder.button(text=name, callback_data=LangAction(code=code))
    builder.adjust(2)
    return builder


def youtube_preview_keyboard(
    url_hash: str,
    available_qualities: list[str],
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()

    # Quality buttons row (e.g. 360p, 720p, 1080p)
    for q in available_qualities:
        builder.button(
            text=f"\U0001f4f9 {q}p",
            callback_data=PreviewAction(action="dl", url_hash=url_hash, quality=q),
        )

    # Action buttons
    builder.button(
        text="\U0001f3a7 Аудио",
        callback_data=PreviewAction(action="audio", url_hash=url_hash),
    )
    builder.button(
        text="\U0001f4fc Кодек",
        callback_data=PreviewAction(action="codec", url_hash=url_hash),
    )
    builder.button(
        text="\U0001f517 Ссылка",
        callback_data=PreviewAction(action="link", url_hash=url_hash),
    )
    builder.button(
        text="\U0001f4c3 Форматы",
        callback_data=PreviewAction(action="formats", url_hash=url_hash),
    )

    # Layout: quality buttons in rows of 3, then action buttons 2x2
    q_count = len(available_qualities)
    if q_count == 0:
        builder.adjust(2, 2)
    elif q_count <= 3:
        builder.adjust(q_count, 2, 2)
    elif q_count <= 6:
        builder.adjust(3, q_count - 3, 2, 2)
    else:
        builder.adjust(3, 3, q_count - 6, 2, 2)

    return builder


def settings_main_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    items = [
        ("Language", "language"),
        ("Format", "format"),
        ("Split", "split"),
        ("Subtitles", "subs"),
        ("NSFW", "nsfw"),
        ("Args", "args"),
        ("Keyboard", "keyboard"),
        ("Close", "close"),
    ]
    for text, action in items:
        builder.button(
            text=text,
            callback_data=SettingsAction(menu="main", action=action),
        )
    builder.adjust(2)
    return builder
