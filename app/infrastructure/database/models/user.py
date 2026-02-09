from datetime import datetime

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    id: int
    username: str | None = None
    first_name: str = ""
    last_name: str | None = None
    language_code: str = "en"
    is_premium: bool = False
    is_banned: bool = False
    ban_reason: str | None = None
    ban_until: datetime | None = None
    count_downloads: int = 0
    count_audio: int = 0
    count_images: int = 0
    count_playlists: int = 0
    preferred_codec: str = "avc1"
    preferred_mkv: bool = False
    split_size_mb: int = 0
    subs_enabled: bool = False
    subs_language: str = "en"
    subs_auto_mode: str = "off"
    keyboard_mode: str = "2x3"
    nsfw_enabled: bool = False
    custom_args: dict = Field(default_factory=dict)
    created_at: datetime | None = None
    last_activity: datetime | None = None
