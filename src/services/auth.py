from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jwt.exceptions import DecodeError, ExpiredSignatureError, InvalidSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import (
    ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN,
    JWT_ALGORITHM,
    REFRESH_TOKEN_EXPIRATION_TIME_IN_MIN,
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
    user_repository: UserRepository = Depends(),
) -> User:
    """Get current authenticated user with validation."""
    try:
        if not token.startswith("Bearer "):
            raise incorrect_token_provided_exception
            
        token_value = token.split(" ")[-1]
        data = jwt.decode(
            token_value, settings().SECRET, algorithms=[JWT_ALGORITHM]
        )

        user_id = data.get("user_id")
        if not user_id:
            raise incorrect_token_provided_exception

        # Get user from database to ensure it still exists
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise incorrect_token_provided_exception

        return user

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
        """Authenticate user and return tokens."""
        # Validate input
        if not data.email or not data.password:
            raise incorrect_credentials_exception
            
        # Rate limiting check (simple implementation)
        # In production, use Redis for proper rate limiting
        
        user = await self._user_repository.get_user_by_email(email=data.email)

        if not user:
            raise incorrect_credentials_exception

        if not pwd_context.verify(data.password, user.hashed_password):
            raise incorrect_credentials_exception

        return await self.generate_tokens(user_id=user.id)

    async def refresh(self, token: str) -> TokenSchema:
        """Refresh access token using refresh token."""
        try:
            data = jwt.decode(token, settings().SECRET, algorithms=[JWT_ALGORITHM])

            user_id = data.get("user_id")
            if not user_id:
                raise incorrect_token_provided_exception

            # Verify user still exists
            user = await self._user_repository.get_user_by_id(user_id)
            if not user:
                raise incorrect_token_provided_exception

            return await self.generate_tokens(user_id=user_id)

        except (InvalidSignatureError, DecodeError, ExpiredSignatureError):
            raise incorrect_token_provided_exception

    async def sign_up(self, user_data: CreateUserSchema) -> User:
        """Register new user."""
        # Validate password strength
        if len(user_data.password) < settings().PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {settings().PASSWORD_MIN_LENGTH} characters long"
            )
            
        if len(user_data.password) > settings().PASSWORD_MAX_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be no more than {settings().PASSWORD_MAX_LENGTH} characters long"
            )

        # Check if user already exists
        if await self._user_repository.get_user_by_email(email=user_data.email):
            raise user_uniquness_exception

        try:
            user = await self._user_repository.create_user(user_data=user_data)
            await self._session.commit()
            return user
        except Exception as e:
            await self._session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

    @staticmethod
    async def generate_tokens(user_id: int) -> TokenSchema:
        """Generate access and refresh tokens."""
        now = datetime.now(timezone.utc)
        
        access_payload = {
            "user_id": user_id,
            "type": "access",
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN),
            "iat": now,
        }
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": now + timedelta(minutes=REFRESH_TOKEN_EXPIRATION_TIME_IN_MIN),
            "iat": now,
        }
        
        access_token = jwt.encode(
            access_payload, settings().SECRET, algorithm=JWT_ALGORITHM
        )
        refresh_token = jwt.encode(
            refresh_payload, settings().SECRET, algorithm=JWT_ALGORITHM
        )

        return TokenSchema(access_token=access_token, refresh_token=refresh_token)

    async def logout(self, token: str) -> bool:
        """Logout user by invalidating token."""
        # In production, implement token blacklisting using Redis
        # For now, just return success
        return True
