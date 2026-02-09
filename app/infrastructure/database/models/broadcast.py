from datetime import datetime

from pydantic import BaseModel


class BroadcastModel(BaseModel):
    id: int | None = None
    admin_id: int
    text: str
    media_file_id: str | None = None
    media_type: str | None = None
    url_buttons: str | None = None
    segment: str = "all"
    scheduled_at: datetime | None = None
    status: str = "draft"
    is_ab_test: bool = False
    ab_variant: str | None = None
    ab_parent_id: int | None = None
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    blocked_count: int = 0
    created_at: datetime | None = None
    completed_at: datetime | None = None
