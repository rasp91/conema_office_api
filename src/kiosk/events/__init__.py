from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select
from fastapi import status, HTTPException

from src.database.models.kiosk_events import KioskEvent


def get_event_or_404(event_id: int, db: Session) -> KioskEvent:
    item = db.execute(select(KioskEvent).where(KioskEvent.id == event_id).options(selectinload(KioskEvent.documents))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return item
