from datetime import date

from pydantic import BaseModel


class InternalInfoDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: str
    sort_order: int

    class Config:
        from_attributes = True


class InternalInfoItemModel(BaseModel):
    id: int
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[InternalInfoDocumentModel] = []

    class Config:
        from_attributes = True


class InternalInfoItemCreateModel(BaseModel):
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True


class InternalInfoItemUpdateModel(BaseModel):
    published_at: date | None = None
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None


class InternalInfoDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: str
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
