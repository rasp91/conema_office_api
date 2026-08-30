from datetime import datetime
import json

from pydantic import BaseModel, Field, field_validator

# Keep in sync with the activity_logs table column widths (src/database/models/activity_logs.py) -
# values that don't fit are rejected here with a 422 instead of silently failing on commit inside
# log_activity()'s best-effort write.
MAX_META_BYTES = 4096


class ActivityLogCreateModel(BaseModel):
    action_type: str = Field(max_length=30)
    resource_type: str | None = Field(default=None, max_length=50)
    resource_id: int | None = None
    meta: dict | None = None
    path: str | None = Field(default=None, max_length=255)

    @field_validator("meta")
    @classmethod
    def limit_meta_size(cls, value: dict | None) -> dict | None:
        if value is not None and len(json.dumps(value)) > MAX_META_BYTES:
            raise ValueError(f"meta must serialize to at most {MAX_META_BYTES} bytes.")
        return value


class ResponseModel(BaseModel):
    success: bool = True


class ActivityCountItem(BaseModel):
    key: str
    count: int


class ActivityDeviceCountItem(BaseModel):
    ip_address: str
    device_id: str | None = None
    device_name: str | None = None
    domain_name: str | None = None
    count: int


class ActivityItemCountItem(BaseModel):
    resource_type: str
    resource_id: int
    title: str
    count: int


class ActivitySummaryPeriod(BaseModel):
    total_events: int
    unique_devices: int
    top_resource_type: str | None = None
    top_action_type: str | None = None


class ActivitySummaryModel(BaseModel):
    current: ActivitySummaryPeriod
    previous: ActivitySummaryPeriod


class ActivityLogItemModel(BaseModel):
    id: int
    created_at: datetime
    ip_address: str | None = None
    device_id: str | None = None
    device_name: str | None = None
    user_agent: str | None = None
    action_type: str
    resource_type: str | None = None
    resource_id: int | None = None
    path: str | None = None
    meta: dict | None = None

    class Config:
        from_attributes = True


class PaginatedActivityLogsModel(BaseModel):
    items: list[ActivityLogItemModel]
    total: int
    page: int
    page_size: int
