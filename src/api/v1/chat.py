from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi_pagination import Page, Params

from db.models.message import Message
from schemas.chat import CreateChatSchema, GetChatSchema
from schemas.message import GetMessageSchema
from services.auth import get_current_user
from services.chat import ChatService

router = APIRouter(
    prefix="/chats", 
    tags=["Chat Management"],
    responses={
        400: {"description": "Bad Request - Invalid input data"},
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Access denied"},
        404: {"description": "Not Found - Chat not found"},
        422: {"description": "Validation Error - Invalid request format"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    path="",
    response_model=GetChatSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Chat",
    description="""
    Создает новый чат с указанными участниками.
    
    **Процесс создания:**
    1. Валидация данных чата
    2. Проверка существования участников
    3. Создание чата в базе данных
    4. Добавление участников в чат
    
    **Требования:**
    - Текущий пользователь должен быть в списке участников
    - Все участники должны существовать в системе
    - Название чата не должно быть пустым
    """,
    responses={
        201: {
            "description": "Чат успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Team Chat",
                        "creator_id": 1,
                        "participants": [1, 2, 3]
                    }
                }
            }
        },
        400: {
            "description": "Неверные данные или участники не найдены",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Some participants not found"
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
async def create_chat(
    data: CreateChatSchema,
    current_user_id: Annotated[int, Depends(get_current_user)],
    chat_service: ChatService = Depends(),
) -> GetChatSchema:
    """
    Создает новый чат.
    
    Args:
        data: Данные для создания чата (name, participants)
        current_user_id: ID текущего пользователя
        chat_service: Сервис управления чатами
        
    Returns:
        GetChatSchema: Данные созданного чата
        
    Raises:
        HTTPException: Если данные неверны или участники не найдены
    """
    return await chat_service.create_chat(
        chat_data=data, current_user_id=current_user_id
    )


@router.get(
    path="/history/{chat_id}",
    response_model=Page[GetMessageSchema],
    status_code=status.HTTP_200_OK,
    summary="Get Chat History",
    description="""
    Получает историю сообщений для указанного чата с пагинацией.
    
    **Функциональность:**
    - Пагинированный список сообщений
    - Сортировка по времени создания (новые сверху)
    - Проверка доступа к чату
    
    **Параметры пагинации:**
    - page: Номер страницы (по умолчанию 1)
    - size: Размер страницы (по умолчанию 20)
    
    **Требования:**
    - Пользователь должен быть участником чата
    - Чат должен существовать
    """,
    responses={
        200: {
            "description": "История сообщений получена",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "chat_id": 1,
                                "sender_id": 1,
                                "text": "Hello everyone!",
                                "was_read": True,
                                "created_at": "2024-01-01T12:00:00Z"
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
        },
        403: {
            "description": "Нет доступа к чату",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied to this chat"
                    }
                }
            }
        },
        404: {
            "description": "Чат не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Chat not found"
                    }
                }
            }
        }
    }
)
async def get_chat_history(
    chat_id: int,
    current_user_id: Annotated[int, Depends(get_current_user)],
    chat_service: ChatService = Depends(),
    params: Params = Depends(),
) -> Page[Message]:
    """
    Получает историю сообщений чата.
    
    Args:
        chat_id: ID чата
        current_user_id: ID текущего пользователя
        chat_service: Сервис управления чатами
        params: Параметры пагинации
        
    Returns:
        Page[Message]: Пагинированный список сообщений
        
    Raises:
        HTTPException: Если чат не найден или нет доступа
    """
    return await chat_service.get_chat_history(chat_id=chat_id, params=params)
