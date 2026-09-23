from pydantic import ConfigDict, BaseModel, Field


class PresentationCategoryModel(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PresentationCategoryCreateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)


class PresentationCategoryUpdateModel(BaseModel):
    # " " must not pass min_length=1 and stray spaces shouldn't be stored
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)


class ResponseModel(BaseModel):
    success: bool = True
