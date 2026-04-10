"""
Unit tests for server/db/models.py
Tests: model instantiation, defaults, enums, relationships declarations
"""
import pytest
import uuid
from datetime import datetime


class TestUserModel:
    """Tests for the User SQLModel."""

    def test_user_has_expected_fields(self):
        from db.models import User
        fields = User.model_fields
        expected = ['id', 'username', 'email', 'phone', 'first_name', 'last_name',
                    'profile_url', 'password_hash', 'is_verified']
        for field in expected:
            assert field in fields, f"Missing field: {field}"

    def test_user_default_values(self):
        from db.models import User
        user = User(
            username="test", email="test@test.com", phone="123",
            password_hash="hash123"
        )
        assert user.first_name == "new_user"
        assert user.last_name == "new_user"
        assert user.is_verified is False
        assert user.profile_url is None

    def test_user_id_is_uuid(self):
        from db.models import User
        user = User(
            username="test", email="test@test.com", phone="123",
            password_hash="hash123"
        )
        assert isinstance(user.id, uuid.UUID)

    def test_user_repr(self):
        from db.models import User
        user = User(
            username="john", email="john@test.com", phone="123",
            password_hash="hash123"
        )
        assert "john" in repr(user)


class TestChatModel:
    """Tests for the Chat SQLModel."""

    def test_chat_has_id(self):
        from db.models import Chat
        chat = Chat()
        assert isinstance(chat.id, uuid.UUID)

    def test_chat_repr(self):
        from db.models import Chat
        chat = Chat()
        assert "Chat" in repr(chat)


class TestMessageModel:
    """Tests for the Message SQLModel."""

    def test_message_has_expected_fields(self):
        from db.models import Message
        fields = Message.model_fields
        expected_fields = ['id', 'content', 'file_key', 'file_name', 'sender_id', 'chat_id']
        for field in expected_fields:
            assert field in fields, f"Missing field: {field}"

    def test_message_defaults(self):
        from db.models import Message
        msg = Message(
            sender_id=uuid.uuid4(),
            chat_id=uuid.uuid4()
        )
        assert msg.content is None
        assert msg.file_key is None
        assert msg.file_name is None


class TestEnums:
    """Tests for MessageType and MessageStatus enums."""

    def test_message_type_values(self):
        from db.models import MessageType
        assert MessageType.text == "text"
        assert MessageType.file == "file"

    def test_message_status_values(self):
        from db.models import MessageStatus
        assert MessageStatus.sent == "sent"
        assert MessageStatus.delivered == "delivered"
        assert MessageStatus.read == "read"

    def test_message_type_is_string_enum(self):
        from db.models import MessageType
        assert isinstance(MessageType.text, str)

    def test_message_status_is_string_enum(self):
        from db.models import MessageStatus
        assert isinstance(MessageStatus.sent, str)


class TestChatParticipants:
    """Tests for the ChatParticipants link model."""

    def test_has_expected_fields(self):
        from db.models import ChatParticipants
        fields = ChatParticipants.model_fields
        assert 'chat_id' in fields
        assert 'user_id' in fields
