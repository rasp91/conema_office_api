from pydantic import ConfigDict, BaseModel, Field


class TeamMemberModel(BaseModel):
    id: int
    first_name: str
    last_name: str
    position: str | None
    photo_path: str | None
    bio: str | None
    is_visible: bool
    views: int = 0

    class Config:
        from_attributes = True


class TeamMemberCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    position: str | None = Field(default=None, max_length=255)
    photo_path: str | None = Field(default=None, max_length=500)
    bio: str | None = None
    is_visible: bool = True


class TeamMemberUpdateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, max_length=255)
    photo_path: str | None = Field(default=None, max_length=500)
    bio: str | None = None
    is_visible: bool | None = None


class ResponseModel(BaseModel):
    success: bool = True
