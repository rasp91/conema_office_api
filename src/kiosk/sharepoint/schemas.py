from datetime import datetime

from pydantic import BaseModel


class SharePointArticleModel(BaseModel):
    id: str
    title: str
    description: str | None = None
    published_at: datetime | None = None
    icon_path: str | None = None

    class Config:
        from_attributes = True


class SharePointArticleDetailModel(BaseModel):
    id: str
    title: str
    body_html: str
    published_at: datetime | None = None
    web_url: str | None = None
    has_icon: bool

    class Config:
        from_attributes = True


class SyncResponseModel(BaseModel):
    success: bool = True
    synced: int
