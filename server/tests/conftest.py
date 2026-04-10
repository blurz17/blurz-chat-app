"""
conftest.py — Shared fixtures for all tests.
Uses mocks/fakes for DB, Redis, and external services so tests run
without any infrastructure.
"""
import sys
import os
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import fakeredis.aioredis

# ── Ensure the server package is importable ──────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Patch heavy/env-dependent modules BEFORE they are imported ───────
# Patch config before anything reads .env
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///test.db")
os.environ.setdefault("jwt_secret", "test-jwt-secret-key-12345")
os.environ.setdefault("jwt_algorithm", "HS256")
os.environ.setdefault("refresh_token_expiary", "7")
os.environ.setdefault("access_token_expiary", "30")
os.environ.setdefault("Redis_Url", "redis://localhost:6379/0")
os.environ.setdefault("MAIL_USERNAME", "test@test.com")
os.environ.setdefault("MAIL_PASSWORD", "testpass")
os.environ.setdefault("MAIL_FROM", "test@test.com")
os.environ.setdefault("MAIL_PORT", "587")
os.environ.setdefault("MAIL_SERVER", "smtp.test.com")
os.environ.setdefault("MAIL_FROM_NAME", "Test")
os.environ.setdefault("domain", "http://localhost:3000")
os.environ.setdefault("password_secrete_reset", "test-reset-secret")
os.environ.setdefault("profile_picture_path", "./test_media")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # Fast for tests


# ── Event loop fixture ───────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Fake Redis ───────────────────────────────────────────
@pytest.fixture
def fake_redis():
    """Return a fakeredis async client."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


# ── Sample user data ─────────────────────────────────────
@pytest.fixture
def sample_user_data():
    """A raw dict matching Create_User schema."""
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "phone": "+1234567890",
        "first_name": "Test",
        "last_name": "User",
        "password": "securepassword123",
        "profile_picture": None,
    }


@pytest.fixture
def sample_user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_user_model(sample_user_id):
    """Mimics a db.models.User ORM object with attributes."""
    user = MagicMock()
    user.id = sample_user_id
    user.username = "testuser"
    user.email = "testuser@example.com"
    user.phone = "+1234567890"
    user.first_name = "Test"
    user.last_name = "User"
    user.profile_url = None
    user.password_hash = "$2b$04$fakehashedpassword"
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_session():
    """Mock AsyncSession for unit tests."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session
