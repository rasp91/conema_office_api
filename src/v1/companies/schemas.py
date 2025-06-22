import datetime

from pydantic import BaseModel


class CompanyModel(BaseModel):
    id: int
    created_at: datetime.datetime
    name: str

    # Pydantic configuration for datetime serialization
    class Config:
        from_attributes = True  # Allows ORM conversion


class CompanyCreateModel(BaseModel):
    name: str


class ResponseModel(BaseModel):
    success: bool = True
