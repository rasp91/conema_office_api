from fastapi.responses import JSONResponse
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload, Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.v1.forms.schemas import FormCreateModel, ResponseModel, FormModel
from src.database.models import Form
from src.auth.schemas import AuthUser
from src.database import get_db
from src.logger import logger
from src.auth import get_admin_user

router = APIRouter()


@router.get(
    "/get-form",
    status_code=status.HTTP_200_OK,
    name="Get Form",
    response_model=FormModel,
)
def get_form(locate: str, gdpr: bool = False, db: Session = Depends(get_db)) -> None:
    try:
        # Form Conditions
        form_name = str(locate).strip().lower()
        if gdpr:
            form_name = f"{locate}_gdpr"
        # Get all forms from the database
        form_data = db.execute(select(Form).where(Form.name == form_name).options(joinedload(Form.updater))).scalar_one_or_none()
        if not form_data:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"Form with name '{form_name}' not found."},
            )
        # Return the form data
        return form_data
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching form data.")


@router.get(
    "/get-forms",
    status_code=status.HTTP_200_OK,
    name="Get Forms",
    dependencies=[Depends(get_admin_user)],
    response_model=list[FormModel],
)
def get_forms(db: Session = Depends(get_db)) -> None:
    try:
        # Get all forms from the database
        forms_data = db.execute(select(Form).options(joinedload(Form.updater))).scalars().all()
        # Use Pydantic to convert ORM objects to dicts
        return forms_data
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with fetching forms data.")


@router.post(
    "/create",
    status_code=status.HTTP_200_OK,
    name="Create Form",
    dependencies=[Depends(get_admin_user)],
    response_model=ResponseModel,
)
def create_form(data: FormCreateModel, db: Session = Depends(get_db), user: AuthUser = Depends(get_admin_user)) -> None:
    try:
        # Variables
        form_name = str(data.name).strip().lower()

        # Validate form
        form_data = db.execute(select(Form).where(Form.name == form_name)).scalar_one_or_none()
        if form_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Form with name '{form_name}' already exists.")

        # Create a record
        form = Form(
            created_by=user.id,
            updated_by=user.id,
            name=form_name,
            content=data.content,
        )
        db.add(form)
        db.commit()

        # Return the created form
        return {}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with creating new form.")


@router.put(
    "/edit/{form_id}",
    status_code=status.HTTP_200_OK,
    name="Edit Form",
    dependencies=[Depends(get_admin_user)],
    response_model=ResponseModel,
)
def edit_form(form_id: int, data: FormCreateModel, db: Session = Depends(get_db), user: AuthUser = Depends(get_admin_user)) -> None:
    try:
        # Fetch the order to ensure it exists
        form = db.execute(select(Form).where(Form.id == form_id)).scalar_one_or_none()
        if not form:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        # Edit record
        form.updated_by = user.id
        form.updated_at = func.now()
        form.content = data.content
        db.commit()

        # Return all companies from the database
        return {}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"There is a problem with guest registration.")


@router.delete(
    "/delete-form/{form_id}",
    status_code=status.HTTP_200_OK,
    name="Delete Form",
    dependencies=[Depends(get_admin_user)],
    response_model=ResponseModel,
)
def delete_form(form_id: int, db: Session = Depends(get_db)) -> None:
    try:
        form = db.execute(select(Form).where(Form.id == form_id)).scalar_one_or_none()
        if not form:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found.")
        db.delete(form)
        db.commit()
        # Return response
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="There is a problem with deleting the form.")
