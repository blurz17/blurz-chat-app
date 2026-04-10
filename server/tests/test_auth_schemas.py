"""
Tests for auth/schema.py
Tests: Pydantic schema validation, required fields, constraints
"""
import pytest
import uuid
from datetime import datetime, timezone


class TestUserSchema:
    """Tests for the User response schema."""

    def test_valid_user(self):
        from auth.schema import User
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@test.com",
            phone="+1234567890",
            first_name="Test",
            last_name="User",
            is_verified=True,
        )
        assert user.username == "testuser"
        assert user.is_verified is True

    def test_optional_fields_default_to_none(self):
        from auth.schema import User
        user = User(
            id=uuid.uuid4(),
            username="testuser",
            email="test@test.com",
            phone="+1234567890",
            first_name="Test",
            last_name="User",
            is_verified=False,
        )
        assert user.profile_url is None
        assert user.created_at is None
        assert user.updated_at is None

    def test_username_max_length(self):
        from auth.schema import User
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            User(
                id=uuid.uuid4(),
                username="a" * 21,  # exceeds 20
                email="test@test.com",
                phone="+1234567890",
                first_name="Test",
                last_name="User",
                is_verified=False,
            )


class TestCreateUserSchema:
    """Tests for Create_User schema."""

    def test_valid_create_user(self):
        from auth.schema import Create_User
        user = Create_User(
            username="newuser",
            email="new@test.com",
            phone="+1234567890",
            first_name="New",
            last_name="User",
            password="securepass123",
            profile_picture=None,
        )
        assert user.username == "newuser"

    def test_password_min_length(self):
        from auth.schema import Create_User
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Create_User(
                username="user",
                email="test@test.com",
                phone="+123",
                first_name="T",
                last_name="U",
                password="short",  # < 8 chars
                profile_picture=None,
            )

    def test_password_max_length(self):
        from auth.schema import Create_User
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Create_User(
                username="user",
                email="test@test.com",
                phone="+123",
                first_name="T",
                last_name="U",
                password="a" * 73,  # > 72 chars
                profile_picture=None,
            )


class TestLoginUserSchema:
    """Tests for Login_User schema."""

    def test_valid_login(self):
        from auth.schema import Login_User
        login = Login_User(
            email="test@test.com",
            password="mypassword123",
        )
        assert login.email == "test@test.com"

    def test_phone_optional(self):
        from auth.schema import Login_User
        login = Login_User(
            email="test@test.com",
            password="mypassword123",
        )
        assert login.phone is None

    def test_password_optional(self):
        from auth.schema import Login_User
        login = Login_User(
            email="test@test.com",
            password=None,
        )
        assert login.password is None


class TestPasswordResetSchema:
    """Tests for Password_Reset schema."""

    def test_valid_email(self):
        from auth.schema import Password_Reset
        pr = Password_Reset(email="test@test.com")
        assert pr.email == "test@test.com"


class TestPasswordResetConfirmSchema:
    """Tests for Password_reset_Confirm schema."""

    def test_valid_passwords(self):
        from auth.schema import Password_reset_Confirm
        prc = Password_reset_Confirm(
            new_password="newpassword123",
            confirm_password="newpassword123"
        )
        assert prc.new_password == prc.confirm_password

    def test_min_length_validation(self):
        from auth.schema import Password_reset_Confirm
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Password_reset_Confirm(
                new_password="short",
                confirm_password="short"
            )


class TestChangePasswordSchema:
    """Tests for ChangePassword schema."""

    def test_valid_change_password(self):
        from auth.schema import ChangePassword
        cp = ChangePassword(
            current_password="oldpassword",
            new_password="newpassword123"
        )
        assert cp.current_password == "oldpassword"

    def test_new_password_min_length(self):
        from auth.schema import ChangePassword
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChangePassword(
                current_password="old",
                new_password="short"  # < 8
            )


class TestUserActivationSchema:
    """Tests for User_Activation schema."""

    def test_field_name_is_verified(self):
        """BUG-22 fix verification: field name should be is_verified, not is_verifed."""
        from auth.schema import User_Activation
        fields = User_Activation.model_fields
        assert "is_verified" in fields
        assert "is_verifed" not in fields, "Typo 'is_verifed' should be fixed to 'is_verified'"
