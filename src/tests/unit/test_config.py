import pytest
import os
from unittest.mock import patch, MagicMock
from tests.factories.user import UserFactory
from core.config import Settings, get_settings


class TestSettings:
    """Unit tests for Settings class."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict('os.environ', {}, clear=True):
            config = Settings()
            
            assert config.ENVIRONMENT == "local"
            assert config.SECRET == ""
            assert config.POSTGRES_HOST == "localhost"
            assert config.POSTGRES_PORT == 5432
            assert config.REDIS_HOST == "localhost"
            assert config.REDIS_PORT == 6379
            assert config.DB_POOL_SIZE == 20
            assert config.RATE_LIMIT_ENABLED is True

    def test_validate_secrets_production_without_secret(self):
        """Test secret validation fails in production without secret."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production', 'SECRET': ''}, clear=True):
            with pytest.raises(ValueError, match="SECRET and SESSION_MIDDLEWARE_SECRET must be set in production environment"):
                Settings()

    def test_validate_secrets_production_with_secret(self):
        """Test secret validation passes in production with secret."""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production', 
            'SECRET': 'secret123',
            'SESSION_MIDDLEWARE_SECRET': 'session_secret123',
            'CORS_ALLOW_ORIGIN_LIST': 'https://example.com'
        }, clear=True):
            config = Settings()
            assert config.SECRET == "secret123"

    def test_validate_cors_origins_production_with_wildcard(self):
        """Test CORS validation fails in production with wildcard."""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production', 
            'CORS_ALLOW_ORIGIN_LIST': '*',
            'SECRET': 'secret123',
            'SESSION_MIDDLEWARE_SECRET': 'session_secret123'
        }, clear=True):
            with pytest.raises(ValueError, match=r"CORS_ALLOW_ORIGIN_LIST cannot be '\*' in production environment"):
                Settings()

    def test_validate_cors_origins_production_with_specific_origins(self):
        """Test CORS validation passes in production with specific origins."""
        with patch.dict('os.environ', {
            'ENVIRONMENT': 'production', 
            'CORS_ALLOW_ORIGIN_LIST': 'https://example.com',
            'SECRET': 'secret123',
            'SESSION_MIDDLEWARE_SECRET': 'session_secret123'
        }, clear=True):
            config = Settings()
            assert config.CORS_ALLOW_ORIGIN_LIST == "https://example.com"


class TestGetSettings:
    def test_get_settings_singleton(self):
        # Arrange
        # Act
        settings1 = get_settings()
        settings2 = get_settings()
        # Assert
        assert settings1 is settings2
        assert isinstance(settings1, Settings)

    def test_get_settings_with_environment(self):
        # Arrange
        env_vars = {
            "ENVIRONMENT": "test",
            "SECRET": "test_secret"
        }
        # Act
        with patch.dict('os.environ', env_vars, clear=True):
            # Сбрасываем кеш get_settings
            get_settings.cache_clear()
            settings = get_settings()
        # Assert
        assert settings.ENVIRONMENT == "test"
        assert settings.SECRET == "test_secret" 