from datetime import datetime, date

from pydantic import BaseModel, Field

from src.database.schemas import UserModel


class FormModel(BaseModel):
    id: int
    updated_at: datetime
    updated_by: int
    name: str
    content: str
    updater: UserModel

    # Pydantic configuration for datetime serialization
    class Config:
        from_attributes = True  # Allows ORM conversion
        # json_encoders = {datetime: lambda v: v.date().isoformat()}  # Customize the format


class FormsResponseModel(BaseModel):
    name: str
    content: str


class FormCreateModel(BaseModel):
    name: str
    content: str


class FormResponseModel(BaseModel):
    success: bool = True
