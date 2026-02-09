from aiogram.fsm.state import State, StatesGroup


class SubtitleSG(StatesGroup):
    main = State()
    language_list = State()
    confirm = State()
