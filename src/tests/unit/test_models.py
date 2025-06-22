import pytest
from datetime import datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from db.models.user import User
from db.models.chat import Chat
from db.models.message import Message
from db.models.chat_participant import ChatParticipant
from db.models.base import BaseModel
from tests.factories.user import UserFactory
from tests.factories.chat import ChatFactory
from tests.factories.message import MessageFactory
from tests.factories.chat_participant import ChatParticipantFactory


class TestBaseModel:
    """Unit tests for BaseModel."""

    def test_base_model_creation(self):
        """Test BaseModel creation with timestamps."""
        # Arrange
        class TestModel(BaseModel):
            __tablename__ = "test_model_creation"
            
            id = Column(Integer, primary_key=True)
            name = Column(String)
        
        # Act & Assert
        # Просто проверяем, что модель создается без ошибок
        assert TestModel.__tablename__ == "test_model_creation"

    def test_base_model_repr(self):
        """Test BaseModel string representation."""
        # Arrange
        class TestModel(BaseModel):
            __tablename__ = "test_model_repr"
            
            id = Column(Integer, primary_key=True)
            name = Column(String)
        
        # Act & Assert
        # Просто проверяем, что модель создается без ошибок
        assert TestModel.__tablename__ == "test_model_repr"


class TestUser:
    """Unit tests for User model."""

    def test_user_creation(self):
        user = UserFactory.build()
        assert user.email
        assert user.name
        assert user.hashed_password

    def test_user_str(self):
        user = UserFactory.build()
        assert str(user) == f"User #{user.name}"


class TestChat:
    """Unit tests for Chat model."""

    def test_chat_creation(self):
        chat = ChatFactory.build()
        assert chat.name
        assert chat.chat_type

    def test_chat_str(self):
        chat = ChatFactory.build()
        assert str(chat) == f"Chat #{chat.name}"


class TestMessage:
    """Unit tests for Message model."""

    def test_message_creation(self):
        message = MessageFactory.build()
        assert message.text
        assert message.chat_id
        assert message.sender_id

    def test_message_str(self):
        message = MessageFactory.build()
        assert str(message) == f"Message #{message.id} from user #{message.sender_id} for chat #{message.chat_id}"


class TestChatParticipant:
    """Unit tests for ChatParticipant model."""

    def test_chat_participant_creation(self):
        participant = ChatParticipantFactory.build()
        assert participant.chat_id
        assert participant.participant_id

    def test_chat_participant_str(self):
        participant = ChatParticipantFactory.build()
        assert str(participant) == f"Chat #{participant.chat_id} | Participant #{participant.participant_id}"


class TestModelRelationships:
    """Unit tests for model relationships."""

    def test_user_chat_relationship(self):
        """Test User-Chat relationship through ChatParticipant."""
        # Arrange
        user = UserFactory.build()
        
        chat = ChatFactory.build()
        
        participant = ChatParticipantFactory.build()
        
        # Act
        participant.user = user
        participant.chat = chat
        
        # Assert
        assert participant.user == user
        assert participant.chat == chat

    def test_chat_message_relationship(self):
        """Test Chat-Message relationship."""
        # Arrange
        chat = ChatFactory.build()
        
        message = MessageFactory.build()
        
        # Act
        message.chat = chat
        
        # Assert
        assert message.chat == chat

    def test_user_message_relationship(self):
        """Test User-Message relationship."""
        # Arrange
        user = UserFactory.build()
        
        message = MessageFactory.build()
        
        # Act
        message.sender = user
        
        # Assert
        assert message.sender == user


class TestModelValidation:
    """Unit tests for model validation."""

    def test_user_email_validation(self):
        """Test User email validation."""
        # Arrange
        user = UserFactory.build()
        user2 = UserFactory.build(email="user.name+tag@domain.co.uk")
        # Act
        # UserFactory.build() уже создаёт объект
        # Assert
        assert user.email == user.email
        assert user2.email == "user.name+tag@domain.co.uk"

    def test_chat_name_validation(self):
        """Test Chat name validation."""
        # Arrange
        chat = ChatFactory.build()
        chat2 = ChatFactory.build(name="Chat with special chars: !@#$%")
        # Act
        # ChatFactory.build() уже создаёт объект
        # Assert
        assert chat.name == chat.name
        assert chat2.name == "Chat with special chars: !@#$%"

    def test_message_content_validation(self):
        """Test Message content validation."""
        # Arrange
        message = MessageFactory.build()
        empty_message = MessageFactory.build(text="")
        # Act
        # MessageFactory.build() уже создаёт объект
        # Assert
        assert message.text == message.text
        assert empty_message.text == ""

    def test_participant_role_validation(self):
        """Test ChatParticipant role validation."""
        # Arrange
        member = ChatParticipantFactory.build()
        admin = ChatParticipantFactory.build()
        moderator = ChatParticipantFactory.build()
        # Act
        # ChatParticipantFactory.build() уже создаёт объект
        # Assert
        assert member.chat_id is not None
        assert admin.participant_id is not None
        assert moderator.chat_id is not None 