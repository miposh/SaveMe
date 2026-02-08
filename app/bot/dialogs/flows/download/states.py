from aiogram.fsm.state import State, StatesGroup


class DownloadSG(StatesGroup):
    preview = State()
