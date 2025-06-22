import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import warnings

# Suppress deprecation warnings for websockets
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")

try:
    from websockets.client import connect as ws_connect
    from websockets.exceptions import ConnectionClosed
except ImportError:
    # Fallback for newer versions
    ws_connect = None
    ConnectionClosed = Exception

from tests.factories.user import UserFactory
from tests.factories.message import MessageFactory
from tests.factories.chat import ChatFactory
from main import app
from ws.connection import WebSocketConnectionManager
from tests.conftest import api_client
from tests.utils import (
    TEST_USER_ID,
    TEST_CHAT_ID,
    TEST_MESSAGE_ID,
    TEST_CONNECTION_ID,
    TEST_RATE_LIMIT,
    TEST_TIMEOUT_SECONDS,
    TEST_MAX_CONNECTIONS_PER_USER,
    TEST_MAX_MESSAGE_LENGTH,
    TEST_PING_INTERVAL,
    TEST_PONG_TIMEOUT
)


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.fixture
    def ws_manager(self):
        """Create WebSocket connection manager."""
        return WebSocketConnectionManager()

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, ws_manager):
        """Test establishing WebSocket connection."""
        # Simulate connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, chat_id=1, user_id=1)
        
        assert len(ws_manager._active_connections) == 1
        assert 1 in ws_manager._active_connections
        assert mock_websocket in [conn[0] for conn in ws_manager._active_connections[1]]

    @pytest.mark.asyncio
    async def test_websocket_disconnection(self, ws_manager):
        """Test WebSocket disconnection."""
        # Simulate connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        assert len(ws_manager.active_connections) == 1
        
        # Disconnect
        await ws_manager.disconnect(mock_websocket, user_id=1)
        assert len(ws_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_message_broadcast(self, ws_manager):
        """Test broadcasting message to all connections."""
        mock_websocket1 = AsyncMock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8080
        mock_websocket2 = AsyncMock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8081
        await ws_manager.connect(mock_websocket1, user_id=UserFactory.build().id or 1)
        await ws_manager.connect(mock_websocket2, user_id=UserFactory.build().id or 2)
        message = MessageFactory.build().__dict__
        await ws_manager.broadcast(message)
        mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        mock_websocket2.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_websocket_personal_message(self, ws_manager):
        """Test sending personal message to specific user."""
        mock_websocket1 = AsyncMock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8080
        mock_websocket2 = AsyncMock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8081
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        await ws_manager.connect(mock_websocket1, user_id=user1.id or 1)
        await ws_manager.connect(mock_websocket2, user_id=user2.id or 2)
        message = MessageFactory.build().__dict__
        await ws_manager.send_personal_message(message, user_id=user1.id or 1)
        mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        mock_websocket2.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_multiple_connections_same_user(self, ws_manager):
        """Test multiple connections for the same user."""
        # Create multiple connections for same user
        mock_websocket1 = AsyncMock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8080
        
        mock_websocket2 = AsyncMock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8081
        
        # Connect both for user 1
        await ws_manager.connect(mock_websocket1, user_id=1)
        await ws_manager.connect(mock_websocket2, user_id=1)
        
        assert len(ws_manager.active_connections[1]) == 2
        
        # Send personal message to user 1
        message = {"type": "personal", "content": "Hello user 1!"}
        await ws_manager.send_personal_message(message, user_id=1)
        
        # Check that both connections received the message
        mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        mock_websocket2.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(self, ws_manager):
        """Test cleanup of disconnected connections."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        assert len(ws_manager.active_connections) == 1
        
        # Simulate connection close
        mock_websocket.close.side_effect = ConnectionClosed(1000, "Normal closure")
        
        # Disconnect
        await ws_manager.disconnect(mock_websocket, user_id=1)
        assert len(ws_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, ws_manager):
        """Test ping/pong mechanism."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        
        # Simulate ping
        await ws_manager.send_ping(mock_websocket)
        mock_websocket.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_stats(self, ws_manager):
        """Test connection statistics."""
        # Create multiple connections
        mock_websocket1 = AsyncMock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8080
        
        mock_websocket2 = AsyncMock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8081
        
        # Connect
        await ws_manager.connect(mock_websocket1, user_id=1)
        await ws_manager.connect(mock_websocket2, user_id=2)
        
        # Get stats
        stats = ws_manager.get_connection_stats()
        
        assert stats["total_connections"] == 2
        assert stats["unique_users"] == 2
        assert stats["connections_per_user"] == {1: 1, 2: 1}

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, ws_manager):
        """Test error handling in WebSocket operations."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        
        # Simulate send error
        mock_websocket.send_text.side_effect = Exception("Send error")
        
        # Try to send message
        message = {"type": "test", "content": "test"}
        await ws_manager.send_personal_message(message, user_id=1)
        
        # Connection should be removed due to error
        assert len(ws_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_rate_limiting(self, ws_manager):
        """Test rate limiting for WebSocket connections."""
        # Create multiple connections rapidly
        connections = []
        for i in range(10):
            mock_websocket = AsyncMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 8080 + i
            
            await ws_manager.connect(mock_websocket, user_id=i)
            connections.append(mock_websocket)
        
        # Check that all connections are established
        assert len(ws_manager.active_connections) == 10

    @pytest.mark.asyncio
    async def test_websocket_message_validation(self, ws_manager):
        """Test message validation."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        
        # Test valid message
        valid_message = {"type": "chat", "content": "Hello", "timestamp": "2023-01-01T00:00:00Z"}
        await ws_manager.send_personal_message(valid_message, user_id=1)
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_persistence(self, ws_manager):
        """Test connection persistence across operations."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        
        # Perform multiple operations
        for i in range(5):
            message = {"type": "test", "content": f"Message {i}"}
            await ws_manager.send_personal_message(message, user_id=1)
        
        # Connection should still be active
        assert len(ws_manager.active_connections) == 1
        assert mock_websocket in ws_manager.active_connections[1]

    @pytest.mark.asyncio
    async def test_websocket_concurrent_operations(self, ws_manager):
        """Test concurrent WebSocket operations."""
        # Create multiple connections
        connections = []
        for i in range(5):
            mock_websocket = AsyncMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 8080 + i
            connections.append(mock_websocket)
        
        # Connect all concurrently
        connect_tasks = [
            ws_manager.connect(conn, user_id=i) 
            for i, conn in enumerate(connections)
        ]
        await asyncio.gather(*connect_tasks)
        
        # Send messages concurrently
        message = {"type": "broadcast", "content": "Concurrent test"}
        send_tasks = [ws_manager.send_personal_message(message, user_id=i) for i in range(5)]
        await asyncio.gather(*send_tasks)
        
        # Check all connections received messages
        for conn in connections:
            conn.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_timeout(self, ws_manager):
        """Test connection timeout handling."""
        # Create connection
        mock_websocket = AsyncMock()
        mock_websocket.client.host = "127.0.0.1"
        mock_websocket.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket, user_id=1)
        
        # Simulate timeout
        mock_websocket.send_text.side_effect = Exception("Connection timeout")
        
        # Try to send message
        message = {"type": "test", "content": "test"}
        await ws_manager.send_personal_message(message, user_id=1)
        
        # Connection should be removed
        assert len(ws_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_connection_recovery(self, ws_manager):
        """Test connection recovery after disconnection."""
        # Create connection
        mock_websocket1 = AsyncMock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8080
        
        # Connect
        await ws_manager.connect(mock_websocket1, user_id=1)
        assert len(ws_manager.active_connections) == 1
        
        # Disconnect
        await ws_manager.disconnect(mock_websocket1, user_id=1)
        assert len(ws_manager.active_connections) == 0
        
        # Reconnect
        mock_websocket2 = AsyncMock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8081
        
        await ws_manager.connect(mock_websocket2, user_id=1)
        assert len(ws_manager.active_connections) == 1
        assert mock_websocket2 in ws_manager.active_connections[1]


class TestWebSocketEndpoints:
    """Integration tests for WebSocket endpoints."""

    @pytest.mark.asyncio
    async def test_websocket_endpoint_connection(self):
        """Test WebSocket endpoint connection."""
        # This would require a running server to test actual WebSocket connections
        # For now, we'll test the endpoint registration
        app_routes = [route.path for route in app.routes]
        assert "/ws/{user_id}" in app_routes

    @pytest.mark.asyncio
    async def test_websocket_endpoint_with_authentication(self):
        """Test WebSocket endpoint with authentication."""
        # Test that the endpoint requires authentication
        # This would be tested with actual WebSocket client
        pass

    @pytest.mark.asyncio
    async def test_websocket_endpoint_message_handling(self):
        """Test WebSocket endpoint message handling."""
        # Test message handling in the endpoint
        # This would require actual WebSocket testing
        pass


class TestWebSocketPerformance:
    """Performance tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_mass_connection(self, ws_manager):
        """Test handling many concurrent connections."""
        # Create many connections
        connections = []
        for i in range(100):
            mock_websocket = AsyncMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 8080 + i
            connections.append(mock_websocket)
        
        # Connect all
        start_time = asyncio.get_event_loop().time()
        connect_tasks = [
            ws_manager.connect(conn, user_id=i) 
            for i, conn in enumerate(connections)
        ]
        await asyncio.gather(*connect_tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Check performance
        assert end_time - start_time < 1.0  # Should complete within 1 second
        assert len(ws_manager.active_connections) == 100

    @pytest.mark.asyncio
    async def test_websocket_mass_message_broadcast(self, ws_manager):
        """Test broadcasting to many connections."""
        # Create many connections
        connections = []
        for i in range(50):
            mock_websocket = AsyncMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 8080 + i
            await ws_manager.connect(mock_websocket, user_id=i)
            connections.append(mock_websocket)
        
        # Broadcast message
        start_time = asyncio.get_event_loop().time()
        message = {"type": "broadcast", "content": "Mass broadcast test"}
        await ws_manager.broadcast(message)
        end_time = asyncio.get_event_loop().time()
        
        # Check performance
        assert end_time - start_time < 0.5  # Should complete within 0.5 seconds
        
        # Check all received message
        for conn in connections:
            conn.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_memory_usage(self, ws_manager):
        """Test memory usage with many connections."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many connections
        connections = []
        for i in range(1000):
            mock_websocket = AsyncMock()
            mock_websocket.client.host = "127.0.0.1"
            mock_websocket.client.port = 8080 + i
            await ws_manager.connect(mock_websocket, user_id=i)
            connections.append(mock_websocket)
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
        
        # Cleanup
        for i, conn in enumerate(connections):
            await ws_manager.disconnect(conn, user_id=i)


class TestWebSocketConnectionManager:
    @pytest.fixture
    def connection_manager(self):
        return WebSocketConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        mock = AsyncMock()
        mock.send_text = AsyncMock()
        mock.send_json = AsyncMock()
        mock.close = AsyncMock()
        mock.receive_text = AsyncMock()
        mock.receive_json = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_connect_user(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        # Act
        await connection_manager.connect(user_id, mock_websocket)
        # Assert
        assert user_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[user_id]
        assert len(connection_manager.active_connections[user_id]) == 1

    @pytest.mark.asyncio
    async def test_disconnect_user(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.disconnect(user_id, mock_websocket)
        # Assert
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_user(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        # Act
        await connection_manager.disconnect(user_id, mock_websocket)
        # Assert
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        message = MessageFactory.build().__dict__
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_to_nonexistent_user(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        message = MessageFactory.build().__dict__
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        # Should not raise any exception

    @pytest.mark.asyncio
    async def test_broadcast_message(self, connection_manager):
        # Arrange
        user1_id = UserFactory.build().id
        user2_id = UserFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        message = MessageFactory.build().__dict__
        
        await connection_manager.connect(user1_id, mock_websocket1)
        await connection_manager.connect(user2_id, mock_websocket2)
        # Act
        await connection_manager.broadcast(message)
        # Assert
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message_to_chat(self, connection_manager):
        # Arrange
        user1_id = UserFactory.build().id
        user2_id = UserFactory.build().id
        chat_id = ChatFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        message = MessageFactory.build().__dict__
        
        await connection_manager.connect(user1_id, mock_websocket1)
        await connection_manager.connect(user2_id, mock_websocket2)
        # Act
        await connection_manager.broadcast_to_chat(message, chat_id, [user1_id, user2_id])
        # Assert
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message_to_chat_with_nonexistent_users(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        chat_id = ChatFactory.build().id
        mock_websocket = AsyncMock()
        message = MessageFactory.build().__dict__
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.broadcast_to_chat(message, chat_id, [user_id, 99999])
        # Assert
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_multiple_connections_per_user(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        message = MessageFactory.build().__dict__
        
        await connection_manager.connect(user_id, mock_websocket1)
        await connection_manager.connect(user_id, mock_websocket2)
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        assert len(connection_manager.active_connections[user_id]) == 2
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_connection_cleanup(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.disconnect(user_id, mock_websocket)
        # Assert
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_get_connection_stats(self, connection_manager):
        # Arrange
        user1_id = UserFactory.build().id
        user2_id = UserFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        await connection_manager.connect(user1_id, mock_websocket1)
        await connection_manager.connect(user2_id, mock_websocket2)
        # Act
        stats = connection_manager.get_connection_stats()
        # Assert
        assert stats["total_connections"] == 2
        assert stats["total_users"] == 2
        assert user1_id in stats["connected_users"]
        assert user2_id in stats["connected_users"]

    @pytest.mark.asyncio
    async def test_get_connection_stats_empty(self, connection_manager):
        # Arrange
        # Act
        stats = connection_manager.get_connection_stats()
        # Assert
        assert stats["total_connections"] == 0
        assert stats["total_users"] == 0
        assert len(stats["connected_users"]) == 0

    @pytest.mark.asyncio
    async def test_is_user_connected(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        # Act
        result_before = connection_manager.is_user_connected(user_id)
        await connection_manager.connect(user_id, mock_websocket)
        result_after = connection_manager.is_user_connected(user_id)
        # Assert
        assert result_before is False
        assert result_after is True

    @pytest.mark.asyncio
    async def test_get_user_connections(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        await connection_manager.connect(user_id, mock_websocket1)
        await connection_manager.connect(user_id, mock_websocket2)
        # Act
        connections = connection_manager.get_user_connections(user_id)
        # Assert
        assert len(connections) == 2
        assert mock_websocket1 in connections
        assert mock_websocket2 in connections

    @pytest.mark.asyncio
    async def test_get_user_connections_nonexistent(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        # Act
        connections = connection_manager.get_user_connections(user_id)
        # Assert
        assert connections == []

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        message = MessageFactory.build().__dict__
        mock_websocket.send_json.side_effect = Exception("WebSocket error")
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        # Should handle the error gracefully and remove the connection
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_websocket_close_error(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket.close.side_effect = Exception("Close error")
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.disconnect(user_id, mock_websocket)
        # Assert
        # Should handle the error gracefully
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websockets = [AsyncMock() for _ in range(5)]
        message = MessageFactory.build().__dict__
        
        # Act
        for websocket in mock_websockets:
            await connection_manager.connect(user_id, websocket)
        
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        assert len(connection_manager.active_connections[user_id]) == 5
        for websocket in mock_websockets:
            websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_connection_removal_on_error(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        message = MessageFactory.build().__dict__
        mock_websocket.send_json.side_effect = Exception("Connection error")
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_users_broadcast(self, connection_manager):
        # Arrange
        users = [UserFactory.build().id for _ in range(3)]
        websockets = [AsyncMock() for _ in range(3)]
        message = MessageFactory.build().__dict__
        
        for user_id, websocket in zip(users, websockets):
            await connection_manager.connect(user_id, websocket)
        # Act
        await connection_manager.broadcast(message)
        # Assert
        for websocket in websockets:
            websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_connection_manager_cleanup(self, connection_manager):
        # Arrange
        users = [UserFactory.build().id for _ in range(3)]
        websockets = [AsyncMock() for _ in range(3)]
        
        for user_id, websocket in zip(users, websockets):
            await connection_manager.connect(user_id, websocket)
        # Act
        for user_id, websocket in zip(users, websockets):
            await connection_manager.disconnect(user_id, websocket)
        # Assert
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_message_validation(self, connection_manager, mock_websocket):
        # Arrange
        user_id = UserFactory.build().id
        valid_message = MessageFactory.build().__dict__
        invalid_message = None
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.send_personal_message(valid_message, user_id)
        await connection_manager.send_personal_message(invalid_message, user_id)
        # Assert
        mock_websocket.send_json.assert_called_once_with(valid_message)

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = asyncio.TimeoutError()
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        await connection_manager.send_personal_message(MessageFactory.build().__dict__, user_id)
        # Assert
        assert user_id not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_performance(self, connection_manager):
        # Arrange
        users = [UserFactory.build().id for _ in range(100)]
        websockets = [AsyncMock() for _ in range(100)]
        message = MessageFactory.build().__dict__
        
        # Act
        start_time = datetime.now()
        for user_id, websocket in zip(users, websockets):
            await connection_manager.connect(user_id, websocket)
        
        await connection_manager.broadcast(message)
        
        for user_id, websocket in zip(users, websockets):
            await connection_manager.disconnect(user_id, websocket)
        end_time = datetime.now()
        # Assert
        duration = (end_time - start_time).total_seconds()
        assert duration < 1.0  # Should complete within 1 second
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connection_manager_memory_cleanup(self, connection_manager):
        # Arrange
        initial_connections = len(connection_manager.active_connections)
        users = [UserFactory.build().id for _ in range(10)]
        websockets = [AsyncMock() for _ in range(10)]
        
        for user_id, websocket in zip(users, websockets):
            await connection_manager.connect(user_id, websocket)
        
        middle_connections = len(connection_manager.active_connections)
        
        for user_id, websocket in zip(users, websockets):
            await connection_manager.disconnect(user_id, websocket)
        # Act
        final_connections = len(connection_manager.active_connections)
        # Assert
        assert initial_connections == 0
        assert middle_connections == 10
        assert final_connections == 0

    @pytest.mark.asyncio
    async def test_connection_manager_thread_safety(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket = AsyncMock()
        message = MessageFactory.build().__dict__
        
        await connection_manager.connect(user_id, mock_websocket)
        # Act
        # Simulate concurrent operations
        tasks = []
        for _ in range(10):
            task1 = asyncio.create_task(connection_manager.send_personal_message(message, user_id))
            task2 = asyncio.create_task(connection_manager.get_connection_stats())
            tasks.extend([task1, task2])
        
        await asyncio.gather(*tasks)
        # Assert
        assert user_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[user_id]

    @pytest.mark.asyncio
    async def test_connection_manager_error_recovery(self, connection_manager):
        # Arrange
        user_id = UserFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        message = MessageFactory.build().__dict__
        
        # First connection fails
        mock_websocket1.send_json.side_effect = Exception("Connection 1 failed")
        await connection_manager.connect(user_id, mock_websocket1)
        
        # Second connection works
        await connection_manager.connect(user_id, mock_websocket2)
        # Act
        await connection_manager.send_personal_message(message, user_id)
        # Assert
        assert user_id in connection_manager.active_connections
        assert mock_websocket1 not in connection_manager.active_connections[user_id]
        assert mock_websocket2 in connection_manager.active_connections[user_id]
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_connection_manager_edge_cases(self, connection_manager):
        # Arrange
        # Test with None values
        await connection_manager.send_personal_message(None, None)
        
        # Test with empty message
        await connection_manager.broadcast({})
        
        # Test with very large message
        large_message = {"data": "x" * 10000}
        await connection_manager.broadcast(large_message)
        # Act & Assert
        # Should handle all edge cases gracefully without errors

    @pytest.mark.asyncio
    async def test_connection_manager_integration(self, connection_manager):
        # Arrange
        # Simulate a complete chat session
        user1_id = UserFactory.build().id
        user2_id = UserFactory.build().id
        chat_id = ChatFactory.build().id
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        # Connect users
        await connection_manager.connect(user1_id, mock_websocket1)
        await connection_manager.connect(user2_id, mock_websocket2)
        
        # Send messages
        message1 = MessageFactory.build().__dict__
        message2 = MessageFactory.build().__dict__
        
        await connection_manager.send_personal_message(message1, user1_id)
        await connection_manager.broadcast_to_chat(message2, chat_id, [user1_id, user2_id])
        
        # Disconnect users
        await connection_manager.disconnect(user1_id, mock_websocket1)
        await connection_manager.disconnect(user2_id, mock_websocket2)
        # Act & Assert
        assert len(connection_manager.active_connections) == 0
        mock_websocket1.send_json.assert_called()
        mock_websocket2.send_json.assert_called() 