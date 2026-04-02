"""Tests for Step 4: Associate and Run Processing."""

import pytest
import responses

from steps import step4_associate_and_run


class TestBuildPayload:
    """Tests for _build_payload function."""

    def test_payload_fields(self):
        """Should include all required fields in payload."""
        payload = step4_associate_and_run._build_payload(
            unique_str="test-uuid",
            email="test@test.com",
            firstname="Test",
            lastname="User",
            address="123 Main St",
            files_count=3,
        )

        assert payload["unique_str"] == "test-uuid"
        assert payload["email"] == "test@test.com"
        assert payload["firstname"] == "Test"
        assert payload["lastname"] == "User"
        assert payload["address"] == "123 Main St"
        assert payload["files_count"] == 3
        assert payload["perspective_correction"] is True
        assert payload["spoofId"] is None


class TestExecute:
    """Tests for step4 execute function."""

    @responses.activate
    def test_successful_processing(self, http_client):
        """Should return True when API returns success=true."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/inference/associate-and-run",
            json={"success": True, "env": "prod"},
            status=200,
        )

        result = step4_associate_and_run.execute(
            client=http_client,
            unique_str="test-uuid",
            email="test@test.com",
            firstname="Test",
            lastname="User",
            address="123 Main St",
            files_count=2,
        )
        assert result is True

    @responses.activate
    def test_failed_processing(self, http_client):
        """Should return False when API returns success=false."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/inference/associate-and-run",
            json={"success": False, "env": "prod"},
            status=200,
        )

        result = step4_associate_and_run.execute(
            client=http_client,
            unique_str="test-uuid",
            email="test@test.com",
            firstname="Test",
            lastname="User",
            address="123 Main St",
            files_count=2,
        )
        assert result is False

    @responses.activate
    def test_http_error(self, http_client):
        """Should return False on HTTP error."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/inference/associate-and-run",
            status=500,
        )

        result = step4_associate_and_run.execute(
            client=http_client,
            unique_str="test-uuid",
            email="test@test.com",
            firstname="Test",
            lastname="User",
            address="123 Main St",
            files_count=2,
        )
        assert result is False
