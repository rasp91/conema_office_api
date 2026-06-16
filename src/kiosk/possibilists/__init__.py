from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select
from fastapi import status, HTTPException

from src.database.models.kiosk_possibilist_items import PossibilistItem


def get_possibilist_or_404(possibilist_id: int, db: Session) -> PossibilistItem:
    item = db.execute(
        select(PossibilistItem)
        .where(PossibilistItem.id == possibilist_id)
        .options(selectinload(PossibilistItem.documents), selectinload(PossibilistItem.category))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Possibilist not found.")
    return item
