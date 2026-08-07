from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.sql import func
from sqlalchemy import JSON, String, Index, TIMESTAMP

from src.database.base import Base


class ActivityLog(Base):
    """Usage-tracking log for anonymous kiosk activity (page views, item opens, document opens).

    Written explicitly from the kiosk view/detail endpoints and from the generic
    POST /kiosk/activity/log endpoint — see src/activity_log/logger.py.
    """

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_resource_type_created_at", "resource_type", "created_at"),
        Index("ix_activity_logs_device_id_created_at", "device_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
