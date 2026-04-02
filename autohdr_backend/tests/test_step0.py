"""Tests for Step 0: Session Management."""

import json
import os
import tempfile
import pytest
import responses

from config.settings import Settings
from steps import step0_session
from models.schemas import SessionRecord, QuotaRecord


@pytest.fixture
def temp_settings():
    """Create settings with temp files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Settings(
            base_url="https://www.autohdr.com",
            cookie="env_cookie",
            user_agent="TestAgent/1.0",
            output_dir=os.path.join(tmpdir, "output"),
            quota_file=os.path.join(tmpdir, "quota.json"),
            sessions_file=os.path.join(tmpdir, "sessions.json"),
            user_id="env_user_id",
            email="env@test.com",
            firstname="EnvFirst",
            lastname="EnvLast",
            limit_count=100,
            limit_file=10,
        )


@pytest.fixture
def sample_session_api_response():
    """Sample /api/auth/session response."""
    return {
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "image": "https://example.com/photo.jpg",
            "id": 95654,
            "current_credit_balance": 29,
            "first_name": "Test",
            "last_name": "User",
            "creation_date_utc": "2026-03-26T05:58:15",
            "is_admin": False,
        },
        "expires": "2099-05-01T10:30:14.880Z",
    }


class TestSessionRecord:
    """Tests for SessionRecord dataclass."""

    def test_not_expired(self):
        """Should return False for future expiry date."""
        session = SessionRecord(
            cookie="c", email="e", user_id="1",
            firstname="F", lastname="L",
            expires="2099-12-31T23:59:59.000Z",
        )
        assert session.is_expired() is False

    def test_expired(self):
        """Should return True for past expiry date."""
        session = SessionRecord(
            cookie="c", email="e", user_id="1",
            firstname="F", lastname="L",
            expires="2020-01-01T00:00:00.000Z",
        )
        assert session.is_expired() is True

    def test_invalid_expires(self):
        """Should return True for invalid expiry string."""
        session = SessionRecord(
            cookie="c", email="e", user_id="1",
            firstname="F", lastname="L",
            expires="invalid",
        )
        assert session.is_expired() is True

    def test_to_dict_and_from_dict(self):
        """Should roundtrip through dict serialization."""
        original = SessionRecord(
            cookie="cookie_val", email="test@test.com",
            user_id="123", firstname="First", lastname="Last",
            expires="2099-12-31T00:00:00Z",
        )
        d = original.to_dict()
        restored = SessionRecord.from_dict(d)
        assert restored.email == original.email
        assert restored.user_id == original.user_id


class TestLoadSaveSessions:
    """Tests for session file I/O."""

    def test_load_nonexistent(self):
        """Should return empty list for nonexistent file."""
        result = step0_session._load_sessions("/nonexistent.json")
        assert result == []

    def test_save_and_load(self):
        """Should save and load sessions correctly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            records = [{"email": "test@test.com", "cookie": "c"}]
            step0_session._save_sessions(path, records)
            loaded = step0_session._load_sessions(path)
            assert len(loaded) == 1
            assert loaded[0]["email"] == "test@test.com"
        finally:
            os.unlink(path)


class TestFindSessionByEmail:
    """Tests for _find_session_by_email."""

    def test_found(self):
        """Should find session by email."""
        records = [
            {"email": "a@test.com", "cookie": "ca",
             "user_id": "1", "firstname": "A", "lastname": "A", "expires": "2099-01-01T00:00:00Z"},
            {"email": "b@test.com", "cookie": "cb",
             "user_id": "2", "firstname": "B", "lastname": "B", "expires": "2099-01-01T00:00:00Z"},
        ]
        result = step0_session._find_session_by_email(records, "b@test.com")
        assert result is not None
        assert result.user_id == "2"

    def test_not_found(self):
        """Should return None when email not found."""
        records = [{"email": "a@test.com", "cookie": "c",
                     "user_id": "1", "firstname": "A", "lastname": "A", "expires": ""}]
        result = step0_session._find_session_by_email(records, "missing@test.com")
        assert result is None


