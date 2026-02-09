from datetime import datetime

from pydantic import BaseModel


class AdminModel(BaseModel):
    id: int
    username: str | None = None
    added_at: datetime | None = None
    added_by: int | None = None
