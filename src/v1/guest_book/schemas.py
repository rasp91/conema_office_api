import datetime

from pydantic import BaseModel, EmailStr, Field


class GuestBookModel(BaseModel):
    id: int
    created_at: datetime.datetime
    first_name: str
    last_name: str
    company: str
    phone: str
    email: EmailStr | None


class RegisterModel(BaseModel):
    name: str = Field(..., min_length=3, description="Name")
    surname: str = Field(..., min_length=3, description="Surname")
    acknowledged: bool = False
    gdpr: bool = False
    company: str
    phone: str = Field(..., pattern=r'^(\+\d{1,3}\s?)?\d{3,12}$', description="Phone number")
    email: EmailStr | str
    signature: str
    locate: str
    header: str


class ResponseModel(BaseModel):
    success: bool = True
