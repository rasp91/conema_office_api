from datetime import timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import status, HTTPException, APIRouter, Request, Depends, Query

from src.database.models.kiosk_sharepoint_articles import SharePointArticle
from src.database.models.kiosk_internal_info_items import InternalInfoItem
from src.database.models.kiosk_presentation_items import PresentationItem
from src.database.models.kiosk_possibilist_items import PossibilistItem
from src.database.models.kiosk_news_items import NewsItem
from src.database.models.activity_logs import ActivityLog
from src.database.models.kiosk_events import KioskEvent
from src.activity_log.schemas import (
    PaginatedActivityLogsModel,
    ActivityDeviceCountItem,
    ActivityLogCreateModel,
    ActivitySummaryPeriod,
    ActivityItemCountItem,
    ActivitySummaryModel,
    ActivityLogItemModel,
    ActivityCountItem,
    ResponseModel,
)
from src.activity_log.logger import log_activity
from src.database import get_db
from src.logger import app_logger
from src.auth import get_admin_user
from src.enums import ResourceType, ActionType

router = APIRouter()

# The "home" resource_type is logged on every kiosk idle/landing view, so it dominates any
# section ranking without telling us anything about what visitors actually engage with.
# Excluded from the section breakdowns/top-section summary below rather than from logging
# itself, so the raw event is still recorded and visible in the log listing.
EXCLUDED_SECTIONS = (ResourceType.HOME, ResourceType.DOCUMENT)

# resource_type -> (ORM model, title column) for the "view_detail" events that carry a
# resource_id pointing at an actual content item. Keys mirror the singular resource_type
# strings written by each kiosk detail endpoint's log_activity() call (see e.g.
# src/kiosk/news/router.py) — distinct from the plural route-name strings page_view logs
# for the top-sections breakdown above.
ITEM_TITLE_MODELS: dict[str, tuple[type, str]] = {
    ResourceType.NEWS: (NewsItem, "title"),
    ResourceType.EVENT: (KioskEvent, "title"),
    ResourceType.INTERNAL_INFO: (InternalInfoItem, "title"),
    ResourceType.POSSIBILIST: (PossibilistItem, "title"),
    ResourceType.PRESENTATION: (PresentationItem, "title"),
    ResourceType.SHAREPOINT_ARTICLE: (SharePointArticle, "title"),
}


def _resolve_item_titles(db: Session, rows) -> dict[tuple[str, int], str]:
    """Batch-resolves current titles for a set of grouped (resource_type, resource_id) rows.

    One lookup query per resource_type rather than a row-by-row fetch. Items that no longer
    exist (deleted news/event/... or a SharePoint article removed by sync) simply fall back
    to a placeholder below — the click counts stay meaningful even once the content is gone.
    """
    ids_by_type: dict[str, set[int]] = {}
    for row in rows:
        ids_by_type.setdefault(row.resource_type, set()).add(row.resource_id)

    titles: dict[tuple[str, int], str] = {}
    for r_type, ids in ids_by_type.items():
        model, title_attr = ITEM_TITLE_MODELS[r_type]
        # SharePointArticle's primary key is the SharePoint list item id stored as a string
        # (see kiosk_sharepoint_articles.py) - every other model here uses an int BIGINT id.
        pk_values = [str(i) for i in ids] if r_type == "sharepoint-article" else list(ids)
        found = db.execute(select(model.id, getattr(model, title_attr)).where(model.id.in_(pk_values))).all()
        for item_id, title in found:
            titles[(r_type, int(item_id))] = title
    return titles


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
        query = select(ActivityLog.resource_type, func.count().label("count")).where(
            ActivityLog.resource_type.is_not(None),
            ActivityLog.resource_type.not_in(EXCLUDED_SECTIONS),
            ActivityLog.action_type == ActionType.PAGE_VIEW,
        )
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.resource_type).order_by(func.count().desc())
        rows = db.execute(query).all()
        return [ActivityCountItem(key=row.resource_type, count=row._mapping["count"]) for row in rows]
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
        return [ActivityCountItem(key=row.action_type, count=row._mapping["count"]) for row in rows]
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build top-actions report.")


@router.get(
    "/report/top-items",
    status_code=status.HTTP_200_OK,
    name="Activity Report - Top Items",
    dependencies=[Depends(get_admin_user)],
    response_model=list[ActivityItemCountItem],
)
def report_top_items(
    date_from: date | None = None,
    date_to: date | None = None,
    resource_type: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ActivityItemCountItem]:
    if resource_type is not None and resource_type not in ITEM_TITLE_MODELS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported resource_type for item breakdown.")
    try:
        allowed_types = [resource_type] if resource_type else list(ITEM_TITLE_MODELS)
        query = select(ActivityLog.resource_type, ActivityLog.resource_id, func.count().label("count")).where(
            ActivityLog.resource_type.in_(allowed_types), ActivityLog.resource_id.is_not(None)
        )
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.resource_type, ActivityLog.resource_id).order_by(func.count().desc()).limit(limit)
        rows = db.execute(query).all()
        titles = _resolve_item_titles(db, rows)
        return [
            ActivityItemCountItem(
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                title=titles.get((row.resource_type, row.resource_id), f"Smazaná položka #{row.resource_id}"),
                count=row._mapping["count"],
            )
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to build top-items report.")


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
            func.max(ActivityLog.ip_address).label("ip_address"),
            func.max(ActivityLog.device_name).label("device_name"),
            func.count().label("count"),
        ).where(ActivityLog.device_id.is_not(None))
        for condition in _date_range_filter(date_from, date_to):
            query = query.where(condition)
        query = query.group_by(ActivityLog.device_id).order_by(func.count().desc()).limit(limit)
        rows = db.execute(query).all()
        return [
            ActivityDeviceCountItem(
                device_id=row.device_id, ip_address=row.ip_address, device_name=row.device_name, count=row._mapping["count"]
            )
            for row in rows
        ]
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
        return [ActivityCountItem(key=row.bucket, count=row._mapping["count"]) for row in rows]
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
        .where(ActivityLog.resource_type.is_not(None), ActivityLog.resource_type.not_in(EXCLUDED_SECTIONS))
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
