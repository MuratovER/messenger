from fastapi import APIRouter, Depends, WebSocket

from services.chat import ChatService
from ws.connection import ConnectionManager

router = APIRouter(tags=["Messages"])


@router.websocket("/ws/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: int,
    token: str,
    websocket_manager: ConnectionManager = Depends(),
    chat_service: ChatService = Depends(),
):
    user_id = await websocket_manager.validate_user(token=token)

    if not user_id:
        await websocket.close(code=1008)
        return

    await chat_service.get_chat_by_id(chat_id=chat_id)
    await websocket_manager.run(websocket=websocket, chat_id=chat_id, user_id=user_id)
