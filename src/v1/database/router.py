from sqlalchemy.orm import Session
from fastapi import status, HTTPException, APIRouter, Depends

from src.database import get_db
from src.logger import logger

router = APIRouter()


@router.post(
    "/rebuild-database",
    status_code=status.HTTP_200_OK,
    name="Rebuild Database",
    response_model=dict[str, bool],
)
def rebuild_database(db: Session = Depends(get_db)) -> None:
    try:
        from src.database.models import create_default_admin_user, create_all_tables, drop_all_tables

        # Drop all tables
        drop_all_tables()
        logger.info("Database tables have been successfully dropped.")
        # Recreate all tables
        create_all_tables()
        logger.info("Database tables have been successfully rebuilt.")
        # Create default admin user
        create_default_admin_user(db)
        logger.info("Default admin user has been successfully created.")
        # Use Pydantic to convert ORM objects to dicts
        return {"success": True}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching orders data.")
