from pydantic import BaseModel
from core.enums import ChatTypeEnum
from schemas.base import BaseOrmSchema


class BaseChatSchema(BaseOrmSchema):
    name: str
    chat_type: ChatTypeEnum


class CreateChatSchema(BaseModel):
    name: str
    participants: list[int]


class GetChatSchema(BaseModel):
    id: int
    name: str
    creator_id: int
    participants: list[int]

    class Config:
        from_attributes = True
