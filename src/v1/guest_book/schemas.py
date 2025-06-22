import datetime

from pydantic import BaseModel, EmailStr


class GuestBookModel(BaseModel):
    id: int
    created_at: datetime.datetime
    first_name: str
    last_name: str
    company: str
    phone: str
    email: EmailStr

    # Pydantic configuration for datetime serialization
    class Config:
        from_attributes = True  # Allows ORM conversion


class RegisterModel(BaseModel):
    name: str
    surname: str
    acknowledged: bool = True
    gdpr: bool = False
    company: str
    phone: str
    email: EmailStr | str
    signature: str
    locate: str
    header: str


class ResponseModel(BaseModel):
    success: bool = True
