from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/vid"),
                KeyboardButton(text="/audio"),
                KeyboardButton(text="/img"),
            ],
            [
                KeyboardButton(text="/format"),
                KeyboardButton(text="/settings"),
                KeyboardButton(text="/help"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
