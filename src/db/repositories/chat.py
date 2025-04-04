from typing import Sequence

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from db.models.chat import Chat
from db.models.chat_participant import ChatsParticipant
from db.models.message import Message
from db.repositories.base import BaseDatabaseRepository
from schemas.chat import CreateChatSchema


class ChatRepository(BaseDatabaseRepository):
    async def get_chat_by_name(self, name: str) -> Chat | None:
        query = select(Chat).where(Chat.name == name).limit(1)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def create_chat(self, chat_data: CreateChatSchema) -> Chat:
        chat = Chat(**chat_data.model_dump(exclude={"participants"}))
        self._session.add(chat)
        await self._session.flush()

        await self._apply_participants_for_chat(
            chat_id=chat.id, participants_ids=chat_data.participants
        )

        return chat

    async def get_chat_by_id(self, chat_id: int) -> Chat | None:
        return await self._session.get(Chat, chat_id)

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

    async def _apply_participants_for_chat(
        self, chat_id: int, participants_ids: list[int]
    ) -> Sequence[ChatsParticipant]:
        result = []

        for participant_id in participants_ids:
            chat_participant = ChatsParticipant(
                chat_id=chat_id,
                participant_id=participant_id,  # type: ignore
            )
            self._session.add(chat_participant)
            result.append(chat_participant)

        await self._session.flush()
        return result
