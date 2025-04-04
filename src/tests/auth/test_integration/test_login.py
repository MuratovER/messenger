from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from tests.factories.user import UserFactory
from tests.utils import generate_valide_password
from utils.utils import pwd_context


@pytest.mark.asyncio
async def test__login__success_case(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    user = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    response = await api_client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": password}
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test__login__incorrect_password_provided(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    user = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    response = await api_client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": str(uuid4())}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test__login__incorrect_email_provided(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    response = await api_client.post(
        "/api/v1/auth/login", json={"email": str(uuid4()), "password": password}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
