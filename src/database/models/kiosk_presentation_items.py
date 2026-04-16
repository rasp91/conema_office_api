from sqlalchemy.dialects.mysql import BIGINT, LONGTEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, TIMESTAMP

from src.database.base import Base


class PresentationItem(Base):
    __tablename__ = "kiosk_presentation_items"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    published_at: Mapped[str] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    category_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("kiosk_presentation_categories.id", ondelete="SET NULL"), nullable=True
    )

    category = relationship("PresentationCategory", back_populates="presentations")
    documents = relationship(
        "PresentationDocument", back_populates="presentation_item", cascade="all, delete-orphan", order_by="PresentationDocument.sort_order"
    )

    @property
    def category_name(self) -> str | None:
        return self.category.name if self.category else None

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
