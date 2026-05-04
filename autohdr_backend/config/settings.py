"""
Settings module - loads configuration from environment variables.

All configurable values are centralized here. No hardcoded values
should exist anywhere else in the codebase.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List

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
    proxy_user: Optional[str] = None
    proxy_pass: Optional[str] = None
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
    
    # S3 Settings
    s3_region: Optional[str] = None
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: Optional[str] = None

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
            proxy_user=os.getenv("AUTOHDR_PROXY_USER"),
            proxy_pass=os.getenv("AUTOHDR_PROXY_PASS"),
            resources_dir=res_dir,
            address=os.getenv("AUTOHDR_ADDRESS", ""),
            limit_count=int(os.getenv("AUTOHDR_LIMIT_COUNT", "1000")),
            limit_file=int(os.getenv("AUTOHDR_LIMIT_FILE", "50")),
            retry_max_attempts=int(os.getenv("AUTOHDR_RETRY_MAX_ATTEMPTS", "10")),
            retry_initial_delay=float(os.getenv("AUTOHDR_RETRY_INITIAL_DELAY", "15.0")),
            retry_backoff_factor=float(os.getenv("AUTOHDR_RETRY_BACKOFF_FACTOR", "1.5")),
            photoshoot_limit=int(os.getenv("AUTOHDR_PHOTOSHOOT_LIMIT", "20")),
            photoshoot_page_size=int(os.getenv("AUTOHDR_PHOTOSHOOT_PAGE_SIZE", "10")),
            s3_region=os.getenv("S3_REGION"),
            s3_endpoint=os.getenv("S3_ENDPOINT"),
            s3_access_key=os.getenv("S3_ACCESS_KEY"),
            s3_secret_key=os.getenv("S3_SECRET_KEY"),
            s3_bucket=os.getenv("S3_BUCKET_NAME"),
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
    def keys_file(self) -> str:
        return os.path.join(self.system_dir, "keys.json")

    @property
    def sessions_file(self) -> str:
        return os.path.join(self.system_dir, "sessions.json")

    def get_user_dir(self, email: str) -> str:
        return os.path.join(self.users_dir, email)

    def get_user_dir(self, email: str) -> str:
        return os.path.join(self.users_dir, email)

    def get_user_input_dir(self, email: str) -> str:
        return os.path.join(self.get_user_dir(email), "input")

    def get_user_logs_dir(self, email: str) -> str:
        return os.path.join(self.get_user_dir(email), "logs")

    @property
    def all_proxies(self) -> List[str]:
        """
        Load a list of proxy URLs from proxies.json.
        Example format: ["http://proxy1", "http://proxy2"]
        """
        proxies_file = os.path.join(self.system_dir, "proxies.json")
        if os.path.exists(proxies_file):
            try:
                import json
                with open(proxies_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    proxies = []
                    if isinstance(data, list):
                        proxies = data
                    elif isinstance(data, dict) and "http" in data:
                        proxies = [data["http"]]
                    
                    # Apply authentication if provided
                    if self.proxy_user and self.proxy_pass:
                        auth = f"{self.proxy_user}:{self.proxy_pass}@"
                        formatted = []
                        for p in proxies:
                            if not p.startswith("http"):
                                p = f"http://{p}"
                            
                            if "@" not in p: # Only add if not already present
                                parts = p.split("://", 1)
                                p = f"{parts[0]}://{auth}{parts[1]}"
                            formatted.append(p)
                        return formatted
                    return proxies
            except Exception:
                pass
        return []

    @property
    def proxies(self) -> Optional[dict]:
        """
        Legacy single proxy support from environment variables.
        """
        if not self.proxy_http and not self.proxy_https:
            return None
            
        proxies = {}
        if self.proxy_http:
            proxies["http"] = self.proxy_http
        if self.proxy_https:
            proxies["https"] = self.proxy_https
        return proxies


