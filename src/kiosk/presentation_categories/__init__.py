from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException

from src.database.models.kiosk_presentation_categories import PresentationCategory


def get_category_or_404(category_id: int, db: Session) -> PresentationCategory:
    item = db.execute(select(PresentationCategory).where(PresentationCategory.id == category_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation category not found.")
    return item
