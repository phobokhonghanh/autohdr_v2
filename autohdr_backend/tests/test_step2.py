"""Tests for Step 2: Upload Files to S3."""

import os
import tempfile
import pytest
import responses

from steps import step2_upload_files
from models.schemas import PipelineContext, PresignedUrl


class TestFindFilePath:
    """Tests for _find_file_path function."""

    def test_finds_matching_file(self):
        """Should find file path matching the filename."""
        paths = ["/path/to/photo1.jpg", "/path/to/photo2.png"]
        result = step2_upload_files._find_file_path("photo1.jpg", paths)
        assert result == "/path/to/photo1.jpg"

    def test_raises_on_not_found(self):
        """Should raise FileNotFoundError when filename doesn't match."""
        paths = ["/path/to/photo1.jpg"]
        with pytest.raises(FileNotFoundError):
            step2_upload_files._find_file_path("missing.jpg", paths)


class TestUploadSingleFile:
    """Tests for _upload_single_file function."""

    @responses.activate
    def test_successful_upload(self, http_client):
        """Should return True on status 200."""
        url = "https://s3.amazonaws.com/bucket/test.jpg?sig=xxx"
        responses.add(responses.PUT, url, status=200)

        presigned = PresignedUrl(filename="test.jpg", url=url)
        result = step2_upload_files._upload_single_file(
            http_client, presigned, b"file content"
        )
        assert result is True

    @responses.activate
    def test_failed_upload(self, http_client):
        """Should return False on non-200 status."""
        url = "https://s3.amazonaws.com/bucket/test.jpg?sig=xxx"
        responses.add(responses.PUT, url, status=403)

        presigned = PresignedUrl(filename="test.jpg", url=url)
        result = step2_upload_files._upload_single_file(
            http_client, presigned, b"file content"
        )
        assert result is False


class TestExecute:
    """Tests for step2 execute function."""

    @responses.activate
    def test_all_uploads_succeed(self, http_client):
        """Should return True when all files upload successfully."""
        url1 = "https://s3.amazonaws.com/bucket/p1.jpg?sig=a"
        url2 = "https://s3.amazonaws.com/bucket/p2.png?sig=b"
        responses.add(responses.PUT, url1, status=200)
        responses.add(responses.PUT, url2, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "p1.jpg")
            f2 = os.path.join(tmpdir, "p2.png")
            for f in [f1, f2]:
                with open(f, "wb") as fh:
                    fh.write(b"test data")

            context = PipelineContext(
                file_paths=[f1, f2],
                address="test",
                email="test@test.com",
                firstname="T",
                lastname="U",
                user_id="1",
                presigned_urls=[
                    PresignedUrl(filename="p1.jpg", url=url1),
                    PresignedUrl(filename="p2.png", url=url2),
                ],
                filenames=["p1.jpg", "p2.png"],
            )

            result = step2_upload_files.execute(http_client, context)
            assert result is True

    def test_no_presigned_urls(self, http_client):
        """Should return False when no presigned URLs available."""
        context = PipelineContext(
            file_paths=[],
            address="test",
            email="test@test.com",
            firstname="T",
            lastname="U",
            user_id="1",
            presigned_urls=[],
        )
        result = step2_upload_files.execute(http_client, context)
        assert result is False
