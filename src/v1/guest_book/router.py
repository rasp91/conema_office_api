import re

from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.v1.guest_book.schemas import CompaniesResponseModel, RegisterResponseModel, RegisterModel
from src.v1.guest_book.form import generate_form
from src.database.models import GuestBook, Company, Form
from src.database import get_db
from src.logger import logger

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    name="Register guest",
    response_model=RegisterResponseModel,
)
def register(data: RegisterModel, db: Session = Depends(get_db)) -> None:
    try:
        # Validate signature
        match = re.match(r"^data:image/.+;base64,(.+)$", data.signature)
        if not match:
            return JSONResponse(status_code=400, content={"detail": "Invalid signature image format."})

        # Get Form
        form_name = str(data.locate).strip().lower()
        form_data = db.execute(select(Form).where(Form.name == form_name)).scalar_one_or_none()
        if not form_data:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": f"Form with name '{form_name}' not found."})

        # Generate PDF file
        report = generate_form(data, form_data.content)
        report.seek(0)
        pdf_bytes = report.getvalue()

        # Save data to the database
        guest_entry = GuestBook(
            first_name=data.name,
            last_name=data.surname,
            company=data.company.name,
            phone=data.phone,
            email=data.email,
            pdf_file=pdf_bytes,
        )
        db.add(guest_entry)
        db.commit()

        # Create a new company if it does not exist
        company = db.execute(select(Company).where(Company.name == data.company.name)).scalar_one_or_none()
        if not company:
            company = Company(name=data.company.name)
            db.add(company)
            db.commit()

        # Return the PDF as a response
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=generated.pdf"})
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with guest registration.")


# ---------------------------
# Companies
# ---------------------------
@router.get(
    "/get-companies",
    status_code=status.HTTP_200_OK,
    name="Get Companies",
    response_model=list[CompaniesResponseModel],
)
def get_companies(db: Session = Depends(get_db)) -> None:
    try:
        # Return all companies from the database
        return db.execute(select(Company).order_by(Company.name.asc())).scalars().all()
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching companies data.")
