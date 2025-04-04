from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from tests.factories.user import UserFactory
from tests.utils import generate_valide_password
from utils.utils import pwd_context


@pytest.mark.asyncio
async def test__refresh_token__success_case(
    async_db_session: AsyncSession,
    api_client: AsyncClient,
) -> None:
    password = await generate_valide_password()
    user = await UserFactory.create(
        session=async_db_session, hashed_password=pwd_context.hash(password)
    )

    login_response = await api_client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": password}
    )

    response = await api_client.post(
        f"/api/v1/auth/refresh?refresh_token={login_response.json()['refresh_token']}"
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test__refresh_token__incorrect_token(
    api_client: AsyncClient,
) -> None:
    response = await api_client.post(
        f"/api/v1/auth/refresh?refresh_token={str(uuid4())}"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
