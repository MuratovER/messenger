from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import BaseModel
from db.models.mixins import IDMixin
from schemas.user import CreateUserSchema
from utils.utils import pwd_context


class User(BaseModel, IDMixin):
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    email: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(length=255), nullable=False)

    def __str__(self) -> str:
        return f"User #{self.name}"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    async def create_user_with_hashed_password(
        cls, create_data: CreateUserSchema
    ) -> "User":
        return cls(
            name=create_data.name,
            email=create_data.email,
            hashed_password=pwd_context.hash(create_data.password),
        )
