from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import LargeBinary, String, TIMESTAMP

from src.database.base import Base


class GuestBook(Base):
    __tablename__ = "guest_book"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    pdf_file: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
