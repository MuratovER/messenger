from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse

from db.models.user import User
from schemas.auth import LoginSchema, TokenSchema
from schemas.user import CreateUserSchema, GetUserSchema
from services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        401: {"description": "Unauthorized - Invalid credentials"},
        422: {"description": "Validation Error - Invalid request format"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    path="/refresh",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="""
    Обновляет access token используя refresh token.
    
    **Использование:**
    - Отправьте refresh token в теле запроса
    - Получите новую пару access/refresh токенов
    
    **Безопасность:**
    - Refresh token должен быть валидным и не истекшим
    - Старый refresh token становится недействительным
    """,
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            }
        },
        401: {
            "description": "Недействительный или истекший refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired refresh token"
                    }
                }
            }
        }
    }
)
async def refresh(
    refresh_token: str,
    auth_service: AuthService = Depends(),
) -> TokenSchema:
    """
    Обновляет access token используя refresh token.
    
    Args:
        refresh_token: Валидный refresh token
        auth_service: Сервис аутентификации
        
    Returns:
        TokenSchema: Новая пара токенов
        
    Raises:
        HTTPException: Если refresh token недействителен или истек
    """
    return await auth_service.refresh(token=refresh_token)


@router.post(
    "/login",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="""
    Аутентификация пользователя и получение токенов доступа.
    
    **Процесс аутентификации:**
    1. Проверка email и пароля
    2. Генерация JWT токенов
    3. Возврат access и refresh токенов
    
    **Требования:**
    - Email должен быть зарегистрирован
    - Пароль должен быть корректным
    """,
    responses={
        200: {
            "description": "Успешная аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            }
        },
        401: {
            "description": "Неверные учетные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        }
    }
)
async def login(
    form_data: LoginSchema, 
    auth_service: AuthService = Depends()
) -> TokenSchema:
    """
    Аутентификация пользователя.
    
    Args:
        form_data: Данные для входа (email, password)
        auth_service: Сервис аутентификации
        
    Returns:
        TokenSchema: Токены доступа
        
    Raises:
        HTTPException: Если учетные данные неверны
    """
    return await auth_service.login(data=form_data)


@router.post(
    path="/sign-up",
    response_model=GetUserSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="""
    Регистрация нового пользователя.
    
    **Процесс регистрации:**
    1. Валидация входных данных
    2. Проверка уникальности email
    3. Хеширование пароля
    4. Создание пользователя в базе данных
    
    **Требования к паролю:**
    - Минимум 8 символов
    - Содержит буквы и цифры
    - Не содержит специальных символов
    """,
    responses={
        201: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john.doe@example.com"
                    }
                }
            }
        },
        400: {
            "description": "Email уже существует или неверные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "invalid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def sign_up(
    user_data: CreateUserSchema,
    auth_service: AuthService = Depends(),
) -> GetUserSchema:
    """
    Регистрация нового пользователя.
    
    Args:
        user_data: Данные для регистрации (name, email, password)
        auth_service: Сервис аутентификации
        
    Returns:
        GetUserSchema: Данные созданного пользователя
        
    Raises:
        HTTPException: Если email уже существует или данные неверны
    """
    return await auth_service.sign_up(user_data=user_data)
