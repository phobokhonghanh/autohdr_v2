"""
Step 4: Associate and Run Processing.

Sends user info and unique_str to the AutoHDR API to trigger
HDR image processing.

Input:
    - unique_str, email, firstname, lastname, address, files_count

Output:
    - True if success == true in response, False otherwise

API Endpoint: POST /api/inference/associate-and-run
"""

import logging
from typing import Optional

from core.http_client import HttpClient
from core.logger import log

logger = logging.getLogger(__name__)


def _build_payload(
    unique_str: str,
    email: str,
    firstname: str,
    lastname: str,
    address: str,
    files_count: int,
) -> dict:
    """
    Build the request payload for associate-and-run.

    Args:
        unique_str: UUID string from step1.
        email: User email.
        firstname: User first name.
        lastname: User last name.
        address: Photoshoot address.
        files_count: Number of files uploaded.

    Returns:
        Dictionary payload matching the API specification.
    """
    return {
        "unique_str": unique_str,
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "address": address,
        "spoofId": None,
        "smartlook_url": None,
        "indoor_model_id": 1,
        "outdoor_model_id": None,
        "files_count": files_count,
        "grass_replacement": False,
        "perspective_correction": True,
        "special_attention": False,
        "declutter": False,
        "photoshoot_id": None,
    }


def execute(
    client: HttpClient,
    unique_str: str,
    email: str,
    firstname: str,
    lastname: str,
    address: str,
    files_count: int,
) -> bool:
    """
    Execute Step 4: Associate files with user and trigger processing.

    Sends a POST request to the associate-and-run endpoint with user
    information and file details. The API triggers HDR processing.

    Args:
        client: HTTP client instance.
        unique_str: UUID string from step1.
        email: User email address.
        firstname: User first name.
        lastname: User last name.
        address: Photoshoot address.
        files_count: Number of files uploaded.

    Returns:
        True if response.success is True, False otherwise.
    """
    step = 4

    payload = _build_payload(
        unique_str, email, firstname, lastname, address, files_count
    )

    try:
        response = client.post(
            "/api/inference/associate-and-run", json_data=payload
        )

        if response.status_code != 200:
            log(logger, "ERROR", step, f"HTTP {response.status_code}: {response.text}")
            log(logger, "ERROR", step, f"Payload: {payload}")
            return False

        data = response.json()
    except Exception as e:
        log(logger, "ERROR", step, f"Associate-and-run failed: {e}")
        log(logger, "ERROR", step, f"Payload: {payload}")
        return False

    success = data.get("success", False)

    if success:
        log(logger, "INFO", step, "Success")
    else:
        log(
            logger,
            "DEBUG",
            step,
            f"Failed to trigger processing. Response: {data}, Payload: {payload}",
        )

    return success
