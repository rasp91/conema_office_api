from sqlalchemy.dialects.mysql import LONGTEXT, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import ForeignKey, String, TIMESTAMP

from src.database.models.users import User
from src.database.base import Base


class Form(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    created_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(LONGTEXT, nullable=True)

    # Add two separate relationships, one for each FK
    creator = relationship(User, foreign_keys=[created_by], backref="created_forms")
    updater = relationship(User, foreign_keys=[updated_by], backref="updated_forms")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
