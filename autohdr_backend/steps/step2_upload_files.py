"""
Step 2: Upload Files to S3.

Uses the presigned URLs from Step 1 to upload binary file content
to S3 via PUT requests.

Input:
    - presigned_urls: List of {filename, url} from step1
    - file_paths: List of local file paths

Output:
    - True if all uploads succeed (status 200), False otherwise

API: PUT to each presigned S3 URL
"""

import os
import time
import logging
from typing import List

from core.http_client import HttpClient
from core.logger import log
from models.schemas import PipelineContext, PresignedUrl

logger = logging.getLogger(__name__)


def _find_file_path(filename: str, file_paths: List[str]) -> str:
    """
    Find the local file path matching a filename.

    Args:
        filename: The filename to find.
        file_paths: List of local file paths to search.

    Returns:
        The matching file path.

    Raises:
        FileNotFoundError: If no matching file path is found.
    """
    for fp in file_paths:
        if os.path.basename(fp) == filename:
            return fp
    raise FileNotFoundError(f"File not found for filename: {filename}")


def _read_file_binary(file_path: str) -> bytes:
    """
    Read a file in binary mode.

    Args:
        file_path: Path to the file.

    Returns:
        Binary content of the file.
    """
    with open(file_path, "rb") as f:
        return f.read()


import time

def _upload_single_file(
    client: HttpClient,
    presigned_url: PresignedUrl,
    file_data: bytes,
    max_retries: int = 3
) -> bool:
    """
    Upload a single file to S3 using a presigned URL with retries.
    """
    for attempt in range(max_retries):
        try:
            response = client.put_binary(presigned_url.url, data=file_data)
            if response.status_code == 200:
                return True
            log(logger, "WARNING", 2, f"Upload status {response.status_code}, retrying {attempt+1}/{max_retries}")
        except Exception as e:
            log(logger, "WARNING", 2, f"Upload exception: {e}, retrying {attempt+1}/{max_retries}")
        time.sleep(2 * (attempt + 1))  # exponential backoff
    return False

def execute(client: HttpClient, context: PipelineContext) -> bool:
    """
    Execute Step 2: Upload all files to S3.

    Iterates through presigned URLs, reads corresponding local files
    as binary, and uploads each to S3 via PUT request.
    Includes a 2-second delay between each file upload.

    Args:
        client: HTTP client instance.
        context: Pipeline context with presigned_urls and file_paths.

    Returns:
        True if ALL uploads succeed, False if any fails.
    """
    step = 2

    if not context.presigned_urls:
        log(logger, "ERROR", step, "No presigned URLs available for upload")
        return False

    all_success = True

    for i, presigned_url in enumerate(context.presigned_urls):
        # Add 2s delay between files (v5 requirement)
        if i > 0:
            time.sleep(1)
            
        filename = presigned_url.filename

        try:
            file_path = _find_file_path(filename, context.file_paths)
            file_data = _read_file_binary(file_path)
        except (FileNotFoundError, IOError) as e:
            log(logger, "ERROR", step, f"Failed to read file {filename}: {e}")
            all_success = False
            continue

        # Add stagger to prevent throttling
        if i > 0:
            time.sleep(1)
            
        success = _upload_single_file(client, presigned_url, file_data)

        if success:
            log(logger, "INFO", step, f"Success: {filename}")
        else:
            log(logger, "ERROR", step, f"Failed: {filename}")
            all_success = False

    return all_success
