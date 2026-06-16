from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select, func
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models.kiosk_possibilist_categories import PossibilistCategory
from src.database.models.kiosk_possibilist_documents import PossibilistDocument
from src.database.models.kiosk_possibilist_items import PossibilistItem
from src.kiosk.possibilists.schemas import (
    PossibilistDocumentCreateModel,
    PossibilistItemUpdateModel,
    PossibilistItemCreateModel,
    PossibilistDocumentModel,
    PossibilistItemModel,
    ResponseModel,
)
from src.kiosk.possibilists import get_possibilist_or_404
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.enums import DocumentType
from src.auth import get_auth_user

router = APIRouter()


def _validate_category(category_id: int | None, db: Session) -> None:
    if category_id is None:
        return
    category = db.execute(select(PossibilistCategory).where(PossibilistCategory.id == category_id)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    if not category.is_group:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Category is not selectable (is_group must be true).")


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Possibilists",
    response_model=list[PossibilistItemModel],
)
def get_possibilists(db: Session = Depends(get_db)) -> list[PossibilistItem]:
    try:
        items = (
            db.execute(
                select(PossibilistItem)
                .where(PossibilistItem.is_visible == True)  # noqa: E712
                .options(selectinload(PossibilistItem.documents), selectinload(PossibilistItem.category))
                .order_by(PossibilistItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch possibilists.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All Possibilists",
    dependencies=[Depends(get_auth_user)],
    response_model=list[PossibilistItemModel],
)
def get_all_possibilists(db: Session = Depends(get_db)) -> list[PossibilistItem]:
    try:
        items = (
            db.execute(
                select(PossibilistItem)
                .options(selectinload(PossibilistItem.documents), selectinload(PossibilistItem.category))
                .order_by(PossibilistItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch possibilists.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Possibilist",
    dependencies=[Depends(get_auth_user)],
    response_model=PossibilistItemModel,
)
def create_possibilist(data: PossibilistItemCreateModel, db: Session = Depends(get_db)) -> PossibilistItem:
    try:
        _validate_category(data.category_id, db)
        item = PossibilistItem(
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
        item = db.execute(
            select(PossibilistItem)
            .where(PossibilistItem.id == item.id)
            .options(selectinload(PossibilistItem.documents), selectinload(PossibilistItem.category))
        ).scalar_one()
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create possibilist.")


@router.put(
    "/{possibilist_id}",
    status_code=status.HTTP_200_OK,
    name="Update Possibilist",
    dependencies=[Depends(get_auth_user)],
    response_model=PossibilistItemModel,
)
def update_possibilist(possibilist_id: int, data: PossibilistItemUpdateModel, db: Session = Depends(get_db)) -> PossibilistItem:
    try:
        item = get_possibilist_or_404(possibilist_id, db)

        if "category_id" in data.model_fields_set:
            _validate_category(data.category_id, db)

        item.published_at = func.now()
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        if "category_id" in data.model_fields_set:
            item.category_id = data.category_id
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update possibilist.")


@router.delete(
    "/{possibilist_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Possibilist",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_possibilist(possibilist_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = get_possibilist_or_404(possibilist_id, db)

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete possibilist.")


@router.post(
    "/{possibilist_id}/views",
    status_code=status.HTTP_200_OK,
    name="Increment Possibilist Views",
    response_model=ResponseModel,
)
def increment_views(possibilist_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = db.execute(select(PossibilistItem).where(PossibilistItem.id == possibilist_id)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Possibilist not found.")
        item.views = (item.views or 0) + 1
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment views.")


@router.post(
    "/{possibilist_id}/documents",
    status_code=status.HTTP_201_CREATED,
    name="Add Possibilist Document",
    dependencies=[Depends(get_auth_user)],
    response_model=PossibilistDocumentModel,
)
def add_document(possibilist_id: int, data: PossibilistDocumentCreateModel, db: Session = Depends(get_db)) -> PossibilistDocument:
    try:
        get_possibilist_or_404(possibilist_id, db)
        doc = PossibilistDocument(
            possibilist_item_id=possibilist_id,
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
    "/{possibilist_id}/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Possibilist Document",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_document(possibilist_id: int, doc_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        doc = db.execute(
            select(PossibilistDocument).where(
                PossibilistDocument.id == doc_id,
                PossibilistDocument.possibilist_item_id == possibilist_id,
            )
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
