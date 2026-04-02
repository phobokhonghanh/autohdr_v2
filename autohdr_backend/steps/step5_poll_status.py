"""
Step 5: Poll Photoshoot Status.

Polls the AutoHDR API to find the photoshoot matching unique_str and
address, then waits for processing to complete with retry logic.

Input:
    - user_id, unique_str, address

Output:
    - photoshoot_id (int) if found and status is 'success'
    - None if not found, ignored, or timed out

Status handling:
    - 'success' → return id
    - 'ignore' → return None + log
    - 'in_progress' → retry with backoff (15s * 1.5^n, max 10 times)
    - not found → return None + log

API Endpoint: GET /api/users/{user_id}/photoshoots?limit=20&offset=0
"""

import time
import logging
from typing import Optional, List

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import log

logger = logging.getLogger(__name__)


def _find_matching_photoshoot(
    photoshoots: List[dict],
    unique_str: str,
    address: str,
) -> Optional[dict]:
    """
    Find a photoshoot matching unique_str and address.

    Iterates through the photoshoots list to find one where
    name == unique_str AND address == address.

    Args:
        photoshoots: List of photoshoot dictionaries from API.
        unique_str: UUID string to match against 'name' field.
        address: Address string to match.

    Returns:
        Matching photoshoot dict, or None if not found.
    """
    for ps in photoshoots:
        if ps.get("name") == unique_str and ps.get("address") == address:
            return ps
    return None


def _fetch_photoshoots(
    client: HttpClient,
    user_id: str,
    limit: int,
) -> Optional[dict]:
    """
    Fetch photoshoots list from the API.

    Args:
        client: HTTP client instance.
        user_id: AutoHDR user ID.
        limit: Number of photoshoots to fetch.

    Returns:
        JSON response dict, or None on error.
    """
    url = f"/api/users/{user_id}/photoshoots?limit={limit}&offset=0"
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(logger, "ERROR", 5, f"Failed to fetch photoshoots: {e}")
        return None


def execute(
    client: HttpClient,
    settings: Settings,
    unique_str: str,
    address: str,
) -> Optional[int]:
    """
    Execute Step 5: Poll for photoshoot status.

    Fetches the user's photoshoots, finds one matching unique_str
    and address, then handles status:
    - 'success': returns the photoshoot id
    - 'ignore': returns None with log message
    - 'in_progress': retries with exponential backoff
    - not found: returns None with log message

    Retry behavior:
    - Initial delay: 15 seconds
    - After each retry: delay *= 1.5
    - Maximum retries: 10
    - Logs retry count and approximate wait time in minutes

    Args:
        client: HTTP client instance.
        settings: Application settings with retry config.
        unique_str: UUID string from step1.
        address: Address string from step1.

    Returns:
        Photoshoot ID (int) if found with status 'success',
        None otherwise.
    """
    step = 5
    delay = settings.retry_initial_delay
    max_retries = settings.retry_max_attempts
    backoff_factor = settings.retry_backoff_factor
    user_id = settings.user_id

    for attempt in range(max_retries + 1):
        # Fetch photoshoots
        data = _fetch_photoshoots(client, user_id, settings.photoshoot_limit)
        if data is None:
            return None

        photoshoots = data.get("photoshoots", [])

        # Find matching photoshoot
        match = _find_matching_photoshoot(photoshoots, unique_str, address)

        if match is None:
            log(logger, "DEBUG", step, f"Không tìm thấy unique_str: {unique_str}")
            return None

        status = match.get("status", "")
        photoshoot_id = match.get("id")

        if status == "success":
            log(
                logger,
                "INFO",
                step,
                f"Photoshoot found: id={photoshoot_id}, status=success",
            )
            return photoshoot_id

        elif status == "ignore":
            log(logger, "DEBUG", step, f"Đã bị ignore. Response: {match}")
            return None

        elif status == "in_progress":
            if attempt < max_retries:
                minutes_approx = delay / 60
                log(
                    logger,
                    "INFO",
                    step,
                    f"Server XYZ is processing... "
                    f"Retry {attempt + 1}/{max_retries}, "
                    f"waiting for {delay:.0f}s (~{minutes_approx:.1f} minutes)",
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                log(
                    logger,
                    "DEBUG",
                    step,
                    f"Server XYZ is overloaded, please try again later "
                    f"or change cookie. Response: {match}",
                )
                return None

        else:
            log(
                logger,
                "DEBUG",
                step,
                f"Unknown status '{status}' for photoshoot. Response: {match}",
            )
            return None

    # Should not reach here, but safety fallback
    log(
        logger,
        "DEBUG",
        step,
        f"Server XYZ is overloaded, please try again later "
        f"or change cookie.",
    )
    return None
