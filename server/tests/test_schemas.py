"""
Unit tests for server/users/schema.py
Tests: Pydantic schema validation, field types, defaults
"""
import pytest
import uuid
from datetime import datetime, timezone


class TestOtherUsersSchema:
    """Tests for other_users Pydantic model."""

    def test_valid_data(self):
        from users.schema import other_users
        data = {
            "id": uuid.uuid4(),
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "profile_url": "http://example.com/pic.jpg",
            "created_at": datetime.now(timezone.utc),
        }
        user = other_users(**data)
        assert user.username == "testuser"

    def test_profile_url_optional(self):
        from users.schema import other_users
        data = {
            "id": uuid.uuid4(),
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "created_at": datetime.now(timezone.utc),
        }
        user = other_users(**data)
        assert user.profile_url is None

    def test_created_at_optional(self):
        from users.schema import other_users
        data = {
            "id": uuid.uuid4(),
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        }
        user = other_users(**data)
        assert user.created_at is None

    def test_uses_profile_url_not_picture_url(self):
        """BUG-23 fix verification: field should be profile_url, not picture_url."""
        from users.schema import other_users
        fields = other_users.model_fields
        assert "profile_url" in fields
        assert "picture_url" not in fields


class TestUpdateUserSchema:
    """Tests for Update_User Pydantic model."""

    def test_all_fields_optional(self):
        from users.schema import Update_User
        update = Update_User()
        assert update.username is None
        assert update.first_name is None
        assert update.last_name is None

    def test_partial_update(self):
        from users.schema import Update_User
        update = Update_User(username="newname")
        assert update.username == "newname"
        assert update.first_name is None

    def test_username_max_length(self):
        from users.schema import Update_User
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Update_User(username="a" * 21)

    def test_model_dump_exclude_unset(self):
        """BUG-13 fix verification: exclude_unset should work."""
        from users.schema import Update_User
        update = Update_User(first_name="John")
        dumped = update.model_dump(exclude_unset=True)
        assert "first_name" in dumped
        assert "username" not in dumped
        assert "last_name" not in dumped


class TestProfilePictureResponse:
    """Tests for Profile_Picture_Response schema."""

    def test_valid_response(self):
        from users.schema import Profile_Picture_Response
        resp = Profile_Picture_Response(message="Profile picture is being uploaded")
        assert resp.message == "Profile picture is being uploaded"
