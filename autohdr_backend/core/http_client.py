"""
HTTP client module - provides a shared requests.Session with default headers.

All API calls to AutoHDR go through this client, ensuring consistent
headers, cookies, and proxy configuration. Step2 (S3 upload) uses a
separate set of headers via the `get_s3_upload_headers` method.
"""

from typing import Optional

import requests
import random

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

        # Pick one random proxy from the list for this instance (job/session)
        random_proxy_url = self._get_random_proxy_url()
        if random_proxy_url:
            self.session.proxies.update({"http": random_proxy_url, "https": random_proxy_url})
        elif settings.proxies:
            # Fallback to default proxies from settings/env if no list is provided
            self.session.proxies.update(settings.proxies)

    def _get_random_proxy_url(self) -> Optional[str]:
        """
        Pick a random proxy URL from the settings list if available.
        """
        all_proxies = self.settings.all_proxies
        if not all_proxies:
            return None
        return random.choice(all_proxies)

    def post(self, url: str, json_data: Optional[dict] = None, **kwargs) -> requests.Response:
        """
        Send a POST request using the instance's chosen proxy.
        """
        full_url = self._build_url(url)
        return self.session.post(full_url, json=json_data, **kwargs)

    def get(self, url: str, params: Optional[dict] = None, **kwargs) -> requests.Response:
        """
        Send a GET request using the instance's chosen proxy.
        """
        full_url = self._build_url(url)
        return self.session.get(full_url, params=params, **kwargs)

    def put_binary(self, url: str, data: bytes, headers: Optional[dict] = None) -> requests.Response:
        """
        Send a PUT request with binary data using the instance's chosen proxy.
        """
        upload_headers = headers or self.get_s3_upload_headers()
        return self.session.put(url, data=data, headers=upload_headers)

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
        Download a file from a URL using the instance's chosen proxy.
        """
        response = self.session.get(url, stream=True)
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
