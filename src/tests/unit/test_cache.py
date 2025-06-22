import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import timedelta
from tests.factories.message import MessageFactory
from tests.factories.user import UserFactory
from utils.cache import CacheManager, cache_manager

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    mock.expire.return_value = True
    mock.ttl.return_value = -1
    mock.mget.return_value = []
    mock.incr.return_value = 1
    mock.incrby.return_value = 1
    mock.decr.return_value = 1
    mock.decrby.return_value = 1
    mock.flushdb.return_value = True
    return mock

@pytest.fixture
def cache_manager_instance(mock_redis):
    instance = CacheManager()
    instance._redis = mock_redis
    return instance

@pytest.fixture
def mock_redis_with_storage():
    """Mock Redis client with in-memory storage for cache decorator tests."""
    mock = AsyncMock()
    
    # In-memory storage
    storage = {}
    
    async def mock_get(key):
        return storage.get(key)
    
    async def mock_set(key, value):
        storage[key] = value
        return True
    
    async def mock_expire(key, seconds):
        return True
    
    # Replace methods
    mock.get = mock_get
    mock.set = mock_set
    mock.expire = mock_expire
    
    return mock

class TestCacheManager:
    """Unit tests for CacheManager class."""

    @pytest.mark.asyncio
    async def test_get_existing_key(self, cache_manager_instance, mock_redis):
        """Test getting existing key from cache."""
        # Arrange
        data = MessageFactory.build().__dict__
        mock_redis.get.return_value = '{"test": "data"}'
        
        # Act
        result = await cache_manager_instance.get("test_key")
        
        # Assert
        assert result == {"test": "data"}
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_manager_instance, mock_redis):
        """Test getting nonexistent key from cache."""
        # Arrange
        mock_redis.get.return_value = None
        
        # Act
        result = await cache_manager_instance.get("nonexistent_key")
        
        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_get_invalid_json(self, cache_manager_instance, mock_redis):
        """Test getting invalid JSON from cache."""
        # Arrange
        mock_redis.get.return_value = b'invalid json'
        
        # Act
        result = await cache_manager_instance.get("test_key")
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_default_ttl(self, cache_manager_instance, mock_redis):
        """Test setting key with default TTL."""
        # Arrange
        data = MessageFactory.build().__dict__
        
        # Act
        result = await cache_manager_instance.set("test_key", data)
        
        # Assert
        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test_key"
        assert "text" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager_instance, mock_redis):
        """Test setting key with custom TTL."""
        # Arrange
        data = MessageFactory.build().__dict__
        ttl = timedelta(minutes=30)
        
        # Act
        result = await cache_manager_instance.set("test_key", data, ttl)
        
        # Assert
        assert result is True
        mock_redis.set.assert_called_once()
        mock_redis.expire.assert_called_once_with("test_key", 1800)  # 30 minutes in seconds

    @pytest.mark.asyncio
    async def test_set_with_seconds_ttl(self, cache_manager_instance, mock_redis):
        """Test setting key with TTL in seconds."""
        # Arrange
        data = MessageFactory.build().__dict__
        
        # Act
        result = await cache_manager_instance.set("test_key", data, 300)  # 5 minutes
        
        # Assert
        assert result is True
        mock_redis.set.assert_called_once()
        mock_redis.expire.assert_called_once_with("test_key", 300)

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, cache_manager_instance, mock_redis):
        """Test deleting existing key."""
        # Arrange
        mock_redis.delete.return_value = 1
        
        # Act
        result = await cache_manager_instance.delete("test_key")
        
        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache_manager_instance, mock_redis):
        """Test deleting nonexistent key."""
        # Arrange
        mock_redis.delete.return_value = 0
        
        # Act
        result = await cache_manager_instance.delete("nonexistent_key")
        
        # Assert
        assert result is False
        mock_redis.delete.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_exists_true(self, cache_manager_instance, mock_redis):
        """Test checking if key exists."""
        # Arrange
        mock_redis.exists.return_value = 1
        
        # Act
        result = await cache_manager_instance.exists("test_key")
        
        # Assert
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_false(self, cache_manager_instance, mock_redis):
        """Test checking if key doesn't exist."""
        # Arrange
        mock_redis.exists.return_value = 0
        
        # Act
        result = await cache_manager_instance.exists("nonexistent_key")
        
        # Assert
        assert result is False
        mock_redis.exists.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_get_ttl_positive(self, cache_manager_instance, mock_redis):
        """Test getting TTL for key with positive value."""
        # Arrange
        mock_redis.ttl.return_value = 300  # 5 minutes
        
        # Act
        result = await cache_manager_instance.get_ttl("test_key")
        
        # Assert
        assert result == 300
        mock_redis.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_ttl_expired(self, cache_manager_instance, mock_redis):
        """Test getting TTL for expired key."""
        mock_redis.ttl.return_value = -2  # Expired
        
        result = await cache_manager_instance.get_ttl("expired_key")
        
        assert result == -2
        mock_redis.ttl.assert_called_once_with("expired_key")

    @pytest.mark.asyncio
    async def test_get_ttl_no_expiry(self, cache_manager_instance, mock_redis):
        """Test getting TTL for key without expiry."""
        mock_redis.ttl.return_value = -1  # No expiry
        
        result = await cache_manager_instance.get_ttl("no_expiry_key")
        
        assert result == -1
        mock_redis.ttl.assert_called_once_with("no_expiry_key")

    @pytest.mark.asyncio
    async def test_increment(self, cache_manager_instance, mock_redis):
        """Test increment operation."""
        mock_redis.incrby.return_value = 5
        
        result = await cache_manager_instance.increment("counter_key", 5)
        
        assert result == 5
        mock_redis.incrby.assert_called_once_with("counter_key", 5)


