from pydantic import ConfigDict, BaseModel, Field


class PossibilistCategoryModel(BaseModel):
    id: int
    name: str
    icon: str | None
    is_group: bool
    sort_order: int

    class Config:
        from_attributes = True


class PossibilistCategoryCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=500)
    is_group: bool = False
    sort_order: int = 0


class PossibilistCategoryUpdateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=500)
    is_group: bool | None = None
    sort_order: int | None = None


class ResponseModel(BaseModel):
    success: bool = True
