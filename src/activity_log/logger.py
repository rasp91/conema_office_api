from sqlalchemy.orm import Session
from fastapi import Request

from src.database.models.activity_logs import ActivityLog
from src.logger import app_logger


def extract_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For may hold a comma-separated chain (client, proxy1, proxy2, ...) — first entry is the client.
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def extract_device(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("x-device-id"), request.headers.get("x-device-name")


def log_activity(
    db: Session,
    request: Request,
    action_type: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    meta: dict | None = None,
    path: str | None = None,
) -> None:
    """Best-effort activity log write.

    Never raises — a failure to log kiosk usage must never break the caller's actual request.
    """
    try:
        device_id, device_name = extract_device(request)
        entry = ActivityLog(
            ip_address=extract_ip(request),
            device_id=device_id,
            device_name=device_name,
            user_agent=request.headers.get("user-agent"),
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            path=path or request.url.path,
            meta=meta,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        app_logger.exception(e)
        db.rollback()
