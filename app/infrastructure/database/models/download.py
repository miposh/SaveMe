from datetime import datetime

from pydantic import BaseModel, Field


class DownloadModel(BaseModel):
    id: int | None = None
    user_id: int
    url: str
    url_hash: str
    domain: str | None = None
    title: str | None = None
    duration_sec: int | None = None
    file_size_bytes: int | None = None
    quality: str | None = None
    media_type: str = "video"
    telegram_file_id: str | None = None
    telegram_msg_id: int | None = None
    tags: list = Field(default_factory=list)
    is_nsfw: bool = False
    is_playlist: bool = False
    playlist_index: int | None = None
    error: str | None = None
    created_at: datetime | None = None
