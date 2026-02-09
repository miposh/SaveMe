from aiogram.fsm.state import State, StatesGroup


class SettingsSG(StatesGroup):
    main = State()
    format_settings = State()
    split_settings = State()
    language = State()
    subs_settings = State()
    custom_args = State()
    tags_settings = State()
