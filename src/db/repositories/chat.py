from typing import Sequence

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models.chat import Chat
from db.models.chat_participant import ChatParticipant
from db.models.message import Message
from db.repositories.base import BaseDatabaseRepository
from schemas.chat import CreateChatSchema


class ChatRepository(BaseDatabaseRepository):
    async def get_chat_by_name(self, name: str) -> Chat | None:
        query = select(Chat).where(Chat.name == name).limit(1)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def create_chat(self, name: str, creator_id: int) -> Chat:
        chat = Chat(name=name, creator_id=creator_id)
        self._session.add(chat)
        await self._session.flush()
        return chat

    async def get_chat_by_id(self, chat_id: int) -> Chat | None:
        query = (
            select(Chat)
            .options(selectinload(Chat.participants))
            .where(Chat.id == chat_id)
        )
        query_result = await self._session.execute(query)
        return query_result.scalar_one_or_none()

    async def create_message(self, chat_id: int, sender_id: int, text: str) -> Message:
        message = Message(chat_id=chat_id, sender_id=sender_id, text=text)  # type: ignore

        self._session.add(message)
        await self._session.flush()

        return message

    async def get_chat_history(self, chat_id: int, params: Params) -> Page[Message]:
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
        )
        return await paginate(self._session, query, params)

    async def message_was_read(self, message: Message):
        message.was_read = True
        await self._session.flush()

    async def get_message_by_id(self, message_id: int) -> Message | None:
        return await self._session.get(Message, message_id)

    async def get_user_chats(self, user_id: int) -> list[Chat]:
        query = (
            select(Chat)
            .options(selectinload(Chat.participants))
            .join(ChatParticipant)
            .where(ChatParticipant.user_id == user_id)
        )
        query_result = await self._session.execute(query)
        return list(query_result.scalars().all())

    async def add_participants_to_chat(
        self, chat_id: int, participants_ids: list[int]
    ) -> None:
        participants = [
            ChatParticipant(chat_id=chat_id, user_id=user_id)
            for user_id in participants_ids
        ]
        self._session.add_all(participants)
        await self._session.flush()

    async def is_user_participant(self, chat_id: int, user_id: int) -> bool:
        query = select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id,
        )
        query_result = await self._session.execute(query)
        return query_result.scalar_one_or_none() is not None
