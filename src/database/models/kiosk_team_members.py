from sqlalchemy.dialects.mysql import LONGTEXT, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Boolean, String, TIMESTAMP

from src.database.base import Base


class TeamMember(Base):
    __tablename__ = "kiosk_team_members"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
