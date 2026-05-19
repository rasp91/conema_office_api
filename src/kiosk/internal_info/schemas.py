from datetime import datetime

from pydantic import BaseModel

from src.enums import DocumentType


class InternalInfoDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: DocumentType
    sort_order: int

    class Config:
        from_attributes = True


class InternalInfoItemModel(BaseModel):
    id: int
    published_at: datetime
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[InternalInfoDocumentModel] = []

    class Config:
        from_attributes = True


class InternalInfoItemCreateModel(BaseModel):
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True


class InternalInfoItemUpdateModel(BaseModel):
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None


class InternalInfoDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: DocumentType
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
