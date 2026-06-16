from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models.kiosk_possibilist_categories import PossibilistCategory
from src.kiosk.possibilist_categories.schemas import (
    PossibilistCategoryUpdateModel,
    PossibilistCategoryCreateModel,
    PossibilistCategoryModel,
    ResponseModel,
)
from src.kiosk.possibilist_categories import get_category_or_404
from src.database import get_db
from src.logger import app_logger
from src.auth import get_auth_user

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get Possibilist Categories",
    response_model=list[PossibilistCategoryModel],
)
def get_categories(db: Session = Depends(get_db)) -> list[PossibilistCategory]:
    try:
        items = db.execute(select(PossibilistCategory).order_by(PossibilistCategory.sort_order, PossibilistCategory.name)).scalars().all()
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch possibilist categories.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create Possibilist Category",
    dependencies=[Depends(get_auth_user)],
    response_model=PossibilistCategoryModel,
)
def create_category(data: PossibilistCategoryCreateModel, db: Session = Depends(get_db)) -> PossibilistCategory:
    try:
        item = PossibilistCategory(name=data.name, icon=data.icon, is_group=data.is_group, sort_order=data.sort_order)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create possibilist category.")


@router.put(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    name="Update Possibilist Category",
    dependencies=[Depends(get_auth_user)],
    response_model=PossibilistCategoryModel,
)
def update_category(category_id: int, data: PossibilistCategoryUpdateModel, db: Session = Depends(get_db)) -> PossibilistCategory:
    try:
        item = get_category_or_404(category_id, db)
        if data.name is not None:
            item.name = data.name
        if "icon" in data.model_fields_set:
            item.icon = data.icon
        if data.is_group is not None:
            item.is_group = data.is_group
        if data.sort_order is not None:
            item.sort_order = data.sort_order
        db.commit()
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update possibilist category.")


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Possibilist Category",
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete possibilist category.")
