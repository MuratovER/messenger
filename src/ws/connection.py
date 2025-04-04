import asyncio
from collections import defaultdict
from uuid import uuid4

import jwt
import orjson
from fastapi import Depends, WebSocket, WebSocketDisconnect
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from loguru import logger

from core.config import settings
from core.constants import JWT_ALGORITHM
from db.models.message import Message
from schemas.message import GetMessageSchema
from services.chat import ChatService


class ConnectionManager:
    _active_connections: dict[int, list[tuple[WebSocket, int, str]]] = defaultdict(list)

    def __init__(
        self,
        chat_service: ChatService = Depends(),
    ):
        logger.info("[INIT] ConnectionManager initialized.")
        self._chat_service = chat_service
        self.locks: dict[int, asyncio.Lock] = {}

    async def _get_lock(self, chat_id: int) -> asyncio.Lock:
        if chat_id not in self.locks:
            self.locks[chat_id] = asyncio.Lock()
        return self.locks[chat_id]

    async def connect(self, websocket: WebSocket, chat_id: int, client_id: int) -> str:
        logger.info(
            f"[CONNECT] New connection attempt: chat_id={chat_id}, client_id={client_id}"
        )
        await websocket.accept()
        connection_id = str(uuid4())

        async with await self._get_lock(chat_id):
            connections = self._active_connections.setdefault(chat_id, [])

            for ws, cid, _ in connections:
                if cid == client_id:
                    logger.warning(
                        f"[CONNECT] Duplicate connection detected for client_id={client_id}, closing previous one."
                    )
                    await ws.close(code=1008, reason="Duplicate connection")
                    raise ValueError("User already connected")

            connections.append((websocket, client_id, connection_id))
            logger.info(
                f"[CONNECT] Connection established: chat_id={chat_id}, client_id={client_id}, connection_id={connection_id}"
            )

        return connection_id

    async def disconnect(self, connection_id: str, chat_id: int, client_id: int):
        logger.info(
            f"[DISCONNECT] Client {client_id} disconnecting from chat {chat_id}, connection_id={connection_id}"
        )
        async with await self._get_lock(chat_id):
            connections = self._active_connections.get(chat_id, [])
            self._active_connections[chat_id] = [
                (ws, cid, conn_id)
                for ws, cid, conn_id in connections
                if conn_id != connection_id
            ]
            if not self._active_connections[chat_id]:
                self._active_connections.pop(chat_id, None)
                self.locks.pop(chat_id, None)
                logger.info(
                    f"[DISCONNECT] All clients disconnected from chat {chat_id}, cleaning up resources."
                )
            logger.info(
                f"[DISCONNECT] Client {client_id} successfully disconnected from chat {chat_id}."
            )

    async def run(self, websocket: WebSocket, chat_id: int, user_id: int):
        connection_id = await self.connect(websocket, chat_id, user_id)
        try:
            while True:
                data = await websocket.receive_text()
                message_data = orjson.loads(data)
                logger.info(
                    f"[RECEIVE] Received data: {message_data} from user {user_id}"
                )

                if message_data.get("type") == "new_message":
                    message = await self._chat_service.create_message(
                        chat_id=chat_id,
                        sender_id=user_id,
                        text=message_data.get("data", ""),
                    )
                    logger.info(
                        f"[MESSAGE] New message created in chat {chat_id} by user {user_id}: {message.text}"
                    )
                    asyncio.create_task(self.broadcast(message, user_id, chat_id))

                elif message_data.get("type") == "mark_as_read":
                    if "message_id" not in message_data:
                        logger.warning(
                            "[WARNING] Missing message_id in mark_as_read event"
                        )
                        continue
                    asyncio.create_task(
                        self._handle_read_receipt(int(message_data["message_id"]))
                    )
        except WebSocketDisconnect:
            logger.warning(
                f"[DISCONNECT] WebSocket disconnect detected for user {user_id} in chat {chat_id}"
            )
            await self.disconnect(connection_id, chat_id, user_id)
        except Exception as e:
            logger.error(
                f"[ERROR] WebSocket error for user {user_id} in chat {chat_id}: {e}"
            )
            await websocket.close(code=1011)

    async def _handle_read_receipt(self, message_id: int):
        message = await self._chat_service.get_message_by_id(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found")
            return
        asyncio.create_task(
            self._notify_sender(message.id, message.sender_id, message.chat_id)
        )

    async def _notify_sender(self, message_id: int, sender_id: int, chat_id: int):
        connections = self._active_connections.get(chat_id, [])
        async with await self._get_lock(chat_id):
            for websocket, client_id, _ in connections:
                if client_id == sender_id:
                    try:
                        await websocket.send_text(
                            orjson.dumps(
                                {
                                    "type": "message_read",
                                    "message_id": message_id,
                                    "chat_id": chat_id,
                                }
                            ).decode()
                        )
                        logger.info(
                            f"Sent read receipt for message {message_id} to sender {sender_id}"
                        )
                    except Exception as e:
                        logger.error(f"Error notifying sender {sender_id}: {e}")

    async def broadcast(self, message: Message, sender_id: int, chat_id: int):
        logger.info(
            f"[BROADCAST] Sending message {message.id} from sender {sender_id} to chat {chat_id}"
        )
        connections = self._active_connections.get(chat_id, [])
        if not connections:
            logger.warning(
                f"[BROADCAST] No active connections in chat {chat_id}, message not sent."
            )
            return

        dead_connections = []
        async with await self._get_lock(chat_id):
            for websocket, client_id, connection_id in connections:
                if client_id == sender_id:
                    continue
                try:
                    await websocket.send_text(
                        orjson.dumps(
                            {
                                "type": "new_message",
                                "data": GetMessageSchema.model_validate(
                                    message
                                ).model_dump_json(),
                            }
                        ).decode()
                    )
                    logger.info(
                        f"[BROADCAST] Message {message.id} sent to client {client_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"[ERROR] Failed to send message {message.id} to client {client_id}: {e}"
                    )
                    dead_connections.append((connection_id, chat_id, client_id))

        for conn_id, c_id, cl_id in dead_connections:
            await self.disconnect(conn_id, c_id, cl_id)

    @staticmethod
    async def validate_user(token: str):
        try:
            data = jwt.decode(
                token.split(" ")[-1], settings().SECRET, algorithms=[JWT_ALGORITHM]
            )
            user_id = data.get("user_id")
            logger.info(f"[AUTH] User validation successful: user_id={user_id}")
            return user_id
        except (InvalidSignatureError, DecodeError, ExpiredSignatureError) as e:
            logger.warning(f"[AUTH] Token validation failed: {e}")
            return None
