"""
Unit tests for server/middleware.py
Tests: CORS configuration, middleware setup
"""
import pytest
from fastapi import FastAPI
from unittest.mock import patch


class TestMiddlewareSetup:
    """Tests for custome_simple_middle()."""

    def test_middleware_registers_without_error(self):
        from middleware import custome_simple_middle
        app = FastAPI()
        # Should not raise
        custome_simple_middle(app)

    def test_cors_does_not_use_wildcard_with_credentials(self):
        """BUG-14 fix verification: CORS origins should not be ['*'] when credentials are enabled."""
        from middleware import custome_simple_middle
        app = FastAPI()
        custome_simple_middle(app)
        
        # Check that the CORS middleware was added with specific origins
        for mw in app.user_middleware:
            mw_cls = mw.cls if hasattr(mw, 'cls') else None
            if mw_cls and 'CORSMiddleware' in str(mw_cls):
                kwargs = mw.kwargs if hasattr(mw, 'kwargs') else {}
                origins = kwargs.get('allow_origins', [])
                if kwargs.get('allow_credentials', False):
                    assert origins != ['*'], "CORS wildcard with credentials is invalid"
                break
