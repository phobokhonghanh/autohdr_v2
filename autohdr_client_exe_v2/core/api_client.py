"""
API Client for Railway backend — ONLY used for key validation.
All other requests go directly to AutoHDR via http_client.
"""

import requests
import os
import logging
from typing import Optional
from core.utils import get_hwid

logger = logging.getLogger(__name__)


class ApiClient:
    """Client for Railway backend. Only purpose: check_key."""

    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.getenv("AUTOHDR_API_BASE", "https://autohdr-backend.up.railway.app")
        self.base_url = base_url.rstrip("/")

    def check_key(self, key: str, machine_id: Optional[str] = None) -> bool:
        """
        Calls Railway /api/key/active to validate key + machine locking.
        Returns True if key is valid and bound to this machine.
        """
        if not machine_id:
            machine_id = get_hwid()

        try:
            res = requests.post(
                f"{self.base_url}/api/key/active",
                json={"key": key, "machine_id": machine_id},
                timeout=15,
            )
            if res.status_code == 200:
                return res.json().get("valid", False)
            elif res.status_code == 403:
                return False
            res.raise_for_status()
        except requests.exceptions.ConnectionError:
            logger.error("Không thể kết nối đến server. Kiểm tra kết nối mạng.")
        except requests.exceptions.Timeout:
            logger.error("Server không phản hồi (timeout).")
        except Exception as e:
            logger.error(f"Lỗi kiểm tra key: {e}")

        return False
