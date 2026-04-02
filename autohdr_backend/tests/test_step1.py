"""Tests for Step 1: Generate Presigned URLs."""

import os
import tempfile
import pytest
import responses

from steps import step1_presigned_urls
from models.schemas import PipelineContext


class TestExtractFilenames:
    """Tests for _extract_filenames function."""

    def test_extract_from_paths(self):
        """Should extract basename from each file path."""
        paths = ["/path/to/photo1.jpg", "/other/photo2.png"]
        result = step1_presigned_urls._extract_filenames(paths)
        assert result == ["photo1.jpg", "photo2.png"]

    def test_extract_empty_list(self):
        """Should return empty list for empty input."""
        assert step1_presigned_urls._extract_filenames([]) == []


class TestBuildPayload:
    """Tests for _build_payload function."""

    def test_payload_structure(self):
        """Should build correct payload with unique_str and files."""
        payload = step1_presigned_urls._build_payload(
            "test-uuid", ["file1.jpg", "file2.png"]
        )
        assert payload["unique_str"] == "test-uuid"
        assert len(payload["files"]) == 2
        assert payload["files"][0]["filename"] == "file1.jpg"
        assert payload["files"][0]["md5"] == ""


class TestParsePresignedUrls:
    """Tests for _parse_presigned_urls function."""

    def test_parse_valid_response(self, sample_presigned_response):
        """Should parse presigned URLs correctly from API response."""
        result = step1_presigned_urls._parse_presigned_urls(sample_presigned_response)
        assert len(result) == 2
        assert result[0].filename == "test_photo1.jpg"
        assert "s3-accelerate" in result[0].url

    def test_parse_empty_response(self):
        """Should return empty list for missing presignedUrls key."""
        result = step1_presigned_urls._parse_presigned_urls({})
        assert result == []


class TestGenerateUniqueStr:
    """Tests for _generate_unique_str function."""

    def test_generates_uuid_format(self):
        """Should generate a valid UUID4 string."""
        uid = step1_presigned_urls._generate_unique_str()
        assert len(uid) == 36
        assert uid.count("-") == 4

    def test_generates_unique_values(self):
        """Should generate different UUIDs each call."""
        uid1 = step1_presigned_urls._generate_unique_str()
        uid2 = step1_presigned_urls._generate_unique_str()
        assert uid1 != uid2


class TestSaveInputFiles:
    """Tests for _save_input_files function."""

    def test_creates_directory_and_copies(self):
        """Should create input dir and copy files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a source file
            src_file = os.path.join(tmpdir, "source.jpg")
            with open(src_file, "wb") as f:
                f.write(b"test image data")

            result, _ = step1_presigned_urls._save_input_files(
                [src_file], "test-uuid", "test-addr", tmpdir
            )

            expected_dir = os.path.join(tmpdir, "test-uuid", "test-addr")
            assert result == expected_dir
            assert os.path.exists(os.path.join(expected_dir, "source.jpg"))


class TestExecute:
    """Tests for step1 execute function."""

    @responses.activate
    def test_successful_execution(self, http_client, sample_presigned_response):
        """Should generate UUID, call API, and return updated context."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/proxy/generate_presigned_urls",
            json=sample_presigned_response,
            status=200,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, "test_photo1.jpg")
            file2 = os.path.join(tmpdir, "test_photo2.png")
            for f in [file1, file2]:
                with open(f, "wb") as fh:
                    fh.write(b"test data")

            context = PipelineContext(
                file_paths=[file1, file2],
                address="test_addr",
                email="test@test.com",
                firstname="Test",
                lastname="User",
                user_id="12345",
            )

            result = step1_presigned_urls.execute(http_client, context, tmpdir)

            assert result is not None
            assert result.unique_str != ""
            assert len(result.presigned_urls) == 2
            assert result.filenames == ["test_photo1.jpg", "test_photo2.png"]

    @responses.activate
    def test_api_failure(self, http_client):
        """Should return None on API failure."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/proxy/generate_presigned_urls",
            json={"error": "Internal Server Error"},
            status=500,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test.jpg")
            with open(file1, "wb") as f:
                f.write(b"test")

            context = PipelineContext(
                file_paths=[file1],
                address="test",
                email="test@test.com",
                firstname="Test",
                lastname="User",
                user_id="12345",
            )

            result = step1_presigned_urls.execute(http_client, context, tmpdir)
            assert result is None
