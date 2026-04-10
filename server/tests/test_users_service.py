"""
Unit tests for server/users/service.py
Tests: get_contacts, search_user, update_user, is_username_exist
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetContacts:
    """Tests for get_contacts()"""

    @pytest.mark.asyncio
    async def test_returns_list_of_users(self, mock_session):
        from users.service import get_contacts
        
        user1 = MagicMock()
        user1.is_verified = True
        user2 = MagicMock()
        user2.is_verified = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user1, user2]
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await get_contacts(mock_session)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_users(self, mock_session):
        from users.service import get_contacts
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await get_contacts(mock_session)
        assert result == []


class TestSearchUser:
    """Tests for search_user()"""

    @pytest.mark.asyncio
    async def test_returns_matching_users(self, mock_session):
        from users.service import search_user
        
        user = MagicMock()
        user.username = "john_doe"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [user]
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await search_user("john", mock_session)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_match(self, mock_session):
        from users.service import search_user
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await search_user("nonexistent_query_xyz", mock_session)
        assert result == []


class TestIsUsernameExist:
    """Tests for is_username_exist()"""

    @pytest.mark.asyncio
    async def test_returns_user_when_exists(self, mock_session, sample_user_model):
        from users.service import is_username_exist
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await is_username_exist("testuser", mock_session)
        assert result is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, mock_session):
        from users.service import is_username_exist
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        result = await is_username_exist("unknown_user", mock_session)
        assert result is None


class TestUpdateUser:
    """Tests for update_user()"""

    @pytest.mark.asyncio
    async def test_updates_user_fields(self, mock_session):
        from users.service import update_user
        from users.schema import Update_User
        
        user = MagicMock()
        user.id = uuid.uuid4()
        user.username = "oldname"
        user.first_name = "Old"
        user.last_name = "Name"
        
        # is_username_exist returns None (not taken)
        mock_result_check = MagicMock()
        mock_result_check.scalar_one_or_none.return_value = None
        
        # update query returns the user
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = user
        
        mock_session.execute = AsyncMock(side_effect=[mock_result_check, mock_result_user])
        
        update_data = Update_User(username="newname", first_name="New")
        result = await update_user(str(user.id), mock_session, update_data)
        
        mock_session.commit.assert_called_once()
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_user_not_found(self, mock_session):
        from users.service import update_user
        from users.schema import Update_User
        from errors import UserNotFound
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        update_data = Update_User(first_name="Test")
        with pytest.raises(UserNotFound):
            await update_user(str(uuid.uuid4()), mock_session, update_data)

    @pytest.mark.asyncio
    async def test_raises_user_already_exists_for_taken_username(self, mock_session, sample_user_model):
        from users.service import update_user
        from users.schema import Update_User
        from errors import UserAlreadyExists
        
        # is_username_exist returns existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        update_data = Update_User(username="testuser")
        with pytest.raises(UserAlreadyExists):
            await update_user(str(uuid.uuid4()), mock_session, update_data)

    @pytest.mark.asyncio
    async def test_skips_username_check_when_not_provided(self, mock_session):
        from users.service import update_user
        from users.schema import Update_User
        
        user = MagicMock()
        user.id = uuid.uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        update_data = Update_User(first_name="NewFirst")
        await update_user(str(user.id), mock_session, update_data)
        
        # Should only execute once (the user fetch, not username check)
        assert mock_session.execute.call_count == 1
