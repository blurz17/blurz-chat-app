"""
Unit tests for server/errors.py
Tests: exception hierarchy, create_exception_handler, register_error_handlers
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI, status
from fastapi.requests import Request


class TestExceptionHierarchy:
    """Test that all custom exceptions inherit from AppError."""

    def test_all_exceptions_inherit_from_app_error(self):
        from errors import (
            AppError, InvalidToken, TokenExpired, RevokedToken,
            AccessTokenRequired, RefreshTokenRequired, UserAlreadyExists,
            InvalidCredentials, InsufficientPermission, UserNotFound,
            VerificationError, DataNotFound, PasswordAlreadyReset,
            UserAlreadyVerify, EmailNotVerified
        )
        exceptions = [
            InvalidToken, TokenExpired, RevokedToken,
            AccessTokenRequired, RefreshTokenRequired, UserAlreadyExists,
            InvalidCredentials, InsufficientPermission, UserNotFound,
            VerificationError, DataNotFound, PasswordAlreadyReset,
            UserAlreadyVerify, EmailNotVerified
        ]
        for exc_cls in exceptions:
            assert issubclass(exc_cls, AppError), f"{exc_cls.__name__} does not inherit from AppError"

    def test_token_expired_inherits_from_invalid_token(self):
        from errors import TokenExpired, InvalidToken
        assert issubclass(TokenExpired, InvalidToken)

    def test_can_raise_and_catch_app_error(self):
        from errors import AppError, UserNotFound
        with pytest.raises(AppError):
            raise UserNotFound()

    def test_can_instantiate_all_exceptions(self):
        from errors import (
            InvalidToken, TokenExpired, RevokedToken,
            AccessTokenRequired, RefreshTokenRequired, UserAlreadyExists,
            InvalidCredentials, InsufficientPermission, UserNotFound,
            VerificationError, DataNotFound, PasswordAlreadyReset,
            UserAlreadyVerify, EmailNotVerified
        )
        exceptions = [
            InvalidToken, TokenExpired, RevokedToken,
            AccessTokenRequired, RefreshTokenRequired, UserAlreadyExists,
            InvalidCredentials, InsufficientPermission, UserNotFound,
            VerificationError, DataNotFound, PasswordAlreadyReset,
            UserAlreadyVerify, EmailNotVerified
        ]
        for exc_cls in exceptions:
            exc = exc_cls()
            assert isinstance(exc, Exception)


class TestCreateExceptionHandler:
    """Test create_exception_handler factory."""

    @pytest.mark.asyncio
    async def test_returns_correct_status_code(self):
        from errors import create_exception_handler, UserNotFound
        handler = create_exception_handler(404, {"message": "Not found"})
        request = MagicMock(spec=Request)
        response = await handler(request, UserNotFound())
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_correct_body(self):
        from errors import create_exception_handler, UserNotFound
        detail = {"message": "User not found", "error_code": "not_found"}
        handler = create_exception_handler(404, detail)
        request = MagicMock(spec=Request)
        response = await handler(request, UserNotFound())
        import json
        body = json.loads(response.body)
        assert body["detail"]["message"] == "User not found"
        assert body["detail"]["error_code"] == "not_found"
        assert body["status_code"] == 404

    @pytest.mark.asyncio
    async def test_handler_status_code_matches_parameter(self):
        from errors import create_exception_handler, AppError
        for code in [400, 401, 403, 404, 500]:
            handler = create_exception_handler(code, {"msg": "test"})
            request = MagicMock(spec=Request)
            response = await handler(request, AppError())
            assert response.status_code == code


class TestRegisterErrorHandlers:
    """Test that register_error_handlers adds handlers to the app."""

    def test_registers_handlers_without_error(self):
        from errors import register_error_handlers
        app = FastAPI()
        # Should not raise
        register_error_handlers(app)

    def test_no_book_or_tag_related_handlers(self):
        """Per user request: all book/tag related code should be removed."""
        from errors import register_error_handlers
        import errors
        # Verify BookNotFound, TagNotFound, TagAlreadyExists don't exist
        assert not hasattr(errors, 'BookNotFound')
        assert not hasattr(errors, 'TagNotFound')
        assert not hasattr(errors, 'TagAlreadyExists')
