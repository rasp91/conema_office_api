from pydantic import BaseModel


class TeamMemberModel(BaseModel):
    id: int
    first_name: str
    last_name: str
    position: str | None
    photo_path: str | None
    bio: str | None
    is_visible: bool

    class Config:
        from_attributes = True


class TeamMemberCreateModel(BaseModel):
    first_name: str
    last_name: str
    position: str | None = None
    photo_path: str | None = None
    bio: str | None = None
    is_visible: bool = True


class TeamMemberUpdateModel(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    photo_path: str | None = None
    bio: str | None = None
    is_visible: bool | None = None


class ResponseModel(BaseModel):
    success: bool = True
