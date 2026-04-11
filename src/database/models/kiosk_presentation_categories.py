from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import String

from src.database.base import Base


class PresentationCategory(Base):
    __tablename__ = "kiosk_presentation_categories"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    presentations = relationship("PresentationItem", back_populates="category")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