class TestUpdateSessionInRecords:
    """Tests for _update_session_in_records."""

    def test_update_existing(self):
        """Should update existing session by email."""
        records = [{"email": "a@t.com", "cookie": "old"}]
        session = SessionRecord(
            cookie="new", email="a@t.com", user_id="1",
            firstname="F", lastname="L", expires=""
        )
        result = step0_session._update_session_in_records(records, session)
        assert result[0]["cookie"] == "new"

    def test_insert_new(self):
        """Should insert new session when email not found."""
        records = []
        session = SessionRecord(
            cookie="c", email="new@t.com", user_id="1",
            firstname="F", lastname="L", expires=""
        )
        result = step0_session._update_session_in_records(records, session)
        assert len(result) == 1
        assert result[0]["email"] == "new@t.com"


class TestInitQuotaForEmail:
    """Tests for _init_quota_for_email."""

    def test_creates_new_quota(self):
        """Should create quota record for new email."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            step0_session._init_quota_for_email(path, "new@t.com", 0, 0)
            with open(path, "r") as f:
                records = json.load(f)
            assert len(records) == 1
            assert records[0]["email"] == "new@t.com"
            assert records[0]["count"] == 0
        finally:
            os.unlink(path)

    def test_skips_existing(self):
        """Should not duplicate quota for existing email."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump([{"email": "exists@t.com", "unique_str": [],
                        "count": 5, "limit_count": 100, "limit_file": 10}], f)
            path = f.name
        try:
            step0_session._init_quota_for_email(path, "exists@t.com", 0, 0)
            with open(path, "r") as f:
                records = json.load(f)
            assert len(records) == 1
            assert records[0]["count"] == 5  # Unchanged
        finally:
            os.unlink(path)


class TestEnsureDirectories:
    """Tests for _ensure_directories."""

    def test_creates_dirs(self):
        """Should create output_dir and parent dirs for JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(
                output_dir=os.path.join(tmpdir, "out", "subdir"),
                quota_file=os.path.join(tmpdir, "data", "quota.json"),
                sessions_file=os.path.join(tmpdir, "data", "sessions.json"),
            )
            step0_session._ensure_directories(settings)
            assert os.path.isdir(os.path.join(tmpdir, "out", "subdir"))
            assert os.path.isdir(os.path.join(tmpdir, "data"))


class TestExecute:
    """Tests for step0 execute function."""

    @responses.activate
    def test_with_cookie(self, temp_settings, sample_session_api_response):
        """Should fetch session from API and save it."""
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/auth/session",
            json=sample_session_api_response,
            status=200,
        )

        result = step0_session.execute(
            settings=temp_settings,
            cookie="new_cookie_value",
        )

        assert result.email == "test@example.com"
        assert result.user_id == "95654"
        assert result.firstname == "Test"
        assert result.cookie == "new_cookie_value"

        # Check session saved
        sessions = step0_session._load_sessions(temp_settings.sessions_file)
        assert len(sessions) == 1

        # Check quota initialized
        with open(temp_settings.quota_file, "r") as f:
            quotas = json.load(f)
        assert len(quotas) == 1
        assert quotas[0]["email"] == "test@example.com"

    def test_with_email_found(self, temp_settings):
        """Should use saved session when email found."""
        # Pre-save a session
        sessions = [
            {
                "cookie": "saved_cookie",
                "email": "saved@test.com",
                "user_id": "999",
                "firstname": "Saved",
                "lastname": "User",
                "expires": "2099-12-31T00:00:00Z",
            }
        ]
        step0_session._save_sessions(temp_settings.sessions_file, sessions)

        result = step0_session.execute(
            settings=temp_settings,
            email="saved@test.com",
        )

        assert result.email == "saved@test.com"
        assert result.user_id == "999"
        assert result.cookie == "saved_cookie"

    def test_with_email_expired(self, temp_settings):
        """Should return empty cookie when session expired."""
        sessions = [
            {
                "cookie": "old_cookie",
                "email": "expired@test.com",
                "user_id": "111",
                "firstname": "Old",
                "lastname": "User",
                "expires": "2020-01-01T00:00:00Z",
            }
        ]
        step0_session._save_sessions(temp_settings.sessions_file, sessions)

        result = step0_session.execute(
            settings=temp_settings,
            email="expired@test.com",
        )

        assert result.cookie == ""
        assert result.email == "expired@test.com"

    def test_fallback_to_env(self, temp_settings):
        """Should keep env values when no cookie/email provided."""
        result = step0_session.execute(settings=temp_settings)

        assert result.email == "env@test.com"
        assert result.cookie == "env_cookie"
        assert result.user_id == "env_user_id"
