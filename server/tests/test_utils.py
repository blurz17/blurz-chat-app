"""
Unit tests for server/utils.py
Tests: password hashing, token creation/decoding, CreationSafeLink
"""
import pytest
import time
from datetime import timedelta


class TestGenerateHashedPassword:
    """Tests for generate_hashed_password()"""

    def test_returns_string(self):
        from utils import generate_hashed_password
        result = generate_hashed_password("mypassword")
        assert isinstance(result, str)

    def test_hashed_password_starts_with_bcrypt_prefix(self):
        from utils import generate_hashed_password
        result = generate_hashed_password("mypassword")
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_different_passwords_produce_different_hashes(self):
        from utils import generate_hashed_password
        h1 = generate_hashed_password("password1")
        h2 = generate_hashed_password("password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes_due_to_salt(self):
        from utils import generate_hashed_password
        h1 = generate_hashed_password("samepassword")
        h2 = generate_hashed_password("samepassword")
        assert h1 != h2  # Salt makes them different

    def test_truncates_password_at_72_bytes(self):
        from utils import generate_hashed_password, verify_password
        long_pw = "a" * 100
        hashed = generate_hashed_password(long_pw)
        # bcrypt only uses first 72 bytes
        assert verify_password(long_pw[:72], hashed)

    def test_handles_empty_string(self):
        from utils import generate_hashed_password
        result = generate_hashed_password("")
        assert isinstance(result, str)

    def test_handles_unicode_password(self):
        from utils import generate_hashed_password
        result = generate_hashed_password("пароль密码🔐")
        assert isinstance(result, str)


class TestVerifyPassword:
    """Tests for verify_password()"""

    def test_correct_password_returns_true(self):
        from utils import generate_hashed_password, verify_password
        hashed = generate_hashed_password("correctpass")
        assert verify_password("correctpass", hashed) is True

    def test_wrong_password_returns_false(self):
        from utils import generate_hashed_password, verify_password
        hashed = generate_hashed_password("correctpass")
        assert verify_password("wrongpass", hashed) is False

    def test_empty_password_against_hash(self):
        from utils import generate_hashed_password, verify_password
        hashed = generate_hashed_password("somepass")
        assert verify_password("", hashed) is False


class TestAccessToken:
    """Tests for access_token()"""

    def test_creates_token_string(self):
        from utils import access_token
        token = access_token({"email": "test@test.com", "id": "123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_data(self):
        from utils import access_token, decode_token
        user_data = {"email": "test@test.com", "id": "123"}
        token = access_token(user_data)
        decoded = decode_token(token)
        assert decoded["user"]["email"] == "test@test.com"
        assert decoded["user"]["id"] == "123"

    def test_refresh_token_flag_false_by_default(self):
        from utils import access_token, decode_token
        token = access_token({"email": "t@t.com"})
        decoded = decode_token(token)
        assert decoded["refresh_token"] is False

    def test_refresh_token_flag_true(self):
        from utils import access_token, decode_token
        token = access_token({"email": "t@t.com"}, refresh=True)
        decoded = decode_token(token)
        assert decoded["refresh_token"] is True

    def test_custom_expiry(self):
        from utils import access_token, decode_token
        custom = timedelta(hours=2)
        token = access_token({"email": "t@t.com"}, expire=custom)
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_token_has_jti(self):
        from utils import access_token, decode_token
        token = access_token({"email": "t@t.com"})
        decoded = decode_token(token)
        assert "jti" in decoded
        # jti should be a valid UUID string
        import uuid
        uuid.UUID(decoded["jti"])  # raises if invalid

    def test_two_tokens_have_different_jti(self):
        from utils import access_token, decode_token
        t1 = access_token({"email": "t@t.com"})
        t2 = access_token({"email": "t@t.com"})
        d1 = decode_token(t1)
        d2 = decode_token(t2)
        assert d1["jti"] != d2["jti"]


class TestDecodeToken:
    """Tests for decode_token()"""

    def test_decode_valid_token(self):
        from utils import access_token, decode_token
        token = access_token({"email": "test@test.com"})
        result = decode_token(token)
        assert result is not None
        assert result["user"]["email"] == "test@test.com"

    def test_decode_invalid_token_raises(self):
        from utils import decode_token
        from errors import InvalidToken
        with pytest.raises(InvalidToken):
            decode_token("not.a.valid.token")

    def test_decode_expired_token_raises(self):
        from utils import access_token, decode_token
        from errors import TokenExpired
        token = access_token({"email": "t@t.com"}, expire=timedelta(seconds=-1))
        with pytest.raises(TokenExpired):
            decode_token(token)

    def test_decode_tampered_token_raises(self):
        from utils import access_token, decode_token
        from errors import InvalidToken
        token = access_token({"email": "t@t.com"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidToken):
            decode_token(tampered)


class TestCreationSafeLink:
    """Tests for CreationSafeLink class"""

    def test_create_safe_url_returns_string(self):
        from utils import CreationSafeLink
        link = CreationSafeLink("secret", "salt")
        token = link.create_safe_url({"email": "test@test.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_safe_url_adds_token_id(self):
        from utils import CreationSafeLink
        link = CreationSafeLink("secret", "salt")
        token = link.create_safe_url({"email": "test@test.com"})
        data = link.de_serializ_url(token, max_age=60)
        assert "token_id" in data

    def test_de_serializ_url_returns_data(self):
        from utils import CreationSafeLink
        link = CreationSafeLink("secret", "salt")
        original = {"email": "test@test.com", "action": "verify"}
        token = link.create_safe_url(original)
        result = link.de_serializ_url(token, max_age=60)
        assert result is not None
        assert result["email"] == "test@test.com"
        assert result["action"] == "verify"

    def test_de_serializ_url_expired_raises(self):
        import time
        from utils import CreationSafeLink
        from errors import TokenExpired
        link = CreationSafeLink("secret", "salt")
        token = link.create_safe_url({"email": "test@test.com"})
        time.sleep(1.1)  # Wait just over 1 second
        with pytest.raises(TokenExpired):
            link.de_serializ_url(token, max_age=1)  # 1 second max age, token is ~1.1s old

    def test_de_serializ_url_invalid_token_raises(self):
        from utils import CreationSafeLink
        from errors import InvalidToken
        link = CreationSafeLink("secret", "salt")
        with pytest.raises(InvalidToken):
            link.de_serializ_url("totally-invalid-token", max_age=60)

    def test_de_serializ_url_wrong_secret_raises(self):
        from utils import CreationSafeLink
        from errors import InvalidToken
        link1 = CreationSafeLink("secret1", "salt")
        link2 = CreationSafeLink("secret2", "salt")
        token = link1.create_safe_url({"email": "t@t.com"})
        with pytest.raises(InvalidToken):
            link2.de_serializ_url(token, max_age=60)

    def test_create_safe_url_with_none_data(self):
        from utils import CreationSafeLink
        link = CreationSafeLink("secret", "salt")
        token = link.create_safe_url(None)
        result = link.de_serializ_url(token, max_age=60)
        assert "token_id" in result

    def test_different_calls_produce_different_token_ids(self):
        from utils import CreationSafeLink
        link = CreationSafeLink("secret", "salt")
        token1 = link.create_safe_url({"a": 1})
        token2 = link.create_safe_url({"a": 1})
        d1 = link.de_serializ_url(token1, max_age=60)
        d2 = link.de_serializ_url(token2, max_age=60)
        assert d1["token_id"] != d2["token_id"]
