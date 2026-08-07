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
