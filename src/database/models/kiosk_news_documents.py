from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import ForeignKey, Integer, String, Enum

from src.database.base import Base


class NewsDocument(Base):
    __tablename__ = "kiosk_news_documents"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    news_item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("kiosk_news_items.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(Enum("image", "file"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    news_item = relationship("NewsItem", back_populates="documents")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
