import functools
import pathlib

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent
    ENVIRONMENT: str = Field(default="local", description="Environment: local, test, production, showroom")
    SECRET: str = Field(default="", description="JWT secret key - must be set in production")
    
    # CORS settings
    CORS_ALLOW_ORIGIN_LIST: str = Field(default="*", description="Comma-separated list of allowed origins")
    SESSION_MIDDLEWARE_SECRET: str = Field(default="", description="Session middleware secret - must be set in production")

    # Database settings
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="", description="PostgreSQL database name")
    
    # Database connection pool settings
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=30, description="Database max overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle time")

    # Redis settings
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")

    # Performance settings
    WORKERS_COUNT: int = Field(default=1, description="Number of worker processes")
    MAX_CONCURRENT_REQUESTS: int = Field(default=1000, description="Max concurrent requests")
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_MAX_LENGTH: int = Field(default=128, description="Maximum password length")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="Requests per minute per user")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="{time} | {level} | {message}", description="Log format")

    @field_validator("SECRET", "SESSION_MIDDLEWARE_SECRET")
    @classmethod
    def validate_secrets(cls, v, info):
        if info.data.get("ENVIRONMENT") in ["production", "showroom"] and not v:
            raise ValueError("SECRET and SESSION_MIDDLEWARE_SECRET must be set in production environment")
        return v

    @field_validator("CORS_ALLOW_ORIGIN_LIST")
    @classmethod
    def validate_cors_origins(cls, v, info):
        if v == "*" and info.data.get("ENVIRONMENT") in ["production", "showroom"]:
            raise ValueError("CORS_ALLOW_ORIGIN_LIST cannot be '*' in production environment")
        return v

    @property
    def cors_allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGIN_LIST.split(",")]

    @property
    def redis_dsn(self) -> str:
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def postgres_dsn(self) -> str:
        database = (
            self.POSTGRES_DB
            if self.ENVIRONMENT != "test"
            else f"{self.POSTGRES_DB}_test"
        )
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{database}"
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT in ["production", "showroom"]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT in ["local", "test"]


@functools.lru_cache
def settings() -> Settings:
    return Settings()


@functools.lru_cache
def get_settings() -> Settings:
    """Get settings instance (alias for settings())."""
    return Settings()
