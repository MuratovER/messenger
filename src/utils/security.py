import hashlib
import secrets
import string
from datetime import datetime, timedelta

from passlib.context import CryptContext
from loguru import logger

from core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities for the application."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key."""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data using SHA-256."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < settings().PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings().PASSWORD_MIN_LENGTH} characters long"
        
        if len(password) > settings().PASSWORD_MAX_LENGTH:
            return False, f"Password must be no more than {settings().PASSWORD_MAX_LENGTH} characters long"
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent XSS."""
        # Basic XSS prevention - replace & first to avoid double encoding
        dangerous_chars = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, replacement in dangerous_chars.items():
            text = text.replace(char, replacement)
        
        return text
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        
        # Check for double dots
        if '..' in email:
            return False
            
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class TokenBlacklist:
    """Simple in-memory token blacklist (use Redis in production)."""
    
    def __init__(self):
        self._blacklisted_tokens: set[str] = set()
        self._token_expiry: dict[str, datetime] = {}
    
    def add_token(self, token: str, expires_at: datetime):
        """Add token to blacklist."""
        self._blacklisted_tokens.add(token)
        self._token_expiry[token] = expires_at
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        if token not in self._blacklisted_tokens:
            return False
        
        # Check if token has expired
        if datetime.now() > self._token_expiry[token]:
            self._blacklisted_tokens.remove(token)
            del self._token_expiry[token]
            return False
        
        return True
    
    def cleanup_expired(self):
        """Clean up expired tokens."""
        now = datetime.now()
        expired_tokens = [
            token for token, expiry in self._token_expiry.items()
            if now > expiry
        ]
        
        for token in expired_tokens:
            self._blacklisted_tokens.remove(token)
            del self._token_expiry[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired blacklisted tokens")


# Global instances
security_utils = SecurityUtils()
token_blacklist = TokenBlacklist()


def require_strong_password(func):
    """Decorator to require strong password validation."""
    def wrapper(*args, **kwargs):
        # This would be used in password validation endpoints
        # Implementation depends on specific use case
        return func(*args, **kwargs)
    return wrapper


def sanitize_user_input(func):
    """Decorator to sanitize user input."""
    def wrapper(*args, **kwargs):
        # This would be used in endpoints that accept user input
        # Implementation depends on specific use case
        return func(*args, **kwargs)
    return wrapper 