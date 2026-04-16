from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select
from fastapi import status, HTTPException

from src.database.models.kiosk_presentation_items import PresentationItem


def get_presentation_or_404(presentation_id: int, db: Session) -> PresentationItem:
    item = db.execute(
        select(PresentationItem)
        .where(PresentationItem.id == presentation_id)
        .options(selectinload(PresentationItem.documents), selectinload(PresentationItem.category))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found.")
    return item
