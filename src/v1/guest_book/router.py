import unicodedata
import re
import io

from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.v1.guest_book.schemas import *
from src.v1.guest_book.form import generate_form
from src.database.models import GuestBook,  Form
from src.database import get_db
from src.logger import logger
from src.auth import get_admin_user

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    name="Register guest",
    response_model=ResponseModel,
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
            company=data.company,
            phone=data.phone,
            email=data.email,
            pdf_file=pdf_bytes,
        )
        db.add(guest_entry)
        db.commit()

        # Return response
        return {}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with guest registration.")


@router.get(
    "/get-guest-book",
    status_code=status.HTTP_200_OK,
    name="Get Guest Book",
    dependencies=[Depends(get_admin_user)],
    response_model=list[GuestBookModel],
)
def get_guest_book(db: Session = Depends(get_db)) -> None:
    try:
        # Get all forms from the database
        guest_book_data = db.execute(select(GuestBook)).scalars().all()
        # Use Pydantic to convert ORM objects to dicts
        return guest_book_data
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching guest book data.")


@router.get(
    "/download-form/{guest_book_id}",
    status_code=status.HTTP_200_OK,
    name="Download Guest Book Form",
    dependencies=[Depends(get_admin_user)],
)
def download_report(guest_book_id: int, db: Session = Depends(get_db)):
    def remove_diacritics(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    try:
        # Guest Data
        guest_data = db.execute(select(GuestBook).where(GuestBook.id == guest_book_id)).scalar_one_or_none()
        if not guest_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found")

        # Form Data
        form_data = io.BytesIO(guest_data.pdf_file)
        form_data.seek(0)
        form_content = form_data.getvalue()
        filename = remove_diacritics(
            f"{guest_data.last_name}_{guest_data.first_name}_{guest_data.created_at.strftime('%Y%m%d_%H%M%S')}.pdf".lower().strip()
        )

        # Headers
        headers = {
            "Content-Disposition": f'attachment; name="fieldName"; filename="{filename}"',
            "Content-Type": "application/pdf",
            "Content-Length": str(len(form_content)),
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
        # Return Success Response
        return Response(
            content=form_content,
            media_type="application/pdf",
            headers=headers,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with downloading guest form [{e}]."
        )
