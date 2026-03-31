from sqlalchemy.dialects.mysql import VARCHAR, BOOLEAN, BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, TIMESTAMP

from src.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    last_login: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    username: Mapped[str] = mapped_column(String(20), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    remember_token: Mapped[str] = mapped_column(VARCHAR(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(BOOLEAN(), nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(BOOLEAN(), nullable=False, default=False)
