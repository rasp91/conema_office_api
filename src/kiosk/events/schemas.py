import datetime

from pydantic import BaseModel


class EventModel(BaseModel):
    id: int
    date: datetime.date
    time: str
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool

    class Config:
        from_attributes = True


class EventCreateModel(BaseModel):
    date: datetime.date
    time: str
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True


class EventUpdateModel(BaseModel):
    date: datetime.date | None = None
    time: str | None = None
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None


class ResponseModel(BaseModel):
    success: bool = True
