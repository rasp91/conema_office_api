from datetime import datetime

from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, TIMESTAMP

from src.database.base import Base


class ActivityDeviceAlias(Base):
    """Admin-defined display name for a kiosk device in the activity reports, keyed by IP address
    (the same key /kiosk/activity/report/top-devices groups by). Resolved at read time, so a rename
    also applies to all historical activity_logs rows from that IP."""

    __tablename__ = "activity_device_aliases"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    # Same width as activity_logs.ip_address
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
