from aiogram.fsm.state import State, StatesGroup


class AdminSG(StatesGroup):
    main = State()
    stats = State()
    users = State()
    user_info_input = State()
    user_info_result = State()
    broadcast_input = State()
    broadcast_segment = State()
    broadcast_confirm = State()
    broadcast_result = State()
    manage_admins = State()
    add_admin_input = State()
    remove_admin_input = State()
    admin_list = State()
