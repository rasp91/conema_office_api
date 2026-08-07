from datetime import timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import status, HTTPException, APIRouter, Request, Depends, Query

from src.database.models.activity_logs import ActivityLog
from src.activity_log.schemas import (
    ActivityDeviceCountItem,
    ActivityLogCreateModel,
    ActivityCountItem,
    ResponseModel,
)
from src.activity_log.logger import log_activity
from src.database import get_db
from src.logger import app_logger
from src.auth import get_admin_user

router = APIRouter()


@router.post(
    "/log",
    status_code=status.HTTP_200_OK,
    name="Log Kiosk Activity",
    response_model=ResponseModel,
)
def log_kiosk_activity(data: ActivityLogCreateModel, request: Request, db: Session = Depends(get_db)) -> ResponseModel:
    log_activity(
        db,
        request,
        data.action_type,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        meta=data.meta,
        path=data.path,
    )
    return ResponseModel()


def _date_range_filter(date_from: date | None, date_to: date | None) -> list:
    conditions = []
    if date_from is not None:
        conditions.append(ActivityLog.created_at >= date_from)
    if date_to is not None:
        # date_to is inclusive of the whole day
        conditions.append(ActivityLog.created_at < date_to + timedelta(days=1))
    return conditions


@router.get(
    "/report/top-sections",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Top Sections",
    dependencies=[Depends(get_admin_user)],
    response_model=list[ActivityCountItem],
)
def report_top_sections(
    date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)
) -> list[ActivityCountItem]:
    try:
        query = select(ActivityLog.resource_type, func.count().label("count")).where(ActivityLog.resource_type.is_not(None))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.resource_type).order_by(func.count().desc())
        rows = db.execute(query).all()
        return [ActivityCountItem(key=row.resource_type, count=row.count) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build top-sections report.")


@router.get(
    "/report/top-devices",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Top Devices",
    dependencies=[Depends(get_admin_user)],
    response_model=list[ActivityDeviceCountItem],
)
def report_top_devices(
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ActivityDeviceCountItem]:
    try:
        query = select(
            ActivityLog.device_id,
            func.max(ActivityLog.device_name).label("device_name"),
            func.count().label("count"),
        ).where(ActivityLog.device_id.is_not(None))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.device_id).order_by(func.count().desc()).limit(limit)
        rows = db.execute(query).all()
        return [ActivityDeviceCountItem(device_id=row.device_id, device_name=row.device_name, count=row.count) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build top-devices report.")


@router.get(
    "/report/timeseries",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Timeseries",
    dependencies=[Depends(get_admin_user)],
    response_model=list[ActivityCountItem],
)
def report_timeseries(
    date_from: date | None = None,
    date_to: date | None = None,
    bucket: str = Query(default="day", pattern="^(day|hour)$"),
    db: Session = Depends(get_db),
) -> list[ActivityCountItem]:
    try:
        bucket_expr = (
            func.date_format(ActivityLog.created_at, "%Y-%m-%d %H:00")
            if bucket == "hour"
            else func.date_format(ActivityLog.created_at, "%Y-%m-%d")
        )
        query = select(bucket_expr.label("bucket"), func.count().label("count"))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by("bucket").order_by("bucket")
        rows = db.execute(query).all()
        return [ActivityCountItem(key=row.bucket, count=row.count) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build timeseries report.")
