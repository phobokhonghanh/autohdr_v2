"""Tests for Step 5: Poll Photoshoot Status."""

import pytest
import responses

from steps import step5_poll_status


class TestFindMatchingPhotoshoot:
    """Tests for _find_matching_photoshoot function."""

    def test_finds_matching(self, sample_photoshoots_response):
        """Should find photoshoot matching unique_str and address."""
        photoshoots = sample_photoshoots_response["photoshoots"]
        result = step5_poll_status._find_matching_photoshoot(
            photoshoots,
            "83b93a60-aef6-409a-9f0d-7c1683c06e3f",
            "Test Address 123",
        )
        assert result is not None
        assert result["id"] == 907761

    def test_no_match_unique_str(self, sample_photoshoots_response):
        """Should return None when unique_str doesn't match."""
        photoshoots = sample_photoshoots_response["photoshoots"]
        result = step5_poll_status._find_matching_photoshoot(
            photoshoots, "nonexistent-uuid", "Test Address 123"
        )
        assert result is None

    def test_no_match_address(self, sample_photoshoots_response):
        """Should return None when address doesn't match."""
        photoshoots = sample_photoshoots_response["photoshoots"]
        result = step5_poll_status._find_matching_photoshoot(
            photoshoots,
            "83b93a60-aef6-409a-9f0d-7c1683c06e3f",
            "Wrong Address",
        )
        assert result is None


class TestExecute:
    """Tests for step5 execute function."""

    @responses.activate
    def test_success_status(self, http_client, settings, sample_photoshoots_response):
        """Should return photoshoot ID when status is 'success'."""
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/users/12345/photoshoots",
            json=sample_photoshoots_response,
            status=200,
        )

        result = step5_poll_status.execute(
            client=http_client,
            settings=settings,
            unique_str="83b93a60-aef6-409a-9f0d-7c1683c06e3f",
            address="Test Address 123",
        )
        assert result == 907761

    @responses.activate
    def test_ignore_status(self, http_client, settings):
        """Should return None when status is 'ignore'."""
        data = {
            "total_count": 1,
            "photoshoots": [
                {
                    "id": 100,
                    "name": "test-uuid",
                    "address": "test addr",
                    "status": "ignore",
                }
            ],
        }
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/users/12345/photoshoots",
            json=data,
            status=200,
        )

        result = step5_poll_status.execute(
            client=http_client,
            settings=settings,
            unique_str="test-uuid",
            address="test addr",
        )
        assert result is None

    @responses.activate
    def test_not_found(self, http_client, settings):
        """Should return None when unique_str not found in photoshoots."""
        data = {"total_count": 0, "photoshoots": []}
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/users/12345/photoshoots",
            json=data,
            status=200,
        )

        result = step5_poll_status.execute(
            client=http_client,
            settings=settings,
            unique_str="missing-uuid",
            address="test addr",
        )
        assert result is None

    @responses.activate
    def test_in_progress_then_success(self, http_client, settings):
        """Should retry on 'in_progress' and return id on 'success'."""
        in_progress = {
            "total_count": 1,
            "photoshoots": [
                {
                    "id": 200,
                    "name": "retry-uuid",
                    "address": "retry addr",
                    "status": "in_progress",
                }
            ],
        }
        success = {
            "total_count": 1,
            "photoshoots": [
                {
                    "id": 200,
                    "name": "retry-uuid",
                    "address": "retry addr",
                    "status": "success",
                }
            ],
        }

        # First call returns in_progress, second returns success
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/users/12345/photoshoots",
            json=in_progress,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.autohdr.com/api/users/12345/photoshoots",
            json=success,
            status=200,
        )

        result = step5_poll_status.execute(
            client=http_client,
            settings=settings,
            unique_str="retry-uuid",
            address="retry addr",
        )
        assert result == 200
