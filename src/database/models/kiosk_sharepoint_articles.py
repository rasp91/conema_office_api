from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text, TIMESTAMP

from src.database.base import Base


class SharePointArticle(Base):
    __tablename__ = "kiosk_sharepoint_articles"

    # The SharePoint list item id itself is the primary key (not an autoincrement BIGINT like
    # other models here) since every sync upserts by this natural key from the external system.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    published_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)
    icon_path: Mapped[str] = mapped_column(String(500), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
