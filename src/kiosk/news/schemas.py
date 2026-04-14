from datetime import date

from pydantic import BaseModel


class NewsDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: str
    sort_order: int

    class Config:
        from_attributes = True


class NewsItemModel(BaseModel):
    id: int
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[NewsDocumentModel] = []

    class Config:
        from_attributes = True


class NewsItemCreateModel(BaseModel):
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True


class NewsItemUpdateModel(BaseModel):
    published_at: date | None = None
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None


class NewsDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: str
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
