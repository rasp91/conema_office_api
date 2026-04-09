from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.kiosk_events import KioskEvent


def get_event_or_404(event_id: int, db: Session) -> KioskEvent:
    item = db.execute(select(KioskEvent).where(KioskEvent.id == event_id)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return item
