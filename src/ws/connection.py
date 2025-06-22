import asyncio
import time
from collections import defaultdict
from uuid import uuid4

import jwt
import orjson
from fastapi import Depends, WebSocket, WebSocketDisconnect
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from loguru import logger

from core.config import settings
from core.constants import (
    JWT_ALGORITHM,
    MAX_CONNECTIONS_PER_USER,
    MAX_MESSAGES_PER_MINUTE,
    WEBSOCKET_PING_INTERVAL,
    WEBSOCKET_PING_TIMEOUT,
)
from db.models.message import Message
from schemas.message import GetMessageSchema
from services.chat import ChatService


class RateLimiter:
    """Simple in-memory rate limiter for WebSocket connections."""
    
    def __init__(self):
        self.message_counts: dict[int, list[float]] = defaultdict(list)
        self.connection_counts: dict[int, int] = defaultdict(int)
    
    def can_send_message(self, user_id: int) -> bool:
        """Check if user can send a message (rate limiting)."""
        now = time.time()
        user_messages = self.message_counts[user_id]
        
        # Remove old messages (older than 1 minute)
        user_messages = [msg_time for msg_time in user_messages if now - msg_time < 60]
        self.message_counts[user_id] = user_messages
        
        if len(user_messages) >= MAX_MESSAGES_PER_MINUTE:
            return False
        
        user_messages.append(now)
        return True
    
    def can_connect(self, user_id: int) -> bool:
        """Check if user can establish new connection."""
        return self.connection_counts[user_id] < MAX_CONNECTIONS_PER_USER
    
    def add_connection(self, user_id: int):
        """Add user connection."""
        self.connection_counts[user_id] += 1
    
    def remove_connection(self, user_id: int):
        """Remove user connection."""
        self.connection_counts[user_id] = max(0, self.connection_counts[user_id] - 1)


