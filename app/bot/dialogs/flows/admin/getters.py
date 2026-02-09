from aiogram_dialog import DialogManager

from app.infrastructure.database.db import DB


async def get_stats_data(dialog_manager: DialogManager, **kwargs) -> dict:
    db: DB = dialog_manager.middleware_data.get("db")
    if not db:
        return {"total_users": 0, "total_downloads": 0, "active_today": 0}

    try:
        total_users = await db.users.get_users_count()
        total_downloads = await db.downloads.get_total_count()

        active_result = await db.users.get_active_users(days=1)
        active_today = len(active_result) if active_result else 0

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            "active_today": active_today,
        }
    except Exception:
        return {"total_users": 0, "total_downloads": 0, "active_today": 0}


async def get_user_info_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    return {
        "user_id": data.get("user_id", "N/A"),
        "username": data.get("username", "N/A"),
        "first_name": data.get("first_name", "N/A"),
        "downloads": data.get("downloads", 0),
        "is_banned": data.get("is_banned", False),
        "language": data.get("language", "en"),
        "created_at": data.get("created_at", "N/A"),
    }


async def get_broadcast_confirm_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    return {
        "broadcast_text": data.get("broadcast_text", ""),
        "segment": data.get("segment", "all"),
    }


async def get_broadcast_result_data(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    return {
        "sent": data.get("sent", 0),
        "failed": data.get("failed", 0),
        "blocked": data.get("blocked", 0),
    }


async def get_admin_list_data(dialog_manager: DialogManager, **kwargs) -> dict:
    db: DB = dialog_manager.middleware_data.get("db")
    if not db:
        return {"admins_text": "No data"}

    try:
        result = await db.admins.get_all()
        admins = result.as_dicts() if result else []
        if not admins:
            return {"admins_text": "No admins found"}

        lines = []
        for admin in admins:
            admin_id = admin.get("id", "?")
            username = admin.get("username", "unknown")
            lines.append(f"- {admin_id} (@{username})")
        return {"admins_text": "\n".join(lines)}
    except Exception:
        return {"admins_text": "Error loading admins"}
