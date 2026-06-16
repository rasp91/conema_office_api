from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import Integer, Boolean, String

from src.database.base import Base


class PossibilistCategory(Base):
    __tablename__ = "kiosk_possibilist_categories"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    possibilists = relationship("PossibilistItem", back_populates="category")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
