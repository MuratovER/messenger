from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from core.enums import ChatTypeEnum
from db.models.base import BaseModel
from db.models.mixins import IDMixin


class Chat(BaseModel, IDMixin):
    name: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    chat_type: Mapped[ChatTypeEnum] = mapped_column(
        Enum(ChatTypeEnum), nullable=False, default=ChatTypeEnum.private
    )

    def __str__(self) -> str:
        return f"Chat #{self.name}"
