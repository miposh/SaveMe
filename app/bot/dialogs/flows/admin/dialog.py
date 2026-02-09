from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const, Format

from app.bot.dialogs.flows.admin.getters import (
    get_admin_list_data,
    get_broadcast_confirm_data,
    get_broadcast_result_data,
    get_stats_data,
    get_user_info_data,
)
from app.bot.dialogs.flows.admin.handlers import (
    broadcast_text_check,
    on_add_admin_success,
    on_broadcast_text_error,
    on_broadcast_text_success,
    on_close_dialog,
    on_go_back,
    on_go_to_add_admin,
    on_go_to_admin_list,
    on_go_to_broadcast,
    on_go_to_manage_admins,
    on_go_to_remove_admin,
    on_go_to_stats,
    on_go_to_user_info,
    on_go_to_users,
    on_remove_admin_success,
    on_select_segment_active,
    on_select_segment_all,
    on_send_broadcast,
    on_user_info_error,
    on_user_info_success,
    user_info_check,
)
from app.bot.dialogs.flows.admin.states import AdminSG

admin_dialog = Dialog(
    # Main menu
    Window(
        Const("<b>Admin Panel</b>\n\nSelect an option:"),
        Column(
            Button(Const("Stats"), id="stats", on_click=on_go_to_stats),
            Button(Const("Users"), id="users", on_click=on_go_to_users),
            Button(Const("Broadcast"), id="broadcast", on_click=on_go_to_broadcast),
            Button(Const("Manage Admins"), id="admins", on_click=on_go_to_manage_admins),
            Button(Const("Close"), id="close", on_click=on_close_dialog),
        ),
        state=AdminSG.main,
        parse_mode=ParseMode.HTML,
    ),
    # Stats
    Window(
        Format(
            "<b>Statistics</b>\n\n"
            "Total users: <b>{total_users}</b>\n"
            "Total downloads: <b>{total_downloads}</b>\n"
            "Active today: <b>{active_today}</b>"
        ),
        Button(Const("Back"), id="back", on_click=on_go_back),
        state=AdminSG.stats,
        getter=get_stats_data,
        parse_mode=ParseMode.HTML,
    ),
    # Users menu
    Window(
        Const("<b>Users</b>\n\nSearch for a user:"),
        Column(
            Button(Const("Find user"), id="find_user", on_click=on_go_to_user_info),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=AdminSG.users,
        parse_mode=ParseMode.HTML,
    ),
    # User info input
    Window(
        Const("<b>Enter user ID or @username:</b>"),
        TextInput(
            id="user_info_input",
            type_factory=user_info_check,
            on_success=on_user_info_success,
            on_error=on_user_info_error,
        ),
        Button(Const("Back"), id="back", on_click=on_go_to_users),
        state=AdminSG.user_info_input,
        parse_mode=ParseMode.HTML,
    ),
    # User info result
    Window(
        Format(
            "<b>User Info</b>\n\n"
            "ID: <code>{user_id}</code>\n"
            "Username: @{username}\n"
            "Name: {first_name}\n"
            "Downloads: {downloads}\n"
            "Banned: {is_banned}\n"
            "Language: {language}\n"
            "Created: {created_at}"
        ),
        Button(Const("Back"), id="back", on_click=on_go_to_users),
        state=AdminSG.user_info_result,
        getter=get_user_info_data,
        parse_mode=ParseMode.HTML,
    ),
    # Broadcast input
    Window(
        Const("<b>Enter broadcast text:</b>"),
        TextInput(
            id="broadcast_input",
            type_factory=broadcast_text_check,
            on_success=on_broadcast_text_success,
            on_error=on_broadcast_text_error,
        ),
        Button(Const("Back"), id="back", on_click=on_go_back),
        state=AdminSG.broadcast_input,
        parse_mode=ParseMode.HTML,
    ),
    # Broadcast segment selection
    Window(
        Const("<b>Select target segment:</b>"),
        Column(
            Button(Const("All users"), id="seg_all", on_click=on_select_segment_all),
            Button(Const("Active users (30d)"), id="seg_active", on_click=on_select_segment_active),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=AdminSG.broadcast_segment,
        parse_mode=ParseMode.HTML,
    ),
    # Broadcast confirmation
    Window(
        Format(
            "<b>Confirm broadcast</b>\n\n"
            "Segment: <b>{segment}</b>\n"
            "Text:\n{broadcast_text}"
        ),
        Row(
            Button(Const("Cancel"), id="cancel", on_click=on_go_back),
            Button(Const("Send"), id="send", on_click=on_send_broadcast),
        ),
        state=AdminSG.broadcast_confirm,
        getter=get_broadcast_confirm_data,
        parse_mode=ParseMode.HTML,
    ),
    # Broadcast result
    Window(
        Format(
            "<b>Broadcast Complete</b>\n\n"
            "Sent: {sent}\n"
            "Failed: {failed}\n"
            "Blocked: {blocked}"
        ),
        Button(Const("Close"), id="close", on_click=on_close_dialog),
        state=AdminSG.broadcast_result,
        getter=get_broadcast_result_data,
        parse_mode=ParseMode.HTML,
    ),
    # Manage admins menu
    Window(
        Const("<b>Manage Admins</b>"),
        Column(
            Button(Const("Admin list"), id="admin_list", on_click=on_go_to_admin_list),
            Button(Const("Add admin"), id="add_admin", on_click=on_go_to_add_admin),
            Button(Const("Remove admin"), id="remove_admin", on_click=on_go_to_remove_admin),
            Button(Const("Back"), id="back", on_click=on_go_back),
        ),
        state=AdminSG.manage_admins,
        parse_mode=ParseMode.HTML,
    ),
    # Add admin input
    Window(
        Const("<b>Enter user ID to add as admin:</b>"),
        TextInput(
            id="add_admin_input",
            type_factory=user_info_check,
            on_success=on_add_admin_success,
            on_error=on_user_info_error,
        ),
        Button(Const("Back"), id="back", on_click=on_go_to_manage_admins),
        state=AdminSG.add_admin_input,
        parse_mode=ParseMode.HTML,
    ),
    # Remove admin input
    Window(
        Const("<b>Enter user ID to remove from admins:</b>"),
        TextInput(
            id="remove_admin_input",
            type_factory=user_info_check,
            on_success=on_remove_admin_success,
            on_error=on_user_info_error,
        ),
        Button(Const("Back"), id="back", on_click=on_go_to_manage_admins),
        state=AdminSG.remove_admin_input,
        parse_mode=ParseMode.HTML,
    ),
    # Admin list
    Window(
        Format("<b>Admin List</b>\n\n{admins_text}"),
        Button(Const("Back"), id="back", on_click=on_go_to_manage_admins),
        state=AdminSG.admin_list,
        getter=get_admin_list_data,
        parse_mode=ParseMode.HTML,
    ),
)
