from datetime import datetime

from pydantic import BaseModel, Field


class StatisticsModel(BaseModel):
    id: int | None = None
    user_id: int | None = None
    event_type: str
    url: str | None = None
    domain: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime | None = None
