"""
Step 6: Get Processed Photo URLs.

Fetches the list of processed photos for a photoshoot, cleans URLs
by removing query parameters, and validates that each URL contains
the expected unique_str and filename.

Input:
    - photoshoot_id from step5
    - unique_str from step1
    - input filenames from step1

Output:
    - List of cleaned URLs (without query params)
    - Empty list if no processed photos found

API Endpoint: GET /api/proxy/photoshoots/{id}/processed_photos?page=1&page_size=10
"""

import logging
from typing import List
from urllib.parse import urlparse, urlunparse

from core.http_client import HttpClient
from core.logger import log

logger = logging.getLogger(__name__)


def _clean_url(url: str) -> str:
    """
    Remove query parameters from a URL.

    Example:
        'https://example.com/photo.jpg?key=value' → 'https://example.com/photo.jpg'

    Args:
        url: Full URL with potential query parameters.

    Returns:
        URL with query parameters removed.
    """
    parsed = urlparse(url)
    # Rebuild URL without query string and fragment
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return clean


def _extract_filename_from_url(url: str) -> str:
    """
    Extract the filename from a URL path.

    Example:
        'https://s3.com/.../processed/photo.jpg' → 'photo.jpg'

    Args:
        url: URL string.

    Returns:
        Filename from the URL path.
    """
    parsed = urlparse(url)
    path = parsed.path
    return path.split("/")[-1] if "/" in path else path


def _validate_urls(
    urls: List[str],
    unique_str: str,
    input_filenames: List[str],
) -> List[str]:
    """
    Validate processed URLs against expected unique_str and filenames.

    For each URL:
    1. Check if unique_str is present in the URL
    2. Check if the filename matches one from the input list

    Logs debug warnings for any mismatches but still includes the URL
    in the returned list.

    Args:
        urls: List of cleaned URLs to validate.
        unique_str: Expected UUID string from step1.
        input_filenames: List of original input filenames.

    Returns:
        List of validated URLs (all URLs are returned regardless of validation).
    """
    validated = []

    for url in urls:
        # Check unique_str presence
        if unique_str not in url:
            log(
                logger,
                "DEBUG",
                6,
                f"Report to admin to check unique_str {unique_str} not in url {url}",
            )

        # Check filename
        name_file = _extract_filename_from_url(url)
        # Compare without extension since processed files may have different extensions
        name_without_ext = name_file.rsplit(".", 1)[0] if "." in name_file else name_file
        input_names_without_ext = [
            fn.rsplit(".", 1)[0] if "." in fn else fn for fn in input_filenames
        ]

        if name_file not in input_filenames and name_without_ext not in input_names_without_ext:
            log(
                logger,
                "DEBUG",
                6,
                f"Report to admin to check name file {name_file} not in input list {input_filenames}",
            )

        validated.append(url)

    return validated


def execute(
    client: HttpClient,
    photoshoot_id: int,
    unique_str: str,
    input_filenames: List[str],
    page_size: int = 10,
) -> List[str]:
    """
    Execute Step 6: Get processed photo URLs.

    1. Fetches processed photos from API
    2. Cleans URLs by removing query parameters
    3. Validates unique_str and filename presence in each URL
    4. Returns list of cleaned URLs

    Args:
        client: HTTP client instance.
        photoshoot_id: Photoshoot ID from step5.
        unique_str: UUID string from step1.
        input_filenames: List of original input filenames.
        page_size: Number of photos per page (default: 10).

    Returns:
        List of cleaned processed photo URLs, or empty list if none found.
    """
    step = 6

    url = (
        f"/api/proxy/photoshoots/{photoshoot_id}"
        f"/processed_photos?page=1&page_size={page_size}"
    )

    try:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        log(logger, "ERROR", step, f"Failed to get processed photos: {e}")
        return []

    # Response should be a list
    if not isinstance(data, list):
        log(logger, "ERROR", step, f"Unexpected response format: {type(data)}")
        return []

    if len(data) == 0:
        log(logger, "DEBUG", step, "No processed photos found")
        return []

    # Extract and clean URLs
    raw_urls = [item.get("url", "") for item in data if item.get("url")]
    cleaned_urls = [_clean_url(u) for u in raw_urls]

    # Validate
    validated_urls = _validate_urls(cleaned_urls, unique_str, input_filenames)

    log(logger, "INFO", step, f"Found processed photos: {len(validated_urls)}")

    return validated_urls
