from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from services.chat import ChatService
from ws.connection import WebSocketConnectionManager

router = APIRouter(
    tags=["Real-time Messaging"],
    responses={
        400: {"description": "Bad Request - Invalid parameters"},
        401: {"description": "Unauthorized - Invalid token"},
        403: {"description": "Forbidden - Access denied to chat"},
        404: {"description": "Not Found - Chat not found"},
        500: {"description": "Internal Server Error"}
    }
)


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: int,
    token: str,
    websocket_manager: WebSocketConnectionManager = Depends(),
    chat_service: ChatService = Depends(),
):
    """
    WebSocket соединение для реального времени обмена сообщениями.
    
    **Процесс подключения:**
    1. Валидация JWT токена
    2. Проверка доступа к чату
    3. Установка WebSocket соединения
    4. Подписка на события чата
    
    **Функциональность:**
    - Отправка сообщений в реальном времени
    - Получение уведомлений о новых сообщениях
    - Индикация статуса "печатает"
    - Уведомления о прочтении сообщений
    
    **Параметры подключения:**
    - chat_id: ID чата для подключения
    - token: JWT токен для аутентификации (query parameter)
    
    **Формат сообщений:**
    ```json
    {
        "type": "message",
        "text": "Hello world!",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    
    **Типы событий:**
    - message: Новое сообщение
    - typing: Пользователь печатает
    - read: Сообщение прочитано
    - join: Пользователь присоединился
    - leave: Пользователь покинул чат
    
    **Коды закрытия соединения:**
    - 1000: Нормальное закрытие
    - 1008: Недействительный токен
    - 1003: Нет доступа к чату
    - 1006: Неожиданное закрытие
    """
    try:
        # Валидация пользователя по токену
        user_id = await websocket_manager.validate_user(token=token)
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Проверка доступа к чату
        try:
            await chat_service.get_chat_by_id(chat_id=chat_id)
        except Exception:
            await websocket.close(code=1003, reason="Access denied to chat")
            return
        
        # Установка соединения и обработка сообщений
        await websocket_manager.run(
            websocket=websocket, 
            chat_id=chat_id, 
            user_id=user_id
        )
        
    except WebSocketDisconnect:
        # Обработка нормального отключения
        pass
    except Exception as e:
        # Обработка ошибок
        await websocket.close(code=1011, reason=f"Internal error: {str(e)}")
