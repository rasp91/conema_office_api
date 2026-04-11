from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import Enum, ForeignKey, Integer, String

from src.database.base import Base


class PresentationDocument(Base):
    __tablename__ = "kiosk_presentation_documents"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    presentation_item_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("kiosk_presentation_items.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(Enum("image", "file"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    presentation_item = relationship("PresentationItem", back_populates="documents")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
