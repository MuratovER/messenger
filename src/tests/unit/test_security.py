import pytest
from datetime import datetime, timedelta
from tests.utils import TEST_USER_PASSWORD, TEST_USER_WEAK_PASSWORD
from tests.factories.user import UserFactory
from tests.factories.message import MessageFactory
from utils.security import SecurityUtils, TokenBlacklist, security_utils, token_blacklist


class TestSecurityUtils:
    """Unit tests for SecurityUtils class."""

    def test_hash_password(self):
        """Test password hashing."""
        # Arrange
        password = UserFactory.build().hashed_password
        # Act
        hashed = SecurityUtils.hash_password(password)
        # Assert
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        # Arrange
        password = UserFactory.build().hashed_password
        # Act
        hashed = SecurityUtils.hash_password(password)
        result = SecurityUtils.verify_password(password, hashed)
        # Assert
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        # Arrange
        password = UserFactory.build().hashed_password
        wrong_password = UserFactory.build().hashed_password
        hashed = SecurityUtils.hash_password(password)
        # Act
        result = SecurityUtils.verify_password(wrong_password, hashed)
        # Assert
        assert result is False

    def test_generate_secure_token(self):
        """Test secure token generation."""
        # Arrange
        # 32 — стандартная длина для токена (256 бит)
        # Act
        token = SecurityUtils.generate_secure_token(32)
        # Assert
        assert len(token) == 32
        assert token.isalnum()
        assert token != SecurityUtils.generate_secure_token(32)  # Should be unique

    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        # Arrange
        # 16 — тестируем произвольную длину
        # Act
        token = SecurityUtils.generate_secure_token(16)
        # Assert
        assert len(token) == 16
        assert token.isalnum()

    def test_generate_api_key(self):
        """Test API key generation."""
        # Act
        api_key = SecurityUtils.generate_api_key()
        # Assert
        assert api_key.startswith("sk_")
        assert len(api_key) > 35  # Минимальная длина для безопасности
        assert api_key != SecurityUtils.generate_api_key()  # Should be unique

    def test_hash_data(self):
        """Test data hashing."""
        # Arrange
        data = MessageFactory.build().text
        # Act
        hashed = SecurityUtils.hash_data(data)
        # Assert
        assert len(hashed) == 64  # SHA-256 produces 64 character hex string
        assert hashed.isalnum()
        assert SecurityUtils.hash_data(data) == hashed  # Should be deterministic

    def test_validate_password_strength_strong(self):
        """Test password strength validation with strong password."""
        # Arrange
        password = "StrongPass123!"
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is True
        assert message == "Password is strong"

    def test_validate_password_strength_too_short(self):
        """Test password strength validation with too short password."""
        # Arrange
        password = "Short1!"  # 7 символов, меньше минимального порога (обычно 8)
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "at least" in message

    def test_validate_password_strength_too_long(self):
        """Test password strength validation with too long password."""
        # Arrange
        password = "A" * 129 + "1!"  # 129+2=131 символ, больше лимита (128)
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "no more than" in message

    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase."""
        # Arrange
        password = "strongpass123!"  # Нет заглавных
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "uppercase" in message

    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase."""
        # Arrange
        password = "STRONGPASS123!"  # Нет строчных
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "lowercase" in message

    def test_validate_password_strength_no_digit(self):
        """Test password strength validation without digit."""
        # Arrange
        password = "StrongPass!"  # Нет цифры
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "digit" in message

    def test_validate_password_strength_no_special_char(self):
        """Test password strength validation without special character."""
        # Arrange
        password = "StrongPass123"  # Нет спецсимвола
        # Act
        is_valid, message = SecurityUtils.validate_password_strength(password)
        # Assert
        assert is_valid is False
        assert "special character" in message

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Arrange
        dangerous_input = f'<script>{MessageFactory.build().text}</script>'
        # Act
        sanitized = SecurityUtils.sanitize_input(dangerous_input)
        # Assert
        assert "&lt;" in sanitized
        assert "&gt;" in sanitized
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized

    def test_sanitize_input_safe(self):
        """Test input sanitization with safe input."""
        # Arrange
        safe_input = MessageFactory.build().text
        # Act
        sanitized = SecurityUtils.sanitize_input(safe_input)
        # Assert
        assert sanitized == safe_input

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        # Arrange
        valid_emails = [UserFactory.build().email for _ in range(4)]
        # Act & Assert
        for email in valid_emails:
            assert SecurityUtils.validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        # Arrange
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user@example..com"
        ]
        # Act & Assert
        for email in invalid_emails:
            assert SecurityUtils.validate_email(email) is False


