import pytest
from httpx import AsyncClient
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.models.user import User
from schemas.user import CreateUserSchema, GetUserSchema
from tests.factories.user import BaseUserFactory, UserFactory
from tests.utils import generate_valide_password


@pytest.mark.asyncio
async def test__create_user__success_case(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    creator = BaseUserFactory.build()

    data = CreateUserSchema(**creator.__dict__, password=password).model_dump()

    count_before = len((await async_db_session.execute(select(User))).scalars().all())

    response = await api_client.post("/api/v1/auth/sign-up", json=data)
    data = response.json()

    logger.info(response.text)

    query_result = (
        await async_db_session.execute(select(User).where(User.id == data["id"]))
    ).scalar_one_or_none()
    count_after = len((await async_db_session.execute(select(User))).scalars().all())

    assert response.status_code == status.HTTP_201_CREATED
    assert GetUserSchema.model_validate(query_result).model_dump() == data
    assert count_before + 1 == count_after


@pytest.mark.asyncio
async def test__create_user__existed_email_provided(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    creator = await UserFactory.create(session=async_db_session)

    data = CreateUserSchema(**creator.__dict__, password=password).model_dump()

    count_before = len((await async_db_session.execute(select(User))).scalars().all())

    response = await api_client.post("/api/v1/auth/sign-up", json=data)
    count_after = len((await async_db_session.execute(select(User))).scalars().all())

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert count_before == count_after
