"""
Step 3: Finalize Upload.

Notifies the AutoHDR API that all files have been uploaded
for the given unique_str.

Input:
    - unique_str from step1

Output:
    - True if finalization succeeded, False otherwise

Validation:
    - Response must contain 'successfully' keyword
    - If response format differs from expected, log a warning

API Endpoint: POST /api/proxy/finalize_upload
"""

import logging
from typing import Optional

from core.http_client import HttpClient
from core.logger import log

logger = logging.getLogger(__name__)

# Expected response format template
_EXPECTED_INFO_TEMPLATE = "All files uploaded successfully for folder {unique_str}!"


def _validate_response(response_data: dict, unique_str: str) -> bool:
    """
    Validate the finalize upload response.

    Checks:
    1. Response contains 'successfully' keyword → True
    2. If response format differs from expected template → log warning
    3. If 'successfully' not in response → False

    Args:
        response_data: JSON response from the API.
        unique_str: The unique_str to validate against.

    Returns:
        True if response indicates success, False otherwise.
    """
    info = response_data.get("info", "")

    # Check if response contains 'successfully'
    if "successfully" not in info:
        log(logger, "ERROR", 3, f"Response does not contain 'successfully': {response_data}")
        return False

    # Check if format matches expected template
    expected = _EXPECTED_INFO_TEMPLATE.format(unique_str=unique_str)
    if info != expected:
        log(
            logger,
            "DEBUG",
            3,
            f"Response format changed. Expected: '{expected}', Got: '{info}'",
        )

    return True


def execute(client: HttpClient, unique_str: str) -> bool:
    """
    Execute Step 3: Finalize the upload.

    Sends a POST request to notify the API that all files
    have been uploaded for the given unique_str folder.

    Args:
        client: HTTP client instance.
        unique_str: UUID string from step1.

    Returns:
        True if finalization succeeded, False otherwise.
    """
    step = 3

    payload = {"unique_str": unique_str}

    try:
        response = client.post("/api/proxy/finalize_upload", json_data=payload)

        if response.status_code != 200:
            log(logger, "ERROR", step, f"HTTP {response.status_code}: {response.text}")
            return False

        data = response.json()
    except Exception as e:
        log(logger, "ERROR", step, f"Finalize upload failed: {e}")
        return False

    success = _validate_response(data, unique_str)

    if success:
        log(logger, "INFO", step, "Success")
    else:
        log(logger, "DEBUG", step, "Failed")

    return success
