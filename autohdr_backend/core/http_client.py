"""
HTTP client module - provides a shared requests.Session with default headers.

All API calls to AutoHDR go through this client, ensuring consistent
headers, cookies, and proxy configuration. Step2 (S3 upload) uses a
separate set of headers via the `get_s3_upload_headers` method.
"""

from typing import Optional

import requests

from config.settings import Settings


class HttpClient:
    """
    Shared HTTP client wrapping requests.Session.

    Configures default headers, cookies, and proxy settings from
    the application Settings. Provides convenience methods for
    common HTTP operations.

    Attributes:
        settings: Application settings instance.
        session: Underlying requests.Session with configured defaults.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize HttpClient with settings.

        Args:
            settings: Application settings containing base_url, cookie,
                      user_agent, and proxy configuration.
        """
        self.settings = settings
        self.session = requests.Session()

        # Set default headers for AutoHDR API calls
        self.session.headers.update(
            {
                "User-Agent": settings.user_agent,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Referer": f"{settings.base_url}/",
                "Origin": settings.base_url,
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "Cookie": settings.cookie,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Priority": "u=4",
                "TE": "trailers",
            }
        )

        # Configure proxy if provided
        if settings.proxies:
            self.session.proxies.update(settings.proxies)

    def post(self, url: str, json_data: Optional[dict] = None, **kwargs) -> requests.Response:
        """
        Send a POST request.

        Args:
            url: Full URL or path (will be joined with base_url if relative).
            json_data: JSON payload to send.
            **kwargs: Additional arguments passed to requests.Session.post.

        Returns:
            requests.Response object.
        """
        full_url = self._build_url(url)
        return self.session.post(full_url, json=json_data, **kwargs)

    def get(self, url: str, params: Optional[dict] = None, **kwargs) -> requests.Response:
        """
        Send a GET request.

        Args:
            url: Full URL or path (will be joined with base_url if relative).
            params: Query parameters.
            **kwargs: Additional arguments passed to requests.Session.get.

        Returns:
            requests.Response object.
        """
        full_url = self._build_url(url)
        return self.session.get(full_url, params=params, **kwargs)

    def put_binary(self, url: str, data: bytes, headers: Optional[dict] = None) -> requests.Response:
        """
        Send a PUT request with binary data (used for S3 upload).

        This method does NOT use the default session headers.
        It uses S3-specific headers instead.

        Args:
            url: Full S3 presigned URL.
            data: Binary file content to upload.
            headers: Custom headers for the upload. If None, uses default S3 headers.

        Returns:
            requests.Response object.
        """
        upload_headers = headers or self.get_s3_upload_headers()
        return requests.put(url, data=data, headers=upload_headers)

    def get_s3_upload_headers(self) -> dict:
        """
        Get headers specific to S3 file upload (step2).

        These headers are different from the default API headers
        because S3 requires specific content-type and ACL headers.

        Returns:
            Dictionary of headers for S3 upload.
        """
        return {
            "User-Agent": self.settings.user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/octet-stream",
            "x-amz-acl": "private",
            "Origin": self.settings.base_url,
            "Connection": "keep-alive",
            "Referer": f"{self.settings.base_url}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }

    def download_file(self, url: str) -> bytes:
        """
        Download a file from a URL and return its binary content.

        Args:
            url: URL of the file to download.

        Returns:
            Binary content of the downloaded file.

        Raises:
            requests.HTTPError: If the download request fails.
        """
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return response.content

    def _build_url(self, url: str) -> str:
        """
        Build full URL from a path or return as-is if already absolute.

        Args:
            url: URL path (e.g., '/api/proxy/...') or full URL.

        Returns:
            Full URL string.
        """
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base = self.settings.base_url.rstrip("/")
        path = url if url.startswith("/") else f"/{url}"
        return f"{base}{path}"
