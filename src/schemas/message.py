from datetime import datetime

from schemas.base import BaseOrmSchema


class CreateMessageSchema(BaseOrmSchema):
    chat_id: int
    sender_id: int
    text: str
    was_read: bool


class GetMessageSchema(CreateMessageSchema):
    id: int
    created_at: datetime
