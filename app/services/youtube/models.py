from pydantic import BaseModel, ConfigDict


class VideoFormat(BaseModel):
    model_config = ConfigDict(frozen=True)

    height: int
    ext: str
    filesize: int | None = None
    format_note: str | None = None


class VideoInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    video_id: str
    title: str
    thumbnail_url: str
    duration: int
    formats: list[VideoFormat]
