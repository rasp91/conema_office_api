from sqlalchemy.orm import selectinload, Session
from sqlalchemy import update, select, func
from fastapi import status, HTTPException, APIRouter, Request, Depends

from src.database.models.kiosk_presentation_documents import PresentationDocument
from src.database.models.kiosk_presentation_items import PresentationItem
from src.kiosk.presentations.schemas import (
    PresentationDocumentCreateModel,
    PresentationItemUpdateModel,
    PresentationItemCreateModel,
    PresentationDocumentModel,
    PresentationItemModel,
    ResponseModel,
)
from src.kiosk.presentations import get_presentation_or_404
from src.activity_log.logger import log_activity
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.enums import ResourceType, DocumentType, ActionType
from src.auth import get_auth_user

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Presentations",
    response_model=list[PresentationItemModel],
)
def get_presentations(db: Session = Depends(get_db)) -> list[PresentationItem]:
    try:
        items = (
            db.execute(
                select(PresentationItem)
                .where(PresentationItem.is_visible == True)  # noqa: E712
                .options(selectinload(PresentationItem.documents), selectinload(PresentationItem.category))
                .order_by(PresentationItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch presentations.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Presentations",
    dependencies=[Depends(get_auth_user)],
    response_model=list[PresentationItemModel],
)
def get_all_presentations(db: Session = Depends(get_db)) -> list[PresentationItem]:
    try:
        items = (
            db.execute(
                select(PresentationItem)
                .options(selectinload(PresentationItem.documents), selectinload(PresentationItem.category))
                .order_by(PresentationItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch presentations.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Presentation",
    dependencies=[Depends(get_auth_user)],
    response_model=PresentationItemModel,
)
def create_presentation(data: PresentationItemCreateModel, db: Session = Depends(get_db)) -> PresentationItem:
    try:
        item = PresentationItem(
            published_at=func.now(),
            title=data.title,
            description=data.description,
            thumbnail_path=data.thumbnail_path,
            is_visible=data.is_visible,
            category_id=data.category_id,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        # Eagerly load relationships for response
        db.execute(
            select(PresentationItem)
            .where(PresentationItem.id == item.id)
            .options(selectinload(PresentationItem.documents), selectinload(PresentationItem.category))
        ).scalar_one()
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create presentation.")


@router.put(
    "/{presentation_id}",
    status_code=status.HTTP_200_OK,
    name="Update Presentation",
    dependencies=[Depends(get_auth_user)],
    response_model=PresentationItemModel,
)
def update_presentation(presentation_id: int, data: PresentationItemUpdateModel, db: Session = Depends(get_db)) -> PresentationItem:
    try:
        item = get_presentation_or_404(presentation_id, db)

        item.published_at = func.now()
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        if "category_id" in data.model_fields_set:
            item.category_id = data.category_id
        stale_file = None
        # Allow explicitly setting thumbnail_path to None (removal)
        if "thumbnail_path" in data.model_fields_set:
            # Old file is removed from disk only after the commit succeeds
            if item.thumbnail_path and item.thumbnail_path != data.thumbnail_path:
                stale_file = item.thumbnail_path
            item.thumbnail_path = data.thumbnail_path

        db.commit()
        delete_file(stale_file)
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update presentation.")


@router.delete(
    "/{presentation_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Presentation",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_presentation(presentation_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = get_presentation_or_404(presentation_id, db)

        # Collect files first, remove them from disk only once the DB delete is committed
        files = [item.thumbnail_path] + [doc.file_path for doc in item.documents if doc.type != DocumentType.YOUTUBE]

        db.delete(item)
        db.commit()
        for file_path in files:
            delete_file(file_path)
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete presentation.")


@router.post(
    "/{presentation_id}/views",
    status_code=status.HTTP_200_OK,
    name="Increment Presentation Views",
    response_model=ResponseModel,
)
def increment_views(presentation_id: int, request: Request, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        # updated_at is pinned to itself so a view doesn't count as an edit (ORM onupdate would bump it)
        result = db.execute(
            update(PresentationItem)
            .where(PresentationItem.id == presentation_id)
            .values(views=PresentationItem.views + 1, updated_at=PresentationItem.updated_at)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found.")
        db.commit()
        log_activity(db, request, ActionType.VIEW_DETAIL, ResourceType.PRESENTATION, presentation_id)
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment views.")


@router.post(
    "/{presentation_id}/documents",
    status_code=status.HTTP_201_CREATED,
    name="Add Presentation Document",
    dependencies=[Depends(get_auth_user)],
    response_model=PresentationDocumentModel,
)
def add_document(presentation_id: int, data: PresentationDocumentCreateModel, db: Session = Depends(get_db)) -> PresentationDocument:
    try:
        get_presentation_or_404(presentation_id, db)
        doc = PresentationDocument(
            presentation_item_id=presentation_id,
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
    "/{presentation_id}/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Presentation Document",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_document(presentation_id: int, doc_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        doc = db.execute(
            select(PresentationDocument).where(
                PresentationDocument.id == doc_id,
                PresentationDocument.presentation_item_id == presentation_id,
            )
        ).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        file_path = doc.file_path if doc.type != DocumentType.YOUTUBE else None
        db.delete(doc)
        db.commit()
        delete_file(file_path)
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document.")
