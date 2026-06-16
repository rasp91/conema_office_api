from datetime import datetime

from pydantic import BaseModel

from src.enums import DocumentType


class PossibilistDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: DocumentType
    sort_order: int

    class Config:
        from_attributes = True


class PossibilistItemModel(BaseModel):
    id: int
    published_at: datetime
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    category_id: int | None
    category_name: str | None
    documents: list[PossibilistDocumentModel] = []

    class Config:
        from_attributes = True


class PossibilistItemCreateModel(BaseModel):
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True
    category_id: int | None = None


class PossibilistItemUpdateModel(BaseModel):
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None
    category_id: int | None = None


class PossibilistDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: DocumentType
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
