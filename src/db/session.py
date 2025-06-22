import asyncio
import functools
import typing
from contextlib import asynccontextmanager

from sqlalchemy import URL, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings


@functools.lru_cache
def get_engine(url: str | URL | None = None, **kwargs) -> AsyncEngine:
    """Create database engine with optimized settings."""
    engine_kwargs = {
        "echo": settings().is_development,  # SQL logging only in development
        "future": True,
        "pool_pre_ping": True,  # Validate connections before use
        "connect_args": {
            "server_settings": {
                "application_name": "messenger_app",
                "timezone": "UTC",
            }
        },
    }
    
    # Use NullPool for testing to avoid connection issues
    if settings().ENVIRONMENT == "test":
        engine_kwargs["poolclass"] = NullPool
    else:
        # Add pool settings only for non-test environments
        engine_kwargs.update({
            "pool_size": settings().DB_POOL_SIZE,
            "max_overflow": settings().DB_MAX_OVERFLOW,
            "pool_timeout": settings().DB_POOL_TIMEOUT,
            "pool_recycle": settings().DB_POOL_RECYCLE,
        })
    
    engine_kwargs.update(kwargs)
    
    return create_async_engine(
        url or settings().postgres_dsn,
        **engine_kwargs,
    )


def get_async_session(url: str | URL | None = None) -> async_sessionmaker[AsyncSession]:
    """Create async session factory with optimized settings."""
    return async_sessionmaker(
        get_engine(url or settings().postgres_dsn),
        expire_on_commit=False,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> typing.AsyncGenerator[AsyncSession, None]:
    """Get database session with retry logic and error handling."""
    async_session = get_async_session()
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with async_session() as session:
                yield session
                break
        except SQLAlchemyError as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff


@asynccontextmanager
async def get_session_with_retry(max_retries: int = 3) -> typing.AsyncGenerator[AsyncSession, None]:
    """Get database session with retry logic for critical operations."""
    async_session = get_async_session()
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with async_session() as session:
                yield session
                break
        except SQLAlchemyError as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay * (2 ** attempt))


async def health_check() -> bool:
    """Check database connectivity."""
    try:
        async_session = get_async_session()
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
