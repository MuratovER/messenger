from fastapi import APIRouter, Depends, status

from db.models.user import User
from schemas.auth import LoginSchema, TokenSchema
from schemas.user import CreateUserSchema, GetUserSchema
from services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    path="/refresh",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Obtain new access token using refresh token",
)
async def refresh(
    refresh_token: str,
    auth_service: AuthService = Depends(),
) -> TokenSchema:
    return await auth_service.refresh(token=refresh_token)


@router.post(
    "/login",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and get access/refresh tokens",
)
async def login(
    form_data: LoginSchema, auth_service: AuthService = Depends()
) -> TokenSchema:
    return await auth_service.login(data=form_data)


@router.post(
    path="/sign-up",
    response_model=GetUserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create new user account",
)
async def sign_up(
    user_data: CreateUserSchema,
    auth_service: AuthService = Depends(),
) -> User:
    return await auth_service.sign_up(user_data=user_data)
