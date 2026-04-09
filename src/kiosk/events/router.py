from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth import get_auth_user
from src.database import get_db
from src.database.models.kiosk_events import KioskEvent
from src.kiosk.events import get_event_or_404
from src.kiosk.events.schemas import EventCreateModel, EventModel, EventUpdateModel, ResponseModel
from src.logger import app_logger
from src.upload import delete_file

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Events",
    response_model=list[EventModel],
)
def get_events(db: Session = Depends(get_db)) -> list[KioskEvent]:
    try:
        items = (
            db.execute(
                select(KioskEvent)
                .where(KioskEvent.is_visible == True)  # noqa: E712
                .order_by(KioskEvent.date.asc(), KioskEvent.time.asc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch events.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Events (Admin)",
    dependencies=[Depends(get_auth_user)],
    response_model=list[EventModel],
)
def get_all_events(db: Session = Depends(get_db)) -> list[KioskEvent]:
    try:
        items = (
            db.execute(
                select(KioskEvent).order_by(KioskEvent.date.asc(), KioskEvent.time.asc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch events.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Event",
    dependencies=[Depends(get_auth_user)],
    response_model=EventModel,
)
def create_event(data: EventCreateModel, db: Session = Depends(get_db)) -> KioskEvent:
    try:
        item = KioskEvent(
            date=data.date,
            time=data.time,
            title=data.title,
            description=data.description,
            thumbnail_path=data.thumbnail_path,
            is_visible=data.is_visible,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create event.")


@router.put(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    name="Update Event",
    dependencies=[Depends(get_auth_user)],
    response_model=EventModel,
)
def update_event(event_id: int, data: EventUpdateModel, db: Session = Depends(get_db)) -> KioskEvent:
    try:
        item = get_event_or_404(event_id, db)

        if data.date is not None:
            item.date = data.date
        if data.time is not None:
            item.time = data.time
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        if "thumbnail_path" in data.model_fields_set:
            if item.thumbnail_path and item.thumbnail_path != data.thumbnail_path:
                delete_file(item.thumbnail_path)
            item.thumbnail_path = data.thumbnail_path

        db.commit()
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update event.")


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Event",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = get_event_or_404(event_id, db)

        if item.thumbnail_path:
            delete_file(item.thumbnail_path)

        db.delete(item)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete event.")
