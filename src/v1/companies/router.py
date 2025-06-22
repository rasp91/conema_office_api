from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.v1.companies.schemas import *
from src.database.models import Company
from src.database import get_db
from src.logger import logger
from src.auth import get_admin_user

router = APIRouter()


# ---------------------------
# Companies
# ---------------------------
@router.get(
    "/get-companies",
    status_code=status.HTTP_200_OK,
    name="Get Companies",
    response_model=list[CompanyModel],
)
def get_companies(db: Session = Depends(get_db)) -> None:
    try:
        # Return all companies from the database
        return db.execute(select(Company).order_by(Company.name.asc())).scalars().all()
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching companies data.")


@router.post(
    "/create",
    status_code=status.HTTP_200_OK,
    name="Create Company",
    dependencies=[Depends(get_admin_user)],
    response_model=ResponseModel,
)
def create_company(data: CompanyCreateModel, db: Session = Depends(get_db)) -> None:
    try:
        company_name = str(data.name).strip()
        # Validate company
        company_data = db.execute(select(Company).where(Company.name == company_name)).scalar_one_or_none()
        if company_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Company with name '{company_name}' already exists.")

        # Create a record
        company = Company(
            name=company_name,
        )
        db.add(company)
        db.commit()

        # Return response
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with creating new company.")


@router.delete(
    "/delete-company/{company_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Company",
    dependencies=[Depends(get_admin_user)],
    response_model=ResponseModel,
)
def delete_company(company_id: int, db: Session = Depends(get_db)) -> None:
    try:
        company = db.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
        db.delete(company)
        db.commit()
        # Return response
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="There is a problem with deleting the company.")
