from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params

from db.models.message import Message
from schemas.chat import CreateChatSchema, GetChatSchema
from schemas.message import GetMessageSchema
from services.auth import get_current_user
from services.chat import ChatService

router = APIRouter(prefix="/chats", tags=["Chat"])


@router.post(
    path="",
    response_model=GetChatSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new chat",
    description="Creates a new chat with participants and returns chat details",
)
async def create_chat(
    data: CreateChatSchema,
    current_user_id: Annotated[int, Depends(get_current_user)],
    chat_service: ChatService = Depends(),
) -> GetChatSchema:
    return await chat_service.create_chat(
        chat_data=data, current_user_id=current_user_id
    )


@router.get(
    path="/history/{chat_id}",
    response_model=Page[GetMessageSchema],
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
    description="Retrieve paginated message history for specified chat",
)
async def get_chat_history(
    chat_id: int,
    current_user_id: Annotated[int, Depends(get_current_user)],
    chat_service: ChatService = Depends(),
    params: Params = Depends(),
) -> Page[Message]:
    return await chat_service.get_chat_history(chat_id=chat_id, params=params)
