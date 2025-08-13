import datetime

from pydantic import field_validator, BaseModel, EmailStr, Field

USERNAME_PATTERN = r"^[a-z]+(?:[.]+)?(?:[a-z1-9]+)?$"
USERNAME_MIN_LENGTH = 4
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 32
FIRST_NAME_MIN_LENGTH = LAST_NAME_MIN_LENGTH = 2
FIRST_NAME_MAX_LENGTH = LAST_NAME_MAX_LENGTH = 255


class AuthLoginResponse(BaseModel):
    success: bool = False
    access_token: str | None = None
    error: str = ""


class AuthUserResponseModel(BaseModel):
    id: int
    username: str
    enabled: bool


class AuthRegisterModel(BaseModel):
    username: str = Field(..., pattern=USERNAME_PATTERN, min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH, description="Username")
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH, description="Current password")
    confirm_password: str = Field(..., description="Must match new_password")
    email: EmailStr = Field(..., description="Valid email address is required")
    first_name: str = Field(..., min_length=FIRST_NAME_MIN_LENGTH, max_length=FIRST_NAME_MAX_LENGTH, description="First name")
    last_name: str = Field(..., min_length=LAST_NAME_MIN_LENGTH, max_length=LAST_NAME_MAX_LENGTH, description="Last name")

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        if "password" in values.data and confirm_password != values.data["password"]:
            raise ValueError("Password and confirm password must match")
        return confirm_password


class AuthChangePasswordModel(BaseModel):
    old_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH, description="Current password")
    new_password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="New password, at least 8 characters and max 32 characters",
    )
    confirm_password: str = Field(..., description="Must match new_password")

    @field_validator("confirm_password")
    def passwords_match(cls, confirm_password, values):
        if "new_password" in values.data and confirm_password != values.data["new_password"]:
            raise ValueError("New password and confirm password must match")
        return confirm_password


class AuthResetPasswordModel(AuthChangePasswordModel):
    pass


class AuthEditUserModel(BaseModel):
    username: str = Field(..., pattern=USERNAME_PATTERN, min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH, description="Username")
    email: EmailStr = Field(..., description="Valid email address is required")
    first_name: str = Field(..., min_length=FIRST_NAME_MIN_LENGTH, max_length=FIRST_NAME_MAX_LENGTH, description="First name")
    last_name: str = Field(..., min_length=LAST_NAME_MIN_LENGTH, max_length=LAST_NAME_MAX_LENGTH, description="Last name")


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