class TestTokenBlacklist:
    """Unit tests for TokenBlacklist class."""

    def test_add_token(self):
        """Test adding token to blacklist."""
        # Arrange
        blacklist = TokenBlacklist()
        token = "test_token"
        expires_at = datetime.now() + timedelta(hours=1)
        # Act
        blacklist.add_token(token, expires_at)
        # Assert
        assert token in blacklist._blacklisted_tokens
        assert blacklist._token_expiry[token] == expires_at

    def test_is_blacklisted_true(self):
        """Test checking if token is blacklisted."""
        # Arrange
        blacklist = TokenBlacklist()
        token = "test_token"
        expires_at = datetime.now() + timedelta(hours=1)
        blacklist.add_token(token, expires_at)
        # Act
        result = blacklist.is_blacklisted(token)
        # Assert
        assert result is True

    def test_is_blacklisted_false(self):
        """Test checking if token is not blacklisted."""
        # Arrange
        blacklist = TokenBlacklist()
        token = "test_token"
        # Act
        result = blacklist.is_blacklisted(token)
        # Assert
        assert result is False

    def test_is_blacklisted_expired(self):
        """Test checking if expired token is automatically removed."""
        # Arrange
        blacklist = TokenBlacklist()
        token = "test_token"
        expires_at = datetime.now() - timedelta(hours=1)  # Expired
        blacklist.add_token(token, expires_at)
        # Act
        result = blacklist.is_blacklisted(token)
        # Assert
        assert result is False
        assert token not in blacklist._blacklisted_tokens
        assert token not in blacklist._token_expiry

    def test_cleanup_expired(self):
        """Test cleanup of expired tokens."""
        # Arrange
        blacklist = TokenBlacklist()
        expired_token = "expired_token"
        expired_at = datetime.now() - timedelta(hours=1)
        blacklist.add_token(expired_token, expired_at)
        valid_token = "valid_token"
        valid_at = datetime.now() + timedelta(hours=1)
        blacklist.add_token(valid_token, valid_at)
        # Act
        blacklist.cleanup_expired()
        # Assert
        assert expired_token not in blacklist._blacklisted_tokens
        assert expired_token not in blacklist._token_expiry
        assert valid_token in blacklist._blacklisted_tokens
        assert valid_token in blacklist._token_expiry


class TestGlobalInstances:
    """Unit tests for global instances."""

    def test_security_utils_instance(self):
        """Test that security_utils is an instance of SecurityUtils."""
        # Act & Assert
        assert isinstance(security_utils, SecurityUtils)

    def test_token_blacklist_instance(self):
        """Test that token_blacklist is an instance of TokenBlacklist."""
        # Act & Assert
        assert isinstance(token_blacklist, TokenBlacklist)


class TestDecorators:
    """Unit tests for decorators."""

    def test_require_strong_password_decorator(self):
        """Test require_strong_password decorator."""
        # Arrange
        from utils.security import require_strong_password
        
        @require_strong_password
        def test_function():
            return "success"
        
        # Act
        result = test_function()
        # Assert
        assert result == "success"

    def test_sanitize_user_input_decorator(self):
        """Test sanitize_user_input decorator."""
        # Arrange
        from utils.security import sanitize_user_input
        
        @sanitize_user_input
        def test_function():
            return "success"
        
        # Act
        result = test_function()
        # Assert
        assert result == "success" 