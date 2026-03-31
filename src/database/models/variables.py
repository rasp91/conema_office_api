from sqlalchemy.dialects.mysql import BIGINT, TEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, TIMESTAMP

from src.database.base import Base


class Variable(Base):
    __tablename__ = "variables"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(TEXT, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g. "int", "float", "bool", "str", "json"
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
