import asyncio
import json
import time
from functools import wraps
from typing import Any
from datetime import timedelta
from unittest.mock import AsyncMock

import redis.asyncio as redis
from loguru import logger

from core.config import settings


class CacheManager:
    """Redis-based cache manager for improved performance."""
    
    def __init__(self):
        self._redis: redis.Redis | None = None
        self._connection_pool: redis.ConnectionPool | None = None
        
    async def connect(self):
        """Connect to Redis."""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings().redis_dsn,
                max_connections=settings().REDIS_POOL_SIZE,
                decode_responses=True
            )
            self._redis = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis.ping()
            logger.success("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._redis = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> any:
        """Get value from cache."""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def _serialize(self, value):
        # Если это dict, исключаем служебные поля
        if isinstance(value, dict):
            return json.dumps({k: v for k, v in value.items() if k != '_sa_instance_state'})
        # Если это объект с __dict__, исключаем служебные поля
        if hasattr(value, '__dict__'):
            return json.dumps({k: v for k, v in value.__dict__.items() if k != '_sa_instance_state'})
        return json.dumps(value)

    async def set(self, key: str, value: any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self._redis:
            return False
        try:
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
            expire = int(expire)
            serialized_value = self._serialize(value)
            await self._redis.set(key, serialized_value)
            if expire > 0:
                await self._redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._redis:
            return False
        try:
            result = await self._redis.delete(key)
            return result == 1
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._redis:
            return False
            
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        if not self._redis:
            return 0
        try:
            if amount == 1:
                return await self._redis.incr(key)
            else:
                return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self._redis:
            return False
            
        try:
            return await self._redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int | None:
        """Get TTL for a key."""
        if not self._redis:
            return None
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache get_ttl error for key {key}: {e}")
            return None

    async def clear_all(self) -> bool:
        """Clear all cache."""
        if not self._redis:
            return False
        try:
            await self._redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache clear_all error: {e}")
            return False

    async def batch_get(self, keys: list[str]) -> list[Any | None]:
        """Batch get values for multiple keys."""
        if not self._redis:
            return [None] * len(keys)
        try:
            values = await self._redis.mget(*keys)
            return [json.loads(v) if v else None for v in values]
        except Exception as e:
            logger.error(f"Cache batch_get error: {e}")
            return [None] * len(keys)

    async def batch_set(self, data: dict[str, any], expire: int | timedelta | None = None) -> bool:
        """Batch set multiple key-value pairs."""
        if not self._redis:
            return False
        try:
            _expire = expire
            if _expire is None:
                _expire = 3600
            if isinstance(_expire, timedelta):
                _expire = int(_expire.total_seconds())
            _expire = int(_expire)
            for key, value in data.items():
                await self._redis.set(key, self._serialize(value))
                if _expire > 0:
                    await self._redis.expire(key, _expire)
            return True
        except Exception as e:
            logger.error(f"Cache batch_set error: {e}")
            return False

    async def batch_delete(self, keys: list[str]) -> int:
        """Batch delete multiple keys."""
        if not self._redis:
            return 0
        try:
            return await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache batch_delete error: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        if not self._redis:
            return 0
        try:
            if amount == 1:
                return await self._redis.decr(key)
            else:
                return await self._redis.decrby(key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return 0

    async def get_or_set(self, key: str, fetch_func, ttl: int | float | timedelta | None = None):
        """Get value from cache or set it using fetch_func if not present."""
        value = await self.get(key)
        if value is not None:
            return value
        value = await fetch_func()
        expire = ttl if ttl is not None else 3600
        if isinstance(expire, timedelta):
            expire = int(expire.total_seconds())
        expire = int(expire)
        await self.set(key, value, expire)
        return value


# Global cache instance
cache_manager = CacheManager()


def cached(expire: int = 3600, ttl: int = None, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = await func(*args, **kwargs)
            _expire = ttl if ttl is not None else expire
            if isinstance(_expire, timedelta):
                _expire = int(_expire.total_seconds())
            _expire = int(_expire)
            await cache_manager.set(cache_key, result, _expire)
            return result
        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern."""
    if not cache_manager._redis:
        return
        
    try:
        keys = await cache_manager._redis.keys(pattern)
        if keys:
            await cache_manager._redis.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error for pattern {pattern}: {e}")


# Rate limiting utilities
class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def is_allowed(self, key: str, max_requests: int, window: int) -> bool:
        """Check if request is allowed within rate limit."""
        current_time = int(time.time())
        window_start = current_time - window
        
        # Get current count
        count_key = f"rate_limit:{key}:{current_time // window}"
        current_count = await self.cache.get(count_key) or 0
        
        if current_count >= max_requests:
            return False
        
        # Increment counter
        await self.cache.increment(count_key, 1)
        await self.cache.expire(count_key, window)
        
        return True
    
    async def get_remaining(self, key: str, max_requests: int, window: int) -> int:
        """Get remaining requests within rate limit."""
        current_time = int(time.time())
        count_key = f"rate_limit:{key}:{current_time // window}"
        current_count = await self.cache.get(count_key) or 0
        
        return max(0, max_requests - current_count)


# Global rate limiter instance
rate_limiter = RateLimiter(cache_manager)

cache = cached 