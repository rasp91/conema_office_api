from datetime import date

from pydantic import BaseModel

from src.enums import DocumentType


class PresentationDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: DocumentType
    sort_order: int

    class Config:
        from_attributes = True


class PresentationItemModel(BaseModel):
    id: int
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    category_id: int | None
    category_name: str | None
    documents: list[PresentationDocumentModel] = []

    class Config:
        from_attributes = True


class PresentationItemCreateModel(BaseModel):
    published_at: date
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True
    category_id: int | None = None


class PresentationItemUpdateModel(BaseModel):
    published_at: date | None = None
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None
    category_id: int | None = None


class PresentationDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: DocumentType
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
