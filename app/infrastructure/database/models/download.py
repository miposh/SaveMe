from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DownloadModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    user_id: int
    video_url: str
    video_title: str
    download_type: str
    quality: str | None = None
    file_size: int | None = None
    status: str = "pending"
    created_at: datetime | None = None
