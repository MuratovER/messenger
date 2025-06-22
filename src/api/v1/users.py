from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi_pagination import Page, Params

from db.models.user import User
from schemas.user import GetUserSchema, UpdateUserSchema
from services.auth import get_current_user
from services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Access denied"},
        404: {"description": "Not Found - User not found"},
        422: {"description": "Validation Error - Invalid request format"},
        500: {"description": "Internal Server Error"}
    }
)


@router.get(
    path="/me",
    response_model=GetUserSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="""
    Получение профиля текущего аутентифицированного пользователя.
    
    **Возвращаемые данные:**
    - ID пользователя
    - Имя пользователя
    - Email адрес
    - Дата регистрации
    
    **Использование:**
    - Отображение профиля пользователя
    - Проверка аутентификации
    - Получение данных для форм
    """,
    responses={
        200: {
            "description": "Профиль пользователя получен",
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
        401: {
            "description": "Требуется аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        }
    }
)
async def get_current_user_profile(
    current_user_id: Annotated[int, Depends(get_current_user)],
    user_service: UserService = Depends(),
) -> GetUserSchema:
    """
    Получение профиля текущего пользователя.
    
    Args:
        current_user_id: ID текущего пользователя
        user_service: Сервис управления пользователями
        
    Returns:
        GetUserSchema: Данные профиля пользователя
        
    Raises:
        HTTPException: Если пользователь не найден
    """
    return await user_service.get_user_by_id(user_id=current_user_id)


@router.put(
    path="/me",
    response_model=GetUserSchema,
    status_code=status.HTTP_200_OK,
    summary="Update Current User Profile",
    description="""
    Обновление профиля текущего пользователя.
    
    **Обновляемые поля:**
    - Имя пользователя
    - Email адрес (с проверкой уникальности)
    
    **Валидация:**
    - Email должен быть уникальным
    - Имя не должно быть пустым
    - Формат email должен быть корректным
    
    **Безопасность:**
    - Пользователь может обновлять только свой профиль
    - Пароль обновляется отдельным эндпоинтом
    """,
    responses={
        200: {
            "description": "Профиль успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "John Smith",
                        "email": "john.smith@example.com"
                    }
                }
            }
        },
        400: {
            "description": "Email уже существует или неверные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already exists"
                    }
                }
            }
        },
        401: {
            "description": "Требуется аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        }
    }
)
async def update_current_user_profile(
    user_data: UpdateUserSchema,
    current_user_id: Annotated[int, Depends(get_current_user)],
    user_service: UserService = Depends(),
) -> GetUserSchema:
    """
    Обновление профиля текущего пользователя.
    
    Args:
        user_data: Данные для обновления
        current_user_id: ID текущего пользователя
        user_service: Сервис управления пользователями
        
    Returns:
        GetUserSchema: Обновленные данные профиля
        
    Raises:
        HTTPException: Если данные неверны или email уже существует
    """
    return await user_service.update_user(
        user_id=current_user_id, 
        user_data=user_data
    )


@router.get(
    path="/search",
    response_model=Page[GetUserSchema],
    status_code=status.HTTP_200_OK,
    summary="Search Users",
    description="""
    Поиск пользователей по имени или email.
    
    **Функциональность:**
    - Поиск по частичному совпадению имени
    - Поиск по частичному совпадению email
    - Пагинированные результаты
    - Сортировка по имени
    
    **Параметры поиска:**
    - q: Поисковый запрос (имя или email)
    - page: Номер страницы
    - size: Размер страницы
    
    **Использование:**
    - Поиск пользователей для добавления в чат
    - Автодополнение в формах
    - Справочник пользователей
    """,
    responses={
        200: {
            "description": "Результаты поиска получены",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "name": "John Doe",
                                "email": "john.doe@example.com"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "size": 20,
                        "pages": 1
                    }
                }
            }
        },
        401: {
            "description": "Требуется аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        }
    }
)
async def search_users(
    q: str,
    current_user_id: Annotated[int, Depends(get_current_user)],
    user_service: UserService = Depends(),
    params: Params = Depends(),
) -> Page[User]:
    """
    Поиск пользователей.
    
    Args:
        q: Поисковый запрос
        current_user_id: ID текущего пользователя
        user_service: Сервис управления пользователями
        params: Параметры пагинации
        
    Returns:
        Page[User]: Пагинированные результаты поиска
        
    Raises:
        HTTPException: Если поисковый запрос пустой
    """
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    return await user_service.search_users(
        query=q, 
        current_user_id=current_user_id, 
        params=params
    )


@router.get(
    path="/{user_id}",
    response_model=GetUserSchema,
    status_code=status.HTTP_200_OK,
    summary="Get User by ID",
    description="""
    Получение информации о пользователе по ID.
    
    **Возвращаемые данные:**
    - Основная информация о пользователе
    - Статус активности
    - Дата регистрации
    
    **Ограничения:**
    - Возвращается только публичная информация
    - Пароль и служебные данные не включаются
    
    **Использование:**
    - Просмотр профилей других пользователей
    - Проверка существования пользователя
    - Получение данных для чатов
    """,
    responses={
        200: {
            "description": "Информация о пользователе получена",
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
        401: {
            "description": "Требуется аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        404: {
            "description": "Пользователь не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found"
                    }
                }
            }
        }
    }
)
async def get_user_by_id(
    user_id: int,
    current_user_id: Annotated[int, Depends(get_current_user)],
    user_service: UserService = Depends(),
) -> GetUserSchema:
    """
    Получение информации о пользователе по ID.
    
    Args:
        user_id: ID пользователя
        current_user_id: ID текущего пользователя
        user_service: Сервис управления пользователями
        
    Returns:
        GetUserSchema: Данные пользователя
        
    Raises:
        HTTPException: Если пользователь не найден
    """
    return await user_service.get_user_by_id(user_id=user_id) 