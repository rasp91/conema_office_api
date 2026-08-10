from datetime import datetime

from pydantic import BaseModel


class ActivityLogCreateModel(BaseModel):
    action_type: str
    resource_type: str | None = None
    resource_id: int | None = None
    meta: dict | None = None
    path: str | None = None


class ResponseModel(BaseModel):
    success: bool = True


class ActivityCountItem(BaseModel):
    key: str
    count: int


class ActivityDeviceCountItem(BaseModel):
    device_id: str
    device_name: str | None = None
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
