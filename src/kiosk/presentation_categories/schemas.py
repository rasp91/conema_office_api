from pydantic import BaseModel


class PresentationCategoryModel(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PresentationCategoryCreateModel(BaseModel):
    name: str


class PresentationCategoryUpdateModel(BaseModel):
    name: str | None = None


class ResponseModel(BaseModel):
    success: bool = True
