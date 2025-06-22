import random
import string

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from core.constants import MAX_PASS_LENGTH, MIN_PASS_LENGTH, SPECIAL_CHARS
from db.session import get_engine

# Тестовые константы для unit и интеграционных тестов
# Если число не вынесено в константы, то оно либо стандартное для библиотеки, либо его смысл очевиден из контекста (например, 0 или 1 для булевых флагов, или 2 для проверки нескольких объектов)

TEST_USER_EMAIL = "test@example.com"  # Используется для проверки email, заменяется фабрикой, если нужно уникальное значение
TEST_USER_USERNAME = "testuser"
TEST_USER_PASSWORD = "StrongPass123!"  # Соответствует требованиям валидатора
TEST_USER_WEAK_PASSWORD = "weak"  # Для проверки слабого пароля
TEST_USER_INVALID_EMAIL = "invalid-email"
TEST_USER_ID = 1
TEST_USER_ID_2 = 2

TEST_CHAT_NAME = "Test Chat"
TEST_CHAT_DESCRIPTION = "A test chat room"
TEST_CHAT_ID = 1
TEST_CHAT_ID_NOT_FOUND = 999
TEST_CHAT_NAME_TOO_LONG = "A" * 101  # 101 символ, чтобы проверить ограничение

TEST_MESSAGE_CONTENT = "Hello, world!"
TEST_MESSAGE_TYPE_TEXT = "text"
TEST_MESSAGE_TYPE_IMAGE = "image"
TEST_MESSAGE_TYPE_FILE = "file"

TEST_TOKEN = "test_token"
TEST_ACCESS_TOKEN = "test_access_token"
TEST_REFRESH_TOKEN = "test_refresh_token"

TEST_SKIP = 0
TEST_LIMIT = 10

# Для проверки производительности и массовых операций
TEST_MASS_CONNECTIONS = 100
TEST_MASS_BROADCAST = 50
TEST_MASS_MEMORY = 1000
TEST_PERFORMANCE_SEC = 1.0  # 1 секунда на массовое подключение
TEST_BROADCAST_SEC = 0.5  # 0.5 секунды на массовую рассылку
TEST_MEMORY_LIMIT_MB = 100

# Если в тесте используется число 0, 1, 2 — это обычно для проверки пустого результата, одного объекта или пары (например, для проверки уникальности, или что оба объекта обработаны)
# Если используется 5 — это для проверки нескольких повторов (например, 5 сообщений подряд)
# Если используется 30, 60, 300, 1800, 7200 — это стандартные значения TTL (секунды, минуты, часы)
# Если используется 129 — это для проверки ограничения длины пароля (128 символов + 1)
# Если используется 1000 — это нагрузочный тест (массовое подключение)

# Для генерации случайных данных используйте фабрики из tests/factories:
# from tests.factories.user import UserFactory
# user = UserFactory.build()
# from tests.factories.chat import ChatFactory
# chat = ChatFactory.build()
# from tests.factories.message import MessageFactory
# message = MessageFactory.build()

TEST_MESSAGE_ID = 1
TEST_CONNECTION_ID = "test-connection-id"
TEST_RATE_LIMIT = 60  # сообщений в минуту
TEST_TIMEOUT_SECONDS = 30
TEST_MAX_CONNECTIONS_PER_USER = 3
TEST_MAX_MESSAGE_LENGTH = 1000
TEST_PING_INTERVAL = 10
TEST_PONG_TIMEOUT = 20

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
