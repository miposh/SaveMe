from aiogram.fsm.state import State, StatesGroup


class FormatSG(StatesGroup):
    main = State()
    quality_grid = State()
    codec_select = State()
    custom_format = State()
    confirm = State()
