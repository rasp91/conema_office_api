from collections.abc import Sequence

from sqlalchemy.orm import selectinload, Session
from sqlalchemy import update, select
from fastapi import status, HTTPException, APIRouter, Request, Depends

from src.database.models.kiosk_team_event_documents import TeamEventDocument
from src.database.models.kiosk_team_events import TeamEvent
from src.kiosk.team_events.schemas import (
    TeamEventDocumentCreateModel,
    TeamEventDocumentModel,
    TeamEventUpdateModel,
    TeamEventCreateModel,
    TeamEventModel,
    ResponseModel,
)
from src.activity_log.logger import log_activity
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.enums import ResourceType, DocumentType, ActionType
from src.auth import get_auth_user

router = APIRouter()


def _get_team_event_or_404(team_event_id: int, db: Session) -> TeamEvent:
    item = db.execute(
        select(TeamEvent).where(TeamEvent.id == team_event_id).options(selectinload(TeamEvent.documents))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team event not found.")
    return item


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Team Events",
    response_model=list[TeamEventModel],
)
def get_team_events(db: Session = Depends(get_db)) -> Sequence[TeamEvent]:
    try:
        items = (
            db.execute(
                select(TeamEvent)
                .where(TeamEvent.is_visible == True)  # noqa: E712
                .options(selectinload(TeamEvent.documents))
                .order_by(TeamEvent.date.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch team events.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Team Events (Admin)",
    dependencies=[Depends(get_auth_user)],
    response_model=list[TeamEventModel],
)
def get_all_team_events(db: Session = Depends(get_db)) -> Sequence[TeamEvent]:
    try:
        items = db.execute(select(TeamEvent).options(selectinload(TeamEvent.documents)).order_by(TeamEvent.date.desc())).scalars().all()
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch team events.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Team Event",
    dependencies=[Depends(get_auth_user)],
    response_model=TeamEventModel,
)
def create_team_event(data: TeamEventCreateModel, db: Session = Depends(get_db)) -> TeamEvent:
    try:
        item = TeamEvent(
            date=data.date,
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create team event.")


@router.put(
    "/{team_event_id}",
    status_code=status.HTTP_200_OK,
    name="Update Team Event",
    dependencies=[Depends(get_auth_user)],
    response_model=TeamEventModel,
)
def update_team_event(team_event_id: int, data: TeamEventUpdateModel, db: Session = Depends(get_db)) -> TeamEvent:
    try:
        item = _get_team_event_or_404(team_event_id, db)

        if data.date is not None:
            item.date = data.date
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        # Allow explicitly setting thumbnail_path to None (removal)
        if "thumbnail_path" in data.model_fields_set:
            # Delete old thumbnail if being replaced or cleared
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update team event.")


@router.delete(
    "/{team_event_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Team Event",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_team_event(team_event_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = _get_team_event_or_404(team_event_id, db)

        # Delete all associated files from disk
        if item.thumbnail_path:
            delete_file(item.thumbnail_path)
        for doc in item.documents:
            if doc.type != DocumentType.YOUTUBE:
                delete_file(doc.file_path)

        db.delete(item)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete team event.")


@router.post(
    "/{team_event_id}/views",
    status_code=status.HTTP_200_OK,
    name="Increment Team Event Views",
    response_model=ResponseModel,
)
def increment_views(team_event_id: int, request: Request, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        result = db.execute(update(TeamEvent).where(TeamEvent.id == team_event_id).values(views=TeamEvent.views + 1))
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team event not found.")
        db.commit()
        log_activity(db, request, ActionType.VIEW_DETAIL, ResourceType.TEAM_EVENT, team_event_id)
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment views.")


@router.post(
    "/{team_event_id}/documents",
    status_code=status.HTTP_201_CREATED,
    name="Add Team Event Document",
    dependencies=[Depends(get_auth_user)],
    response_model=TeamEventDocumentModel,
)
def add_document(team_event_id: int, data: TeamEventDocumentCreateModel, db: Session = Depends(get_db)) -> TeamEventDocument:
    try:
        _get_team_event_or_404(team_event_id, db)
        doc = TeamEventDocument(
            team_event_id=team_event_id,
            name=data.name,
            file_path=data.file_path,
            type=data.type,
            sort_order=data.sort_order,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add document.")


@router.delete(
    "/{team_event_id}/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Team Event Document",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_document(team_event_id: int, doc_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        doc = db.execute(
            select(TeamEventDocument).where(TeamEventDocument.id == doc_id, TeamEventDocument.team_event_id == team_event_id)
        ).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        if doc.type != DocumentType.YOUTUBE:
            delete_file(doc.file_path)
        db.delete(doc)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document.")
