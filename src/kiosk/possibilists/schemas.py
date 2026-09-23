from datetime import datetime

from pydantic import ConfigDict, BaseModel, Field

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
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str
    thumbnail_path: str | None = Field(default=None, max_length=500)
    is_visible: bool = True
    category_id: int | None = None


class PossibilistItemUpdateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    thumbnail_path: str | None = Field(default=None, max_length=500)
    is_visible: bool | None = None
    category_id: int | None = None


class PossibilistDocumentCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(max_length=500)
    type: DocumentType
    sort_order: int = 0


class ResponseModel(BaseModel):
    success: bool = True
