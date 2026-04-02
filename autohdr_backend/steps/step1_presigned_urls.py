"""
Step 1: Generate Presigned URLs.

Creates a UUID (unique_str), sends file info to AutoHDR API to get
presigned S3 URLs for uploading, and saves input images locally.

Input:
    - List of file paths (images)
    - Address string

Output:
    - unique_str (UUID)
    - List of presigned URLs with filenames

API Endpoint: POST /api/proxy/generate_presigned_urls
"""

import os
import shutil
import uuid
import logging
from typing import List, Tuple, Optional

from core.http_client import HttpClient
from core.logger import log
from models.schemas import PipelineContext, PresignedUrl

logger = logging.getLogger(__name__)


def _generate_unique_str() -> str:
    """
    Generate a random UUID string.

    Returns:
        UUID4 string (e.g., '83b93a60-aef6-409a-9f0d-7c1683c06e3f').
    """
    return str(uuid.uuid4())


def _extract_filenames(file_paths: List[str]) -> List[str]:
    """
    Extract filenames from a list of file paths.

    Args:
        file_paths: List of absolute or relative file paths.

    Returns:
        List of filename strings.
    """
    return [os.path.basename(fp) for fp in file_paths]


def _save_input_files(
    file_paths: List[str],
    unique_str: str,
    address: str,
    input_base_dir: str,
) -> str:
    """
    Move input files to the organized directory structure.

    Creates directory: {input_base_dir}/{unique_str}/{address}/
    and moves all input files there.

    Args:
        file_paths: List of source file paths.
        unique_str: Generated UUID string.
        address: Address string.
        input_base_dir: Base input directory.

    Returns:
        Path to the created input directory.
    """
    input_dir = os.path.join(input_base_dir, unique_str, address)
    os.makedirs(input_dir, exist_ok=True)

    new_paths = []
    for fp in file_paths:
        if os.path.exists(fp):
            dest = os.path.join(input_dir, os.path.basename(fp))
            shutil.move(fp, dest)
            new_paths.append(dest)

    return input_dir, new_paths


def _build_payload(unique_str: str, filenames: List[str]) -> dict:
    """
    Build the request payload for presigned URL generation.

    Args:
        unique_str: UUID string.
        filenames: List of filenames to include.

    Returns:
        Dictionary payload for the API request.
    """
    files = [{"filename": fn, "md5": ""} for fn in filenames]
    return {"unique_str": unique_str, "files": files}


def _parse_presigned_urls(response_data: dict) -> List[PresignedUrl]:
    """
    Parse presigned URLs from the API response.

    Args:
        response_data: JSON response from the API.

    Returns:
        List of PresignedUrl objects.
    """
    urls = []
    for item in response_data.get("presignedUrls", []):
        urls.append(
            PresignedUrl(
                filename=item["filename"],
                url=item["url"],
            )
        )
    return urls


def execute(
    client: HttpClient,
    context: PipelineContext,
    input_dir: str,
) -> Optional[PipelineContext]:
    """
    Execute Step 1: Generate presigned URLs.

    1. Generates a unique_str (UUID)
    2. Extracts filenames from file_paths
    3. Saves input files to {unique_str}/{address}/input
    4. Calls API to get presigned URLs
    5. Updates context with unique_str and presigned_urls

    Args:
        client: HTTP client instance.
        context: Pipeline context with file_paths and address.
        input_dir: Base directory for saving input files.

    Returns:
        Updated PipelineContext on success, or None on failure.
    """
    step = 1

    # Generate unique_str
    context.unique_str = _generate_unique_str()
    log(logger, "INFO", step, f"Generated unique_str: {context.unique_str}")

    # Extract filenames
    context.filenames = _extract_filenames(context.file_paths)
    log(logger, "INFO", step, f"Files: {context.filenames}")

    # Save input files locally and update context with new paths
    input_dir, context.file_paths = _save_input_files(
        context.file_paths, context.unique_str, context.address, input_dir
    )

    # Build and send request
    payload = _build_payload(context.unique_str, context.filenames)
    try:
        response = client.post("/api/proxy/generate_presigned_urls", json_data=payload)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            log(logger, "ERROR", step, f"API returned non-JSON response: {response.text[:500]}")
            return None
    except Exception as e:
        log(logger, "ERROR", step, f"Failed to generate presigned URLs: {e}")
        return None

    # Parse response
    context.presigned_urls = _parse_presigned_urls(data)

    if not context.presigned_urls:
        log(logger, "ERROR", step, "No presigned URLs returned from API")
        return None

    log(
        logger,
        "INFO",
        step,
        f"Success: {len(context.presigned_urls)} presigned URLs",
    )
    return context
