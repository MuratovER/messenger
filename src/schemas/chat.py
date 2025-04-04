from core.enums import ChatTypeEnum
from schemas.base import BaseOrmSchema


class BaseChatSchema(BaseOrmSchema):
    name: str
    chat_type: ChatTypeEnum


class CreateChatSchema(BaseChatSchema):
    participants: list[int]


class GetChatSchema(BaseChatSchema):
    id: int
