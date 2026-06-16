from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException

from src.database.models.kiosk_possibilist_categories import PossibilistCategory


def get_category_or_404(category_id: int, db: Session) -> PossibilistCategory:
    item = db.execute(select(PossibilistCategory).where(PossibilistCategory.id == category_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Possibilist category not found.")
    return item
