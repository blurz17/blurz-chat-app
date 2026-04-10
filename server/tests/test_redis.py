"""
Unit tests for server/db/redis.py
Tests: add_to_blacklist, check_blacklist using fakeredis
"""
import pytest
from unittest.mock import patch


class TestRedisBlacklist:
    """Tests for Redis blacklist operations using fakeredis."""

    @pytest.mark.asyncio
    async def test_add_to_blacklist_success(self, fake_redis):
        with patch("db.redis.Token_Blacklist", fake_redis):
            from db.redis import add_to_blacklist
            result = await add_to_blacklist("test-jti-123", exp=60)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_blacklist_returns_true_after_add(self, fake_redis):
        with patch("db.redis.Token_Blacklist", fake_redis):
            from db.redis import add_to_blacklist, check_blacklist
            await add_to_blacklist("blacklisted-jti", exp=60)
            result = await check_blacklist("blacklisted-jti")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_blacklist_returns_false_for_unknown(self, fake_redis):
        with patch("db.redis.Token_Blacklist", fake_redis):
            from db.redis import check_blacklist
            result = await check_blacklist("never-added-jti")
            assert result is False

    @pytest.mark.asyncio
    async def test_add_multiple_tokens(self, fake_redis):
        with patch("db.redis.Token_Blacklist", fake_redis):
            from db.redis import add_to_blacklist, check_blacklist
            
            for i in range(5):
                await add_to_blacklist(f"token-{i}", exp=60)
            
            for i in range(5):
                result = await check_blacklist(f"token-{i}")
                assert result is True

    @pytest.mark.asyncio
    async def test_default_expiry(self, fake_redis):
        """Test that tokens are added with default expiry."""
        with patch("db.redis.Token_Blacklist", fake_redis):
            from db.redis import add_to_blacklist
            result = await add_to_blacklist("default-exp-jti")
            assert result is True


class TestRedisConnectionHandling:
    """Tests for Redis connection error handling."""

    @pytest.mark.asyncio
    async def test_check_blacklist_returns_false_on_connection_error(self):
        """When Redis is down, check_blacklist should return False."""
        from unittest.mock import AsyncMock
        from redis.exceptions import ConnectionError
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Connection refused"))
        
        with patch("db.redis.Token_Blacklist", mock_redis):
            from db.redis import check_blacklist
            result = await check_blacklist("any-jti")
            assert result is False

    @pytest.mark.asyncio
    async def test_add_to_blacklist_returns_false_on_connection_error(self):
        """When Redis is down, add_to_blacklist should return False."""
        from unittest.mock import AsyncMock
        from redis.exceptions import ConnectionError
        
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(side_effect=ConnectionError("Connection refused"))
        
        with patch("db.redis.Token_Blacklist", mock_redis):
            from db.redis import add_to_blacklist
            result = await add_to_blacklist("any-jti")
            assert result is False
