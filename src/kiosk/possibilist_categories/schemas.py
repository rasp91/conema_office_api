from pydantic import BaseModel


class PossibilistCategoryModel(BaseModel):
    id: int
    name: str
    icon: str | None
    is_group: bool
    sort_order: int

    class Config:
        from_attributes = True


class PossibilistCategoryCreateModel(BaseModel):
    name: str
    icon: str | None = None
    is_group: bool = False
    sort_order: int = 0


class PossibilistCategoryUpdateModel(BaseModel):
    name: str | None = None
    icon: str | None = None
    is_group: bool | None = None
    sort_order: int | None = None


class ResponseModel(BaseModel):
    success: bool = True