class TestGlobalInstance:
    """Unit tests for global cache manager instance."""

    def test_cache_manager_instance(self):
        pass

    async def test_clear_all(self, cache_manager_instance, mock_redis):
        """Test clearing all cache."""
        result = await cache_manager_instance.clear_all()
        
        assert result is True
        mock_redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_manager_instance, mock_redis):
        """Test get_or_set with cache hit."""
        cached_data = {"cached": "data"}
        mock_redis.get.return_value = b'{"cached": "data"}'
        
        async def fetch_func():
            return {"fresh": "data"}
        
        result = await cache_manager_instance.get_or_set("test_key", fetch_func)
        
        assert result == cached_data
        mock_redis.get.assert_called_once_with("test_key")
        # fetch_func should not be called

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_manager_instance, mock_redis):
        """Test get_or_set with cache miss."""
        mock_redis.get.return_value = None
        fresh_data = {"fresh": "data"}
        
        async def fetch_func():
            return fresh_data
        
        result = await cache_manager_instance.get_or_set("test_key", fetch_func)
        
        assert result == fresh_data
        mock_redis.get.assert_called_once_with("test_key")
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_with_custom_ttl(self, cache_manager_instance, mock_redis):
        """Test get_or_set with custom TTL."""
        mock_redis.get.return_value = None
        fresh_data = {"fresh": "data"}
        ttl = timedelta(hours=2)
        
        async def fetch_func():
            return fresh_data
        
        result = await cache_manager_instance.get_or_set("test_key", fetch_func, ttl)
        
        assert result == fresh_data
        mock_redis.get.assert_called_once()
        mock_redis.set.assert_called_once()
        mock_redis.expire.assert_called_once_with("test_key", 7200)  # 2 hours in seconds

    @pytest.mark.asyncio
    async def test_get_or_set_fetch_error(self, cache_manager_instance, mock_redis):
        """Test get_or_set when fetch function raises error."""
        mock_redis.get.return_value = None
        
        async def fetch_func():
            raise ValueError("Fetch error")
        
        with pytest.raises(ValueError, match="Fetch error"):
            await cache_manager_instance.get_or_set("test_key", fetch_func)

    @pytest.mark.asyncio
    async def test_batch_get(self, cache_manager_instance, mock_redis):
        """Test batch get operation."""
        keys = ["key1", "key2", "key3"]
        mock_redis.mget.return_value = [
            b'{"data": "value1"}',
            b'{"data": "value2"}',
            None
        ]
        
        result = await cache_manager_instance.batch_get(keys)
        
        expected = [
            {"data": "value1"},
            {"data": "value2"},
            None
        ]
        assert result == expected
        mock_redis.mget.assert_called_once_with(*keys)

    @pytest.mark.asyncio
    async def test_batch_set(self, cache_manager_instance, mock_redis):
        """Test batch set operation."""
        data = {
            "key1": MessageFactory.build().__dict__,
            "key2": MessageFactory.build().__dict__
        }
        
        result = await cache_manager_instance.batch_set(data)
        
        assert result is True
        assert mock_redis.set.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_delete(self, cache_manager_instance, mock_redis):
        """Test batch delete operation."""
        keys = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 2
        
        result = await cache_manager_instance.batch_delete(keys)
        
        assert result == 2
        mock_redis.delete.assert_called_once_with(*keys)

    @pytest.mark.asyncio
    async def test_increment(self, cache_manager_instance, mock_redis):
        """Test increment operation."""
        mock_redis.incr.return_value = 5
        
        result = await cache_manager_instance.increment("counter_key")
        
        assert result == 5
        mock_redis.incr.assert_called_once_with("counter_key")

    @pytest.mark.asyncio
    async def test_increment_by_amount(self, cache_manager_instance, mock_redis):
        """Test increment by amount operation."""
        mock_redis.incrby.return_value = 10
        
        result = await cache_manager_instance.increment("counter_key", 5)
        
        assert result == 10
        mock_redis.incrby.assert_called_once_with("counter_key", 5)

    @pytest.mark.asyncio
    async def test_decrement(self, cache_manager_instance, mock_redis):
        """Test decrement operation."""
        mock_redis.decr.return_value = 3
        
        result = await cache_manager_instance.decrement("counter_key")
        
        assert result == 3
        mock_redis.decr.assert_called_once_with("counter_key")

    @pytest.mark.asyncio
    async def test_decrement_by_amount(self, cache_manager_instance, mock_redis):
        """Test decrement by amount operation."""
        mock_redis.decrby.return_value = 8
        
        result = await cache_manager_instance.decrement("counter_key", 2)
        
        assert result == 8
        mock_redis.decrby.assert_called_once_with("counter_key", 2)

    @pytest.mark.asyncio
    async def test_redis_connection_error(self, cache_manager_instance, mock_redis):
        """Test handling Redis connection error."""
        mock_redis.get.side_effect = Exception("Redis connection error")
        
        result = await cache_manager_instance.get("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_connection_error_set(self, cache_manager_instance, mock_redis):
        """Test handling Redis connection error in set operation."""
        mock_redis.set.side_effect = Exception("Redis connection error")
        
        result = await cache_manager_instance.set("test_key", {"data": "value"})
        
        assert result is False


class TestDecorators:
    """Unit tests for cache decorators."""

    @pytest.mark.asyncio
    async def test_cache_decorator(self, mock_redis_with_storage):
        """Test cache decorator."""
        from utils.cache import cache, cache_manager

        # Подменяем глобальный cache_manager на mock
        original_redis = cache_manager._redis
        cache_manager._redis = mock_redis_with_storage

        try:
            call_count = 0

            @cache(ttl=300)
            async def test_function(param):
                nonlocal call_count
                call_count += 1
                return f"result_{param}"

            # First call should execute function
            result1 = await test_function("test")
            assert result1 == "result_test"
            assert call_count == 1

            # Second call should use cache
            result2 = await test_function("test")
            assert result2 == "result_test"
            assert call_count == 1  # Should not increment
        finally:
            # Восстанавливаем оригинальный redis
            cache_manager._redis = original_redis

    @pytest.mark.asyncio
    async def test_cache_decorator_different_params(self):
        """Test cache decorator with different parameters."""
        from utils.cache import cache
        
        call_count = 0
        
        @cache(ttl=300)
        async def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # Different parameters should result in different cache keys
        await test_function("param1")
        await test_function("param2")
        
        assert call_count == 2  # Both should execute 