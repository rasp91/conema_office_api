import datetime
import re

from pydantic import model_validator, ConfigDict, BaseModel, Field

from src.enums import DocumentType


class TeamEventDocumentModel(BaseModel):
    id: int
    name: str
    file_path: str
    type: DocumentType
    sort_order: int

    class Config:
        from_attributes = True


class TeamEventModel(BaseModel):
    id: int
    date: datetime.date
    title: str
    description: str
    thumbnail_path: str | None
    is_visible: bool
    views: int = 0
    documents: list[TeamEventDocumentModel] = []

    class Config:
        from_attributes = True


class TeamEventCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    date: datetime.date
    title: str = Field(min_length=1, max_length=255)
    description: str
    thumbnail_path: str | None = Field(default=None, max_length=500)
    is_visible: bool = True


class TeamEventUpdateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    date: datetime.date | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    thumbnail_path: str | None = Field(default=None, max_length=500)
    is_visible: bool | None = None


class TeamEventDocumentCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(max_length=500)
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
