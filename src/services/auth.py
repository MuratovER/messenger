from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import APIKeyHeader
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import (
    ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN,
    JWT_ALGORITHM,
    REFRES_TOKEN_EXPIRATION_TIME_IN_MIN,
)
from core.exceptions import (
    incorrect_credentials_exception,
    incorrect_token_provided_exception,
    user_uniquness_exception,
)
from db.models.user import User
from db.repositories.user import UserRepository
from db.session import get_session
from schemas.auth import LoginSchema, TokenSchema
from schemas.user import CreateUserSchema
from utils.utils import pwd_context

header_scheme = APIKeyHeader(name="Authorization")


async def get_current_user(
    token: Annotated[str, Depends(header_scheme)],
):
    try:
        data = jwt.decode(
            token.split(" ")[-1], settings().SECRET, algorithms=[JWT_ALGORITHM]
        )

        user_id = data.get("user_id")
        if not user_id:
            raise incorrect_token_provided_exception

        return user_id

    except (InvalidSignatureError, DecodeError, ExpiredSignatureError):
        raise incorrect_token_provided_exception


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        session: AsyncSession = Depends(get_session),
    ) -> None:
        self._user_repository = user_repository
        self._session = session

    async def login(self, data: LoginSchema) -> TokenSchema:
        user = await self._user_repository.get_user_by_email(email=data.email)

        if not user:
            raise incorrect_credentials_exception

        if not pwd_context.verify(data.password, user.hashed_password):
            raise incorrect_credentials_exception

        return await self.generate_tokens(user_id=user.id)

    async def refresh(self, token: str) -> TokenSchema:
        try:
            data = jwt.decode(token, settings().SECRET, algorithms=[JWT_ALGORITHM])

            user_id = data.get("user_id")
            if not user_id:
                raise incorrect_token_provided_exception

            return await self.generate_tokens(user_id=user_id)

        except (InvalidSignatureError, DecodeError, ExpiredSignatureError):
            raise incorrect_token_provided_exception

    async def sign_up(self, user_data: CreateUserSchema) -> User:
        if await self._user_repository.get_user_by_email(email=user_data.email):
            raise user_uniquness_exception

        user = await self._user_repository.create_user(user_data=user_data)
        await self._session.commit()

        return user

    @staticmethod
    async def generate_tokens(user_id: int) -> TokenSchema:
        access_payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN),
        }
        refresh_payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=REFRES_TOKEN_EXPIRATION_TIME_IN_MIN),
        }
        access_token = jwt.encode(
            access_payload, settings().SECRET, algorithm=JWT_ALGORITHM
        )
        refresh_token = jwt.encode(
            refresh_payload, settings().SECRET, algorithm=JWT_ALGORITHM
        )

        return TokenSchema(access_token=access_token, refresh_token=refresh_token)
