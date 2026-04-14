import datetime

from pydantic import BaseModel


class EventDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: str
    sort_order: int

    class Config:
        from_attributes = True


class EventModel(BaseModel):
    id: int
    date: datetime.date
    time: str
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[EventDocumentModel] = []

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


class EventDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: str
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
