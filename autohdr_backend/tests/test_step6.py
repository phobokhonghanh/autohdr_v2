"""Tests for Step 6: Get Processed Photo URLs."""

import pytest
import responses

from steps import step6_get_processed_urls


class TestCleanUrl:
    """Tests for _clean_url function."""

    def test_removes_query_params(self):
        """Should remove query parameters from URL."""
        url = "https://s3.amazonaws.com/uuid/processed/photo.jpg?key=val&other=123"
        result = step6_get_processed_urls._clean_url(url)
        assert result == "https://s3.amazonaws.com/uuid/processed/photo.jpg"

    def test_url_without_params(self):
        """Should return URL unchanged when no query params."""
        url = "https://s3.amazonaws.com/uuid/processed/photo.jpg"
        result = step6_get_processed_urls._clean_url(url)
        assert result == url


class TestExtractFilename:
    """Tests for _extract_filename_from_url function."""

    def test_extracts_filename(self):
        """Should extract filename from URL path."""
        url = "https://s3.amazonaws.com/uuid/processed/photo.jpg"
        result = step6_get_processed_urls._extract_filename_from_url(url)
        assert result == "photo.jpg"


class TestValidateUrls:
    """Tests for _validate_urls function."""

    def test_valid_urls(self):
        """Should return all URLs when valid."""
        urls = [
            "https://s3.amazonaws.com/test-uuid/processed/photo1.jpg",
            "https://s3.amazonaws.com/test-uuid/processed/photo2.png",
        ]
        result = step6_get_processed_urls._validate_urls(
            urls, "test-uuid", ["photo1.jpg", "photo2.png"]
        )
        assert len(result) == 2

    def test_missing_unique_str_still_included(self):
        """Should include URL even when unique_str doesn't match (logs warning)."""
        urls = ["https://s3.amazonaws.com/other-uuid/processed/photo.jpg"]
        result = step6_get_processed_urls._validate_urls(
            urls, "test-uuid", ["photo.jpg"]
        )
        assert len(result) == 1

    def test_missing_filename_still_included(self):
        """Should include URL even when filename doesn't match (logs warning)."""
        urls = ["https://s3.amazonaws.com/test-uuid/processed/unknown.jpg"]
        result = step6_get_processed_urls._validate_urls(
            urls, "test-uuid", ["photo1.jpg"]
        )
        assert len(result) == 1


class TestExecute:
    """Tests for step6 execute function."""

    @responses.activate
    def test_successful_execution(self, http_client, sample_processed_photos_response):
        """Should return cleaned URLs on success."""
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/proxy/photoshoots/907761/processed_photos",
            json=sample_processed_photos_response,
            status=200,
        )

        result = step6_get_processed_urls.execute(
            client=http_client,
            photoshoot_id=907761,
            unique_str="83b93a60-aef6-409a-9f0d-7c1683c06e3f",
            input_filenames=["test_photo1.jpg", "test_photo2.png"],
        )

        assert len(result) == 2
        for url in result:
            assert "?" not in url  # Query params removed

    @responses.activate
    def test_empty_response(self, http_client):
        """Should return empty list when no processed photos."""
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/proxy/photoshoots/100/processed_photos",
            json=[],
            status=200,
        )

        result = step6_get_processed_urls.execute(
            client=http_client,
            photoshoot_id=100,
            unique_str="test-uuid",
            input_filenames=["photo.jpg"],
        )
        assert result == []

    @responses.activate
    def test_http_error(self, http_client):
        """Should return empty list on HTTP error."""
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/proxy/photoshoots/100/processed_photos",
            status=500,
        )

        result = step6_get_processed_urls.execute(
            client=http_client,
            photoshoot_id=100,
            unique_str="test-uuid",
            input_filenames=["photo.jpg"],
        )
        assert result == []
