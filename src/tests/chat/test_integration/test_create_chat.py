from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.models.chat import Chat
from schemas.chat import CreateChatSchema, GetChatSchema
from tests.factories.chat import ChatFactory
from tests.factories.user import UserFactory
from tests.utils import get_auth_headers
from utils.utils import pwd_context


@pytest.mark.asyncio
async def test__create_chat__success_case(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = str(uuid4())
    member = await UserFactory.create(session=async_db_session)
    creator = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    chat_data = CreateChatSchema(
        **ChatFactory.build().__dict__, participants=[member.id, creator.id]
    ).model_dump()

    headers = await get_auth_headers(
        email=creator.email, password=password, api_client=api_client
    )

    count_before = len((await async_db_session.execute(select(Chat))).scalars().all())

    response = await api_client.post("/api/v1/chats", json=chat_data, headers=headers)
    data = response.json()

    query_result = (
        await async_db_session.execute(select(Chat).where(Chat.id == data["id"]))
    ).scalar_one_or_none()
    count_after = len((await async_db_session.execute(select(Chat))).scalars().all())

    assert response.status_code == status.HTTP_201_CREATED
    assert GetChatSchema.model_validate(query_result).model_dump() == data
    assert count_before + 1 == count_after


@pytest.mark.asyncio
async def test__create_chat__existed_name_provided(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = str(uuid4())
    member = await UserFactory.create(session=async_db_session)
    creator = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    existing_chat = await ChatFactory.create(session=async_db_session)

    chat_data = CreateChatSchema(
        **existing_chat.__dict__, participants=[member.id, creator.id]
    ).model_dump()

    headers = await get_auth_headers(
        email=creator.email, password=password, api_client=api_client
    )

    count_before = len((await async_db_session.execute(select(Chat))).scalars().all())

    response = await api_client.post("/api/v1/chats", json=chat_data, headers=headers)

    count_after = len((await async_db_session.execute(select(Chat))).scalars().all())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert count_before == count_after


@pytest.mark.asyncio
async def test__create_chat__incorrect_participant_provided(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = str(uuid4())
    creator = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    existing_chat = await ChatFactory.create(session=async_db_session)

    chat_data = CreateChatSchema(
        **existing_chat.__dict__, participants=[-1, creator.id]
    ).model_dump()

    headers = await get_auth_headers(
        email=creator.email, password=password, api_client=api_client
    )

    count_before = len((await async_db_session.execute(select(Chat))).scalars().all())

    response = await api_client.post("/api/v1/chats", json=chat_data, headers=headers)

    count_after = len((await async_db_session.execute(select(Chat))).scalars().all())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert count_before == count_after
