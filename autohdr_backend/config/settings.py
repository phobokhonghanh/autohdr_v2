"""
Settings module - loads configuration from environment variables.

All configurable values are centralized here. No hardcoded values
should exist anywhere else in the codebase.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    """
    Application settings loaded from environment variables.

    Attributes:
        base_url: Base URL for AutoHDR API.
        cookie: Session cookie for authentication.
        user_agent: User-Agent header string.
        proxy_http: HTTP proxy URL (optional).
        proxy_https: HTTPS proxy URL (optional).
        output_dir: Base directory for saving files.
        quota_file: Path to the quota tracking JSON file.
        user_id: AutoHDR user ID.
        email: User email address.
        firstname: User first name.
        lastname: User last name.
        address: Default address for photoshoots.
        limit_count: Maximum total download count allowed.
        limit_file: Maximum files per single download batch.
        retry_max_attempts: Maximum number of retry attempts.
        retry_initial_delay: Initial delay in seconds before first retry.
        retry_backoff_factor: Multiplier applied to delay after each retry.
        photoshoot_limit: Number of photoshoots to fetch per request.
        photoshoot_page_size: Page size for processed photos request.
    """

    base_url: str = ""
    cookie: str = ""
    user_agent: str = ""
    proxy_http: Optional[str] = None
    proxy_https: Optional[str] = None
    resources_dir: str = ""
    user_id: str = ""
    email: str = ""
    firstname: str = ""
    lastname: str = ""
    address: str = ""
    limit_count: int = 1000
    limit_file: int = 50
    retry_max_attempts: int = 10
    retry_initial_delay: float = 15.0
    retry_backoff_factor: float = 1.5
    photoshoot_limit: int = 20
    photoshoot_page_size: int = 10

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Settings":
        """
        Create Settings instance from environment variables.
        """
        load_dotenv(dotenv_path=env_path)
        res_dir = os.getenv("AUTOHDR_RESOURCES_DIR", "./resources")

        return cls(
            base_url=os.getenv("AUTOHDR_BASE_URL", "https://www.autohdr.com"),
            cookie=os.getenv("AUTOHDR_COOKIE", ""),
            user_agent=os.getenv(
                "AUTOHDR_USER_AGENT",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) "
                "Gecko/20100101 Firefox/148.0",
            ),
            proxy_http=os.getenv("AUTOHDR_PROXY_HTTP"),
            proxy_https=os.getenv("AUTOHDR_PROXY_HTTPS"),
            resources_dir=res_dir,
            address=os.getenv("AUTOHDR_ADDRESS", ""),
            limit_count=int(os.getenv("AUTOHDR_LIMIT_COUNT", "1000")),
            limit_file=int(os.getenv("AUTOHDR_LIMIT_FILE", "50")),
            retry_max_attempts=int(os.getenv("AUTOHDR_RETRY_MAX_ATTEMPTS", "10")),
            retry_initial_delay=float(os.getenv("AUTOHDR_RETRY_INITIAL_DELAY", "15.0")),
            retry_backoff_factor=float(os.getenv("AUTOHDR_RETRY_BACKOFF_FACTOR", "1.5")),
            photoshoot_limit=int(os.getenv("AUTOHDR_PHOTOSHOOT_LIMIT", "20")),
            photoshoot_page_size=int(os.getenv("AUTOHDR_PHOTOSHOOT_PAGE_SIZE", "10")),
        )

    @property
    def system_dir(self) -> str:
        return os.path.join(self.resources_dir, "system")

    @property
    def users_dir(self) -> str:
        return os.path.join(self.resources_dir, "users")

    @property
    def quota_file(self) -> str:
        return os.path.join(self.system_dir, "quota.json")

    @property
    def sessions_file(self) -> str:
        return os.path.join(self.system_dir, "sessions.json")

    def get_user_dir(self, email: str) -> str:
        return os.path.join(self.users_dir, email)

    def get_user_input_dir(self, email: str) -> str:
        return os.path.join(self.get_user_dir(email), "input")

    def get_user_logs_dir(self, email: str) -> str:
        return os.path.join(self.get_user_dir(email), "logs")

    @property
    def proxies(self) -> Optional[dict]:
        """
        Build proxies dict for requests library.

        Returns:
            Dictionary with http/https proxy URLs, or None if no proxies configured.
        """
        if not self.proxy_http and not self.proxy_https:
            return None
        proxies = {}
        if self.proxy_http:
            proxies["http"] = self.proxy_http
        if self.proxy_https:
            proxies["https"] = self.proxy_https
        return proxies
