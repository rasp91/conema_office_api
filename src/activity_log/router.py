from datetime import timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import status, HTTPException, APIRouter, Request, Depends, Query

from src.database.models.activity_logs import ActivityLog
from src.activity_log.schemas import (
    PaginatedActivityLogsModel,
    ActivityDeviceCountItem,
    ActivityLogCreateModel,
    ActivitySummaryPeriod,
    ActivityLogItemModel,
    ActivitySummaryModel,
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
    "/report/top-actions",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Top Actions",
    dependencies=[Depends(get_admin_user)],
    response_model=list[ActivityCountItem],
)
def report_top_actions(
    date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)
) -> list[ActivityCountItem]:
    try:
        query = select(ActivityLog.action_type, func.count().label("count"))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.action_type).order_by(func.count().desc())
        rows = db.execute(query).all()
        return [ActivityCountItem(key=row.action_type, count=row.count) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build top-actions report.")


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
    bucket: str = Query(default="day", pattern="^(day|hour|month)$"),
    db: Session = Depends(get_db),
) -> list[ActivityCountItem]:
    try:
        if bucket == "hour":
            bucket_expr = func.date_format(ActivityLog.created_at, "%Y-%m-%d %H:00")
        elif bucket == "month":
            bucket_expr = func.date_format(ActivityLog.created_at, "%Y-%m")
        else:
            bucket_expr = func.date_format(ActivityLog.created_at, "%Y-%m-%d")
        query = select(bucket_expr.label("bucket"), func.count().label("count"))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by("bucket").order_by("bucket")
        rows = db.execute(query).all()
        return [ActivityCountItem(key=row.bucket, count=row.count) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build timeseries report.")


def _summary_for_range(db: Session, date_from: date | None, date_to: date | None) -> ActivitySummaryPeriod:
    conditions = _date_range_filter(date_from, date_to)

    count_query = select(func.count(), func.count(func.distinct(ActivityLog.device_id)))
    for condition in conditions:
        count_query = count_query.where(condition)
    total_events, unique_devices = db.execute(count_query).one()

    top_resource_query = (
        select(ActivityLog.resource_type)
        .where(ActivityLog.resource_type.is_not(None))
        .group_by(ActivityLog.resource_type)
        .order_by(func.count().desc())
        .limit(1)
    )
    top_action_query = select(ActivityLog.action_type).group_by(ActivityLog.action_type).order_by(func.count().desc()).limit(1)
    for condition in conditions:
        top_resource_query = top_resource_query.where(condition)
        top_action_query = top_action_query.where(condition)

    return ActivitySummaryPeriod(
        total_events=total_events,
        unique_devices=unique_devices,
        top_resource_type=db.execute(top_resource_query).scalar(),
        top_action_type=db.execute(top_action_query).scalar(),
    )


@router.get(
    "/report/summary",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Summary",
    dependencies=[Depends(get_admin_user)],
    response_model=ActivitySummaryModel,
)
def report_summary(date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)) -> ActivitySummaryModel:
    try:
        # Default to a trailing 7-day window when no range is given, so the "previous period"
        # comparison below always has a well-defined equal-length window to compare against.
        effective_to = date_to or date.today()
        effective_from = date_from or (effective_to - timedelta(days=6))

        period_length = (effective_to - effective_from).days + 1
        previous_to = effective_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=period_length - 1)

        return ActivitySummaryModel(
            current=_summary_for_range(db, effective_from, effective_to),
            previous=_summary_for_range(db, previous_from, previous_to),
        )
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build summary report.")


@router.get(
    "/report/logs",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Logs",
    dependencies=[Depends(get_admin_user)],
    response_model=PaginatedActivityLogsModel,
)
def report_logs(
    date_from: date | None = None,
    date_to: date | None = None,
    action_type: str | None = None,
    resource_type: str | None = None,
    device_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
) -> PaginatedActivityLogsModel:
    try:
        conditions = _date_range_filter(date_from, date_to)
        if action_type is not None:
            conditions.append(ActivityLog.action_type == action_type)
        if resource_type is not None:
            conditions.append(ActivityLog.resource_type == resource_type)
        if device_id is not None:
            conditions.append(ActivityLog.device_id == device_id)

        count_query = select(func.count()).select_from(ActivityLog)
        rows_query = select(ActivityLog).order_by(ActivityLog.created_at.desc())
        for condition in conditions:
            count_query = count_query.where(condition)
            rows_query = rows_query.where(condition)
        rows_query = rows_query.offset((page - 1) * page_size).limit(page_size)

        total = db.execute(count_query).scalar_one()
        rows = db.execute(rows_query).scalars().all()
        return PaginatedActivityLogsModel(
            items=[ActivityLogItemModel.model_validate(row) for row in rows], total=total, page=page, page_size=page_size
        )
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build activity log listing.")
