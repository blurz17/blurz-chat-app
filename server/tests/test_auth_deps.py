"""
Unit tests for server/auth/dependencies.py
Tests: BearerToken, AccessTokenBearer, RefreshToken, get_current_user, CheckRoler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAccessTokenBearer:
    """Tests for AccessTokenBearer.verify_token()"""

    def test_access_token_passes_for_non_refresh(self):
        from auth.dependencies import AccessTokenBearer
        bearer = AccessTokenBearer()
        # Should not raise
        bearer.verify_token({"refresh_token": False, "user": {"email": "t@t.com"}})

    def test_access_token_raises_for_refresh_token(self):
        from auth.dependencies import AccessTokenBearer
        from errors import AccessTokenRequired
        bearer = AccessTokenBearer()
        with pytest.raises(AccessTokenRequired):
            bearer.verify_token({"refresh_token": True, "user": {"email": "t@t.com"}})

    def test_access_token_passes_for_none_refresh(self):
        from auth.dependencies import AccessTokenBearer
        bearer = AccessTokenBearer()
        # refresh_token not set — should not raise
        bearer.verify_token({"user": {"email": "t@t.com"}})


class TestRefreshToken:
    """Tests for RefreshToken.verify_token()"""

    def test_refresh_token_passes_for_refresh(self):
        from auth.dependencies import RefreshToken
        bearer = RefreshToken()
        # Should not raise
        bearer.verify_token({"refresh_token": True, "user": {"email": "t@t.com"}})

    def test_refresh_token_raises_for_access_token(self):
        from auth.dependencies import RefreshToken
        from errors import RefreshTokenRequired
        bearer = RefreshToken()
        with pytest.raises(RefreshTokenRequired):
            bearer.verify_token({"refresh_token": False, "user": {"email": "t@t.com"}})


class TestCheckRoler:
    """Tests for CheckRoler class."""

    def test_returns_true_for_allowed_role(self):
        from auth.dependencies import CheckRoler
        user = MagicMock()
        user.is_verified = True
        user.role = "admin"
        checker = CheckRoler(["admin", "moderator"])
        result = checker(user)
        assert result is True

    def test_raises_insufficient_permission_for_wrong_role(self):
        from auth.dependencies import CheckRoler
        from errors import InsufficientPermission
        user = MagicMock()
        user.is_verified = True
        user.role = "user"
        checker = CheckRoler(["admin"])
        with pytest.raises(InsufficientPermission):
            checker(user)

    def test_raises_email_not_verified(self):
        from auth.dependencies import CheckRoler
        from errors import EmailNotVerified
        user = MagicMock()
        user.is_verified = False
        user.role = "admin"
        checker = CheckRoler(["admin"])
        with pytest.raises(EmailNotVerified):
            checker(user)
