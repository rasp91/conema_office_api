from pydantic import BaseModel, EmailStr


class CompaniesResponseModel(BaseModel):
    name: str

    # Pydantic configuration for datetime serialization
    class Config:
        from_attributes = True  # Allows ORM conversion


class RegisterModel(BaseModel):
    name: str
    surname: str
    acknowledged: bool = True
    gdpr: bool = False
    company: CompaniesResponseModel
    phone: str
    email: EmailStr | str
    signature: str
    locate: str
    header: str


class RegisterResponseModel(BaseModel):
    success: bool = True
