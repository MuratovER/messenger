from fastapi import Depends
from fastapi_pagination import Page, Params
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import (
    chat_not_found_exception,
    chat_uniquness_exception,
    message_not_found_exception,
    user_not_found_exception,
    user_not_participant_exception,
)
from db.models.chat import Chat
from db.models.message import Message
from db.models.user import User
from db.repositories.chat import ChatRepository
from db.repositories.user import UserRepository
from db.session import get_session
from schemas.chat import CreateChatSchema, GetChatSchema


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository = Depends(),
        user_repository: UserRepository = Depends(),
        session: AsyncSession = Depends(get_session),
    ) -> None:
        self._chat_repository = chat_repository
        self._session = session
        self._user_repository = user_repository

    async def create_message(self, chat_id: int, sender_id: int, text: str) -> Message:
        await self.get_chat_by_id(chat_id=chat_id)
        await self._get_user_by_id(user_id=sender_id)

        message = await self._chat_repository.create_message(
            chat_id=chat_id, sender_id=sender_id, text=text
        )
        await self._session.commit()

        return message

    async def get_chat_by_name(self, name: str) -> Chat:
        chat = await self._chat_repository.get_chat_by_name(name=name)
        if not chat:
            raise chat_not_found_exception

        return chat

    async def get_chat_history(self, chat_id: int, params: Params) -> Page[Message]:
        await self.get_chat_by_id(chat_id=chat_id)
        return await self._chat_repository.get_chat_history(
            chat_id=chat_id, params=params
        )

    async def create_chat(
        self, chat_data: CreateChatSchema, current_user_id: int
    ) -> GetChatSchema:
        if await self._chat_repository.get_chat_by_name(name=chat_data.name):
            raise chat_uniquness_exception

        for participant in chat_data.participants:
            await self._get_user_by_id(user_id=participant)

        if current_user_id not in chat_data.participants:
            raise user_not_participant_exception

        chat = await self._chat_repository.create_chat(chat_data=chat_data)
        await self._session.commit()

        return GetChatSchema(**chat_data.model_dump(), id=chat.id)

    async def get_chat_by_id(self, chat_id: int) -> Chat:
        chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        if not chat:
            raise chat_not_found_exception

        return chat

    async def get_message_by_id(self, message_id: int) -> Message:
        message = await self._chat_repository.get_message_by_id(message_id=message_id)

        if not message:
            raise message_not_found_exception

        return message

    async def message_was_read(self, message_id: int) -> Message:
        message = await self.get_message_by_id(message_id=message_id)

        await self._chat_repository.message_was_read(message=message)
        await self._session.commit()

        return message

    async def _get_user_by_id(self, user_id: int) -> User:
        user = await self._user_repository.get_user_by_id(user_id=user_id)

        if not user:
            raise user_not_found_exception

        return user
