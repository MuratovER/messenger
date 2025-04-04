import random
import string

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from core.constants import MAX_PASS_LENGTH, MIN_PASS_LENGTH, SPECIAL_CHARS
from db.session import get_engine


async def create_database(url: str) -> None:
    url_object = make_url(url)
    database = url_object.database
    url_object = url_object.set(database="postgres")

    engine = get_engine(url=url_object, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE DATABASE "{database}" ENCODING "utf8"'))

    await engine.dispose()


async def database_exists(url: str) -> bool:
    url_object = make_url(url)
    database = url_object.database
    url_object = url_object.set(database="postgres")

    engine = None
    try:
        engine = get_engine(url=url_object, isolation_level="AUTOCOMMIT")
        async with engine.begin() as conn:
            try:
                datname_exists = await conn.scalar(
                    text(f"SELECT 1 FROM pg_database WHERE datname='{database}'")
                )

            except (ProgrammingError, OperationalError):
                datname_exists = 0

        return bool(datname_exists)

    finally:
        if engine:
            await engine.dispose()


async def drop_database(url: str) -> None:
    url_object = make_url(url)
    database = url_object.database
    url_object = url_object.set(database="postgres")

    engine = get_engine(url=url_object, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        disc_users = f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{database}' AND pid <> pg_backend_pid();
        """
        await conn.execute(text(disc_users))

        await conn.execute(text(f'DROP DATABASE "{database}"'))

    await engine.dispose()


async def generate_valide_password(
    digits: bool = True, upper: bool = True, lower: bool = True, special: bool = True
) -> str:
    length = random.randint(MIN_PASS_LENGTH, MAX_PASS_LENGTH)

    requirements = []

    if digits:
        requirements.append(
            (string.digits, 1),
        )

    if upper:
        requirements.append((string.ascii_uppercase, 1))

    if lower:
        requirements.append((string.ascii_lowercase, 1))

    if special:
        requirements.append((SPECIAL_CHARS, 1))  # type: ignore

    password_parts = []
    for chars, count in requirements:
        password_parts.extend(random.choices(chars, k=count))

    remaining = length - len(password_parts)
    if remaining > 0:
        all_chars = string.ascii_letters + string.digits + "".join(SPECIAL_CHARS)
        password_parts.extend(random.choices(all_chars, k=remaining))

    random.shuffle(password_parts)
    return "".join(password_parts)


async def get_auth_headers(
    email: str, password: str, api_client: AsyncClient
) -> dict[str, str]:
    login_response = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == status.HTTP_200_OK

    response_data = login_response.json()
    return {"Authorization": f"Bearer {response_data['access_token']}"}
