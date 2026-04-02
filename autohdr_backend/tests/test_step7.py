"""Tests for Step 7: Download Processed Photos."""

import json
import os
import tempfile
import pytest
import responses

from steps import step7_download_photos
from models.schemas import QuotaRecord


class TestLoadSaveQuota:
    """Tests for quota file load/save functions."""

    def test_load_nonexistent_file(self):
        """Should return empty list when file doesn't exist."""
        result = step7_download_photos._load_quota("/nonexistent/path.json")
        assert result == []

    def test_save_and_load(self):
        """Should save and load quota records correctly."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            records = [
                {
                    "email": "test@test.com",
                    "unique_str": ["uuid-1"],
                    "count": 5,
                    "limit_count": 100,
                    "limit_file": 10,
                }
            ]
            step7_download_photos._save_quota(path, records)
            loaded = step7_download_photos._load_quota(path)

            assert len(loaded) == 1
            assert loaded[0]["email"] == "test@test.com"
            assert loaded[0]["count"] == 5
        finally:
            os.unlink(path)


class TestFindOrCreateQuota:
    """Tests for _find_or_create_quota function."""

    def test_find_existing(self):
        """Should find existing quota record by email."""
        records = [{"email": "test@test.com", "unique_str": ["a"], "count": 5,
                     "limit_count": 100, "limit_file": 10}]
        result = step7_download_photos._find_or_create_quota(
            records, "test@test.com", 1000, 50
        )
        assert result.email == "test@test.com"
        assert result.count == 5

    def test_create_new(self):
        """Should create new quota record when email not found."""
        records = []
        result = step7_download_photos._find_or_create_quota(
            records, "new@test.com", 1000, 50
        )
        assert result.email == "new@test.com"
        assert result.count == 0
        assert result.limit_count == 1000


class TestCheckQuota:
    """Tests for _check_quota function."""

    def test_within_limits(self):
        """Should return None when within quota."""
        quota = QuotaRecord(email="t@t.com", count=0, limit_count=100, limit_file=10)
        result = step7_download_photos._check_quota(quota, 5)
        assert result is None

    def test_exceeds_limit_file(self):
        """Should return error when files exceed limit_file."""
        quota = QuotaRecord(email="t@t.com", count=0, limit_count=100, limit_file=5)
        result = step7_download_photos._check_quota(quota, 10)
        assert result is not None
        assert "limit file" in result

    def test_exceeds_limit_count(self):
        """Should return error when total would exceed limit_count."""
        quota = QuotaRecord(email="t@t.com", count=95, limit_count=100, limit_file=50)
        result = step7_download_photos._check_quota(quota, 10)
        assert result is not None
        assert "limited" in result


class TestUpdateQuota:
    """Tests for _update_quota_in_records function."""

    def test_update_existing(self):
        """Should update existing record in place."""
        records = [{"email": "t@t.com", "unique_str": [], "count": 0,
                     "limit_count": 100, "limit_file": 10}]
        quota = QuotaRecord(email="t@t.com", unique_str=["uuid-1"], count=5,
                           limit_count=100, limit_file=10)
        result = step7_download_photos._update_quota_in_records(records, quota)
        assert result[0]["count"] == 5
        assert "uuid-1" in result[0]["unique_str"]

    def test_insert_new(self):
        """Should append new record when email not found."""
        records = []
        quota = QuotaRecord(email="new@t.com", count=0, limit_count=100, limit_file=10)
        result = step7_download_photos._update_quota_in_records(records, quota)
        assert len(result) == 1
        assert result[0]["email"] == "new@t.com"


class TestExecute:
    """Tests for step7 execute function."""

    @responses.activate
    def test_successful_download(self, settings):
        """Should download files and update quota."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.output_dir = tmpdir
            settings.quota_file = os.path.join(tmpdir, "quota.json")

            url1 = "https://s3.amazonaws.com/uuid/processed/photo1.jpg"
            url2 = "https://s3.amazonaws.com/uuid/processed/photo2.png"

            responses.add(responses.GET, url1, body=b"image data 1", status=200)
            responses.add(responses.GET, url2, body=b"image data 2", status=200)

            from core.http_client import HttpClient
            client = HttpClient(settings)

            result = step7_download_photos.execute(
                client=client,
                settings=settings,
                cleaned_urls=[url1, url2],
                unique_str="uuid",
                address="test_addr",
                email="test@test.com",
            )

            assert result is True

            # Check quota updated
            quota = step7_download_photos._load_quota(settings.quota_file)
            assert len(quota) == 1
            assert quota[0]["count"] == 2

    def test_empty_urls(self, settings):
        """Should return True with no files to download."""
        from core.http_client import HttpClient
        client = HttpClient(settings)

        result = step7_download_photos.execute(
            client=client,
            settings=settings,
            cleaned_urls=[],
            unique_str="uuid",
            address="test",
            email="test@test.com",
        )
        assert result is True

    def test_quota_exceeded(self, settings):
        """Should return False when quota is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.output_dir = tmpdir
            settings.quota_file = os.path.join(tmpdir, "quota.json")
            settings.limit_file = 1  # Only allow 1 file

            from core.http_client import HttpClient
            client = HttpClient(settings)

            result = step7_download_photos.execute(
                client=client,
                settings=settings,
                cleaned_urls=["http://url1", "http://url2"],  # 2 files exceeds limit
                unique_str="uuid",
                address="test",
                email="test@test.com",
            )
            assert result is False
