from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import BaseModel
from db.models.mixins import CreatedAtMixin, IDMixin


class Message(BaseModel, CreatedAtMixin, IDMixin):
    chat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )

    sender_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(length=255), nullable=False)
    was_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __str__(self) -> str:
        return (
            f"Message #{self.id} from user #{self.sender_id} for chat #{self.chat_id}"
        )
