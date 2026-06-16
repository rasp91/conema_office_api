import re
from datetime import datetime

from pydantic import model_validator, BaseModel

from src.enums import DocumentType


class NewsDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: DocumentType
    sort_order: int

    class Config:
        from_attributes = True


class NewsItemModel(BaseModel):
    id: int
    published_at: datetime
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[NewsDocumentModel] = []

    class Config:
        from_attributes = True


class NewsItemCreateModel(BaseModel):
    title: str
    description: str
    thumbnail_path: str | None = None
    is_visible: bool = True


class NewsItemUpdateModel(BaseModel):
    title: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_visible: bool | None = None


class NewsDocumentCreateModel(BaseModel):
    name: str
    file_path: str
    type: DocumentType
    sort_order: int = 0

    @model_validator(mode="after")
    def validate_youtube_url(self):
        if self.type == DocumentType.YOUTUBE:
            if not re.match(r"^https://(www\.)?(youtube\.com|youtu\.be)/", self.file_path):
                raise ValueError("file_path must be a valid YouTube URL for type youtube")
        return self


class ResponseModel(BaseModel):
    success: bool = True