class WebSocketConnectionManager:
    """Improved WebSocket connection manager with better performance and reliability."""
    
    def __init__(
        self,
        chat_service: ChatService = Depends(),
    ):
        """Initialize WebSocket connection manager."""
        self._chat_service = chat_service
        self._rate_limiter = RateLimiter()
        
        # Connection storage: chat_id -> [(websocket, user_id, connection_id, last_ping)]
        self._active_connections: dict[int, list[tuple[WebSocket, int, str, float]]] = defaultdict(list)
        self._user_connections: dict[int, set[str]] = defaultdict(set)  # user_id -> connection_ids
        self._locks: dict[int, asyncio.Lock] = {}
        self._cleanup_task: asyncio.Task | None = None
        
        logger.info("[INIT] ConnectionManager initialized.")

    async def _ensure_cleanup_task(self):
        """Ensure cleanup task is running."""
        if not self._cleanup_task or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_dead_connections())
            except RuntimeError:
                # No event loop running, skip cleanup task for now
                logger.warning("No event loop running, skipping cleanup task initialization")
                pass

    async def _get_lock(self, chat_id: int) -> asyncio.Lock:
        """Get or create lock for a chat."""
        if chat_id not in self._locks:
            self._locks[chat_id] = asyncio.Lock()
        return self._locks[chat_id]

    async def _cleanup_dead_connections(self):
        """Periodically cleanup dead connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                now = time.time()
                dead_connections = []
                
                for chat_id, connections in self._active_connections.items():
                    for websocket, user_id, connection_id, last_ping in connections:
                        if now - last_ping > WEBSOCKET_PING_TIMEOUT * 2:
                            dead_connections.append((connection_id, chat_id, user_id))
                
                for conn_id, chat_id, user_id in dead_connections:
                    await self.disconnect(conn_id, chat_id, user_id)
                    
                if dead_connections:
                    logger.info(f"Cleaned up {len(dead_connections)} dead connections")
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int) -> str:
        """Connect user to chat with improved validation."""
        logger.info(f"[CONNECT] New connection attempt: chat_id={chat_id}, user_id={user_id}")
        
        # Ensure cleanup task is running
        await self._ensure_cleanup_task()
        
        # Rate limiting check
        if not self._rate_limiter.can_connect(user_id):
            logger.warning(f"[CONNECT] Rate limit exceeded for user {user_id}")
            await websocket.close(code=1008, reason="Too many connections")
            raise ValueError("Too many connections")
        
        await websocket.accept()
        connection_id = str(uuid4())
        now = time.time()

        async with await self._get_lock(chat_id):
            connections = self._active_connections.setdefault(chat_id, [])
            
            # Check for duplicate connections from same user
            for ws, uid, _, _ in connections:
                if uid == user_id:
                    logger.warning(f"[CONNECT] Duplicate connection detected for user {user_id}")
                    await ws.close(code=1008, reason="Duplicate connection")
                    # Remove old connection
                    connections = [(w, u, c, t) for w, u, c, t in connections if u != user_id]
                    self._active_connections[chat_id] = connections

            connections.append((websocket, user_id, connection_id, now))
            self._user_connections[user_id].add(connection_id)
            self._rate_limiter.add_connection(user_id)
            
            logger.info(f"[CONNECT] Connection established: chat_id={chat_id}, user_id={user_id}, connection_id={connection_id}")

        return connection_id

    async def disconnect(self, connection_id: str, chat_id: int, user_id: int):
        """Disconnect user from chat with cleanup."""
        logger.info(f"[DISCONNECT] User {user_id} disconnecting from chat {chat_id}, connection_id={connection_id}")
        
        async with await self._get_lock(chat_id):
            connections = self._active_connections.get(chat_id, [])
            self._active_connections[chat_id] = [
                (ws, uid, conn_id, last_ping)
                for ws, uid, conn_id, last_ping in connections
                if conn_id != connection_id
            ]
            
            # Cleanup user connections
            self._user_connections[user_id].discard(connection_id)
            self._rate_limiter.remove_connection(user_id)
            
            # Cleanup empty chats
            if not self._active_connections[chat_id]:
                self._active_connections.pop(chat_id, None)
                self._locks.pop(chat_id, None)
                logger.info(f"[DISCONNECT] All users disconnected from chat {chat_id}, cleaned up resources")
            
            logger.info(f"[DISCONNECT] User {user_id} successfully disconnected from chat {chat_id}")

    async def run(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Main WebSocket handler with improved error handling and ping/pong."""
        connection_id = await self.connect(websocket, chat_id, user_id)
        
        # Start ping task
        ping_task = asyncio.create_task(self._ping_loop(websocket, connection_id, chat_id, user_id))
        
        try:
            while True:
                # Set receive timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[TIMEOUT] Receive timeout for user {user_id} in chat {chat_id}")
                    break
                
                message_data = orjson.loads(data)
                logger.info(f"[RECEIVE] Received data: {message_data} from user {user_id}")

                if message_data.get("type") == "new_message":
                    # Rate limiting check
                    if not self._rate_limiter.can_send_message(user_id):
                        await websocket.send_text(
                            orjson.dumps({
                                "type": "error",
                                "message": "Rate limit exceeded. Please wait before sending another message."
                            }).decode()
                        )
                        continue
                    
                    message = await self._chat_service.create_message(
                        chat_id=chat_id,
                        sender_id=user_id,
                        text=message_data.get("data", ""),
                    )
                    logger.info(f"[MESSAGE] New message created in chat {chat_id} by user {user_id}: {message.text}")
                    asyncio.create_task(self.broadcast(message, user_id, chat_id))

                elif message_data.get("type") == "mark_as_read":
                    if "message_id" not in message_data:
                        logger.warning("[WARNING] Missing message_id in mark_as_read event")
                        continue
                    asyncio.create_task(
                        self._handle_read_receipt(int(message_data["message_id"]))
                    )
                    
                elif message_data.get("type") == "ping":
                    await websocket.send_text(
                        orjson.dumps({"type": "pong"}).decode()
                    )
                    
        except WebSocketDisconnect:
            logger.warning(f"[DISCONNECT] WebSocket disconnect detected for user {user_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"[ERROR] WebSocket error for user {user_id} in chat {chat_id}: {e}")
            await websocket.close(code=1011)
        finally:
            ping_task.cancel()
            await self.disconnect(connection_id, chat_id, user_id)

    async def _ping_loop(self, websocket: WebSocket, connection_id: str, chat_id: int, user_id: int):
        """Send periodic ping messages to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(WEBSOCKET_PING_INTERVAL)
                
                # Update last ping time
                async with await self._get_lock(chat_id):
                    connections = self._active_connections.get(chat_id, [])
                    for i, (ws, uid, conn_id, _) in enumerate(connections):
                        if conn_id == connection_id:
                            connections[i] = (ws, uid, conn_id, time.time())
                            break
                
                try:
                    await websocket.send_text(
                        orjson.dumps({"type": "ping"}).decode()
                    )
                except Exception:
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in ping loop for user {user_id}: {e}")

    async def _handle_read_receipt(self, message_id: int):
        """Handle read receipt with error handling."""
        try:
            message = await self._chat_service.get_message_by_id(message_id)
            if not message:
                logger.warning(f"Message {message_id} not found")
                return
            asyncio.create_task(
                self._notify_sender(message.id, message.sender_id, message.chat_id)
            )
        except Exception as e:
            logger.error(f"Error handling read receipt for message {message_id}: {e}")

    async def _notify_sender(self, message_id: int, sender_id: int, chat_id: int):
        """Notify sender about read receipt with error handling."""
        connections = self._active_connections.get(chat_id, [])
        async with await self._get_lock(chat_id):
            for websocket, client_id, _, _ in connections:
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
                        logger.info(f"Sent read receipt for message {message_id} to sender {sender_id}")
                    except Exception as e:
                        logger.error(f"Error notifying sender {sender_id}: {e}")

    async def broadcast(self, message: Message, sender_id: int, chat_id: int):
        """Broadcast message to all users in chat except sender."""
        logger.info(f"[BROADCAST] Sending message {message.id} from sender {sender_id} to chat {chat_id}")
        
        connections = self._active_connections.get(chat_id, [])
        if not connections:
            logger.warning(f"[BROADCAST] No active connections in chat {chat_id}, message not sent.")
            return

        message_data = orjson.dumps(
            {
                "type": "new_message",
                "data": GetMessageSchema.model_validate(message).model_dump_json(),
            }
        ).decode()

        dead_connections = []
        async with await self._get_lock(chat_id):
            for websocket, client_id, connection_id, _ in connections:
                if client_id == sender_id:
                    continue
                try:
                    await websocket.send_text(message_data)
                    logger.info(f"[BROADCAST] Message {message.id} sent to client {client_id}")
                except Exception as e:
                    logger.error(f"[ERROR] Failed to send message {message.id} to client {client_id}: {e}")
                    dead_connections.append((connection_id, chat_id, client_id))

        # Cleanup dead connections
        for conn_id, c_id, cl_id in dead_connections:
            await self.disconnect(conn_id, c_id, cl_id)

    @staticmethod
    async def validate_user(token: str) -> int | None:
        """Validate user token with improved error handling."""
        try:
            if not token.startswith("Bearer "):
                logger.warning("[AUTH] Invalid token format")
                return None
                
            token_value = token.split(" ")[-1]
            data = jwt.decode(
                token_value, settings().SECRET, algorithms=[JWT_ALGORITHM]
            )
            user_id = data.get("user_id")
            
            if not user_id:
                logger.warning("[AUTH] No user_id in token")
                return None
                
            logger.info(f"[AUTH] User validation successful: user_id={user_id}")
            return user_id
            
        except (InvalidSignatureError, DecodeError, ExpiredSignatureError) as e:
            logger.warning(f"[AUTH] Token validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"[AUTH] Unexpected error during token validation: {e}")
            return None

    async def get_connection_stats(self) -> dict:
        """Get connection statistics for monitoring."""
        total_connections = sum(len(connections) for connections in self._active_connections.values())
        total_users = len(self._user_connections)
        total_chats = len(self._active_connections)
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_chats": total_chats,
            "connections_per_chat": {chat_id: len(connections) for chat_id, connections in self._active_connections.items()}
        }
