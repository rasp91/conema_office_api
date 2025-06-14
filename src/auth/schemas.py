import datetime

from pydantic import field_validator, BaseModel, EmailStr, Field


class AuthLoginResponse(BaseModel):
    success: bool = False
    access_token: str | None = None
    error: str = ""


class AuthUserResponseModel(BaseModel):
    id: int
    username: str
    enabled: bool


class AuthRegisterModel(BaseModel):
    username: str = Field(..., min_length=4, description="Username")
    password: str = Field(..., min_length=6, description="Current password")
    email: EmailStr = Field(..., description="Valid email address is required")
    first_name: str = Field(..., min_length=3, description="First name")
    last_name: str = Field(..., min_length=3, description="Last name")


class AuthChangePasswordModel(BaseModel):
    old_password: str = Field(..., min_length=6, description="Current password")
    new_password: str = Field(..., min_length=6, description="New password, at least 6 characters")
    confirm_password: str = Field(..., description="Must match new_password")

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        if "new_password" in values.data and confirm_password != values.data["new_password"]:
            raise ValueError("New password and confirm password must match")
        return confirm_password


class AuthEditUserModel(BaseModel):
    username: str = Field(..., min_length=4, description="Username")
    email: EmailStr = Field(..., description="Valid email address is required")
    first_name: str = Field(..., min_length=3, description="First name")
    last_name: str = Field(..., min_length=3, description="Last name")


class AuthResetPasswordModel(BaseModel):
    username: str = Field(..., min_length=4, description="Username")
    new_password: str = Field(..., min_length=6, description="New password, at least 6 characters")
    confirm_password: str = Field(..., description="Must match new_password")

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        if "new_password" in values.data and confirm_password != values.data["new_password"]:
            raise ValueError("New password and confirm password must match")
        return confirm_password


class AuthUserListResponseModel(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    last_login: datetime.datetime
    enabled: bool
    is_admin: bool


class AuthUser(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    is_admin: bool
    exp: int
