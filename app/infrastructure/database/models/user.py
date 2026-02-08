from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    downloads_count: int = 0
    created_at: datetime | None = None
    last_activity: datetime | None = None
