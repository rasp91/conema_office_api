from collections.abc import Sequence
from datetime import timedelta, date

from sqlalchemy.orm import selectinload, Session
from sqlalchemy import update, select, func
from fastapi import status, HTTPException, APIRouter, Request, Depends

from src.database.models.kiosk_internal_info_documents import InternalInfoDocument
from src.database.models.kiosk_internal_info_items import InternalInfoItem
from src.kiosk.internal_info.schemas import (
    InternalInfoDocumentCreateModel,
    InternalInfoItemUpdateModel,
    InternalInfoItemCreateModel,
    InternalInfoDocumentModel,
    InternalInfoItemModel,
    ResponseModel,
)
from src.activity_log.logger import log_activity
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.enums import ResourceType, DocumentType, ActionType
from src.auth import get_auth_user

router = APIRouter()


def _get_item_or_404(item_id: int, db: Session) -> InternalInfoItem:
    item = db.execute(
        select(InternalInfoItem).where(InternalInfoItem.id == item_id).options(selectinload(InternalInfoItem.documents))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal info item not found.")
    return item


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Internal Info",
    response_model=list[InternalInfoItemModel],
)
def get_internal_info(db: Session = Depends(get_db)) -> Sequence[InternalInfoItem]:
    try:
        items = (
            db.execute(
                select(InternalInfoItem)
                .where(
                    InternalInfoItem.is_visible == True,  # noqa: E712
                    InternalInfoItem.published_at >= date.today() - timedelta(days=365),
                )
                .options(selectinload(InternalInfoItem.documents))
                .order_by(InternalInfoItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch internal info.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Internal Info (Admin)",
    dependencies=[Depends(get_auth_user)],
    response_model=list[InternalInfoItemModel],
)
def get_all_internal_info(db: Session = Depends(get_db)) -> Sequence[InternalInfoItem]:
    try:
        items = (
            db.execute(
                select(InternalInfoItem).options(selectinload(InternalInfoItem.documents)).order_by(InternalInfoItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch internal info.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Internal Info",
    dependencies=[Depends(get_auth_user)],
    response_model=InternalInfoItemModel,
)
def create_internal_info(data: InternalInfoItemCreateModel, db: Session = Depends(get_db)) -> InternalInfoItem:
    try:
        item = InternalInfoItem(
            published_at=func.now(),
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create internal info item.")


@router.put(
    "/{item_id}",
    status_code=status.HTTP_200_OK,
    name="Update Internal Info",
    dependencies=[Depends(get_auth_user)],
    response_model=InternalInfoItemModel,
)
def update_internal_info(item_id: int, data: InternalInfoItemUpdateModel, db: Session = Depends(get_db)) -> InternalInfoItem:
    try:
        item = _get_item_or_404(item_id, db)

        item.published_at = func.now()
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        stale_file = None
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update internal info item.")


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Internal Info",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_internal_info(item_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = _get_item_or_404(item_id, db)

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete internal info item.")


@router.post(
    "/{item_id}/views",
    status_code=status.HTTP_200_OK,
    name="Increment Internal Info Views",
    response_model=ResponseModel,
)
def increment_views(item_id: int, request: Request, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        # updated_at is pinned to itself so a view doesn't count as an edit (ORM onupdate would bump it)
        result = db.execute(
            update(InternalInfoItem)
            .where(InternalInfoItem.id == item_id)
            .values(views=InternalInfoItem.views + 1, updated_at=InternalInfoItem.updated_at)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internal info item not found.")
        db.commit()
        log_activity(db, request, ActionType.VIEW_DETAIL, ResourceType.INTERNAL_INFO, item_id)
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment views.")


@router.post(
    "/{item_id}/documents",
    status_code=status.HTTP_201_CREATED,
    name="Add Internal Info Document",
    dependencies=[Depends(get_auth_user)],
    response_model=InternalInfoDocumentModel,
)
def add_document(item_id: int, data: InternalInfoDocumentCreateModel, db: Session = Depends(get_db)) -> InternalInfoDocument:
    try:
        _get_item_or_404(item_id, db)
        doc = InternalInfoDocument(
            info_item_id=item_id,
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
    "/{item_id}/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Internal Info Document",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_document(item_id: int, doc_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        doc = db.execute(
            select(InternalInfoDocument).where(InternalInfoDocument.id == doc_id, InternalInfoDocument.info_item_id == item_id)
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
