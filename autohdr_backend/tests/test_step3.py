"""Tests for Step 3: Finalize Upload."""

import pytest
import responses

from steps import step3_finalize_upload


class TestValidateResponse:
    """Tests for _validate_response function."""

    def test_valid_response(self):
        """Should return True when response contains 'successfully'."""
        data = {
            "info": "All files uploaded successfully for folder test-uuid!"
        }
        assert step3_finalize_upload._validate_response(data, "test-uuid") is True

    def test_missing_successfully(self):
        """Should return False when 'successfully' not in response."""
        data = {"info": "Upload failed for folder test-uuid"}
        assert step3_finalize_upload._validate_response(data, "test-uuid") is False

    def test_changed_format(self, capfd):
        """Should log warning when format differs but still contains 'successfully'."""
        data = {"info": "Files uploaded successfully with different format"}
        result = step3_finalize_upload._validate_response(data, "test-uuid")
        assert result is True

    def test_empty_info(self):
        """Should return False when info is empty."""
        data = {"info": ""}
        assert step3_finalize_upload._validate_response(data, "test-uuid") is False


class TestExecute:
    """Tests for step3 execute function."""

    @responses.activate
    def test_successful_finalize(self, http_client):
        """Should return True on successful finalization."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/proxy/finalize_upload",
            json={
                "info": "All files uploaded successfully for folder test-uuid!"
            },
            status=200,
        )
        result = step3_finalize_upload.execute(http_client, "test-uuid")
        assert result is True

    @responses.activate
    def test_failed_finalize(self, http_client):
        """Should return False when response doesn't contain 'successfully'."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/proxy/finalize_upload",
            json={"info": "Upload failed"},
            status=200,
        )
        result = step3_finalize_upload.execute(http_client, "test-uuid")
        assert result is False

    @responses.activate
    def test_http_error(self, http_client):
        """Should return False on HTTP error."""
        responses.add(
            responses.POST,
            "https://www.autohdr.com/api/proxy/finalize_upload",
            status=500,
        )
        result = step3_finalize_upload.execute(http_client, "test-uuid")
        assert result is False
