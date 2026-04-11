from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models.kiosk_presentation_categories import PresentationCategory
from src.kiosk.presentation_categories.schemas import (
    PresentationCategoryUpdateModel,
    PresentationCategoryCreateModel,
    PresentationCategoryModel,
    ResponseModel,
)
from src.kiosk.presentation_categories import get_category_or_404
from src.database import get_db
from src.logger import app_logger
from src.auth import get_auth_user

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Presentation Categories",
    response_model=list[PresentationCategoryModel],
)
def get_categories(db: Session = Depends(get_db)) -> list[PresentationCategory]:
    try:
        items = db.execute(select(PresentationCategory).order_by(PresentationCategory.name)).scalars().all()
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch presentation categories.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Presentation Category",
    dependencies=[Depends(get_auth_user)],
    response_model=PresentationCategoryModel,
)
def create_category(data: PresentationCategoryCreateModel, db: Session = Depends(get_db)) -> PresentationCategory:
    try:
        item = PresentationCategory(name=data.name)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create presentation category.")


@router.put(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    name="Update Presentation Category",
    dependencies=[Depends(get_auth_user)],
    response_model=PresentationCategoryModel,
)
def update_category(category_id: int, data: PresentationCategoryUpdateModel, db: Session = Depends(get_db)) -> PresentationCategory:
    try:
        item = get_category_or_404(category_id, db)
        if data.name is not None:
            item.name = data.name
        db.commit()
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update presentation category.")


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Presentation Category",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = get_category_or_404(category_id, db)
        db.delete(item)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete presentation category.")
