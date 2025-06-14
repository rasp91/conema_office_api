from pydantic import BaseModel, EmailStr


class UserModel(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: EmailStr
