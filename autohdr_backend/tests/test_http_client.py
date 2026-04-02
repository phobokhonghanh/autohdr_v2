"""Tests for the HTTP client module."""

import pytest

from config.settings import Settings
from core.http_client import HttpClient


class TestHttpClient:
    """Tests for HttpClient class."""

    def test_session_headers(self, settings, http_client):
        """Should set default headers correctly."""
        headers = http_client.session.headers
        assert headers["User-Agent"] == "TestAgent/1.0"
        assert headers["Content-Type"] == "application/json"
        assert headers["Cookie"] == "test_cookie=value"

    def test_build_url_absolute(self, http_client):
        """Should return absolute URL as-is."""
        url = "https://other.com/api/test"
        assert http_client._build_url(url) == url

    def test_build_url_relative(self, http_client):
        """Should join relative path with base_url."""
        url = "/api/proxy/test"
        assert http_client._build_url(url) == "https://www.autohdr.com/api/proxy/test"

    def test_build_url_no_leading_slash(self, http_client):
        """Should add leading slash for relative paths."""
        url = "api/test"
        assert http_client._build_url(url) == "https://www.autohdr.com/api/test"

    def test_s3_upload_headers(self, http_client):
        """Should return correct S3 upload headers."""
        headers = http_client.get_s3_upload_headers()
        assert headers["Content-Type"] == "application/octet-stream"
        assert headers["x-amz-acl"] == "private"
        assert headers["Sec-Fetch-Site"] == "cross-site"

    def test_proxy_configuration(self):
        """Should configure proxy when provided."""
        settings = Settings(
            base_url="https://test.com",
            proxy_http="http://proxy:8080",
            proxy_https="https://proxy:8080",
        )
        client = HttpClient(settings)
        assert client.session.proxies["http"] == "http://proxy:8080"
        assert client.session.proxies["https"] == "https://proxy:8080"

    def test_no_proxy(self):
        """Should not set proxies when not configured."""
        settings = Settings(base_url="https://test.com")
        client = HttpClient(settings)
        # Proxies should be empty or not set
        assert not settings.proxies
