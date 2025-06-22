import pytest
from tests.factories.user import UserFactory
from tests.factories.chat import ChatFactory
from services.auth import AuthService
from services.chat import ChatService

class TestAuthService:
    def test_auth_service_init(self):
        service = AuthService()
        assert isinstance(service, AuthService)

class TestChatService:
    def test_chat_service_init(self):
        service = ChatService()
        assert isinstance(service, ChatService) 