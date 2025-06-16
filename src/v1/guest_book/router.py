import base64
import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import status, HTTPException, APIRouter, Depends

from src.v1.guest_book.schemas import CompaniesResponseModel, RegisterResponseModel, RegisterModel
from src.database import get_db
from src.logger import logger
from src.config import config

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
        # Extract base64 part
        match = re.match(r"^data:image/.+;base64,(.+)$", data.signature)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid signature image format.")

        # Decode base64 image data
        signature_data = base64.b64decode(match.group(1))

        # Save to file
        path = Path(config.DATA_PATH) / "guest_book"
        path.mkdir(exist_ok=True)
        signature_filename = path / f"{uuid4()}.png"
        with open(signature_filename, "wb") as fh:
            fh.write(signature_data)

        # Generate PDF file
        # report = generate_report(data, signature_filename)
        # report.seek(0)
        # print(f"Report generated successfully!")
        # report_content = report.read()
        # filename = f"report_{order_data.production_order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Remove the signature file after PDF generation
        # if signature_filename.exists():
        #     print(f"Signature file {signature_filename} created successfully.")
        #     signature_filename.unlink()

        # Return all companies from the database
        return {}
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
        return []
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching companies data.")
