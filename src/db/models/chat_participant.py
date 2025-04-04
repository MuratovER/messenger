from sqlalchemy import Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import BaseModel


class ChatsParticipant(BaseModel):
    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    __table_args__ = (PrimaryKeyConstraint("chat_id", "participant_id"),)

    def __str__(self) -> str:
        return f"Chat #{self.chat_id} | Participant #{self.participant_id}"
