from datetime import datetime

from pydantic import BaseModel, Field


class VideoCacheModel(BaseModel):
    id: int | None = None
    url_hash: str
    quality: str
    telegram_file_id: str
    telegram_msg_ids: list[int] = Field(default_factory=list)
    title: str | None = None
    duration_sec: int | None = None
    file_size_bytes: int | None = None
    is_playlist: bool = False
    playlist_url: str | None = None
    playlist_index: int | None = None
    created_at: datetime | None = None
