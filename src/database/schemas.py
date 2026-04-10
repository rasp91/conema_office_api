from pydantic import computed_field, BaseModel, EmailStr


class UserModel(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: EmailStr | None

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{str(self.first_name).strip()} {str(self.last_name).strip()}".replace("  ", " ").strip()
