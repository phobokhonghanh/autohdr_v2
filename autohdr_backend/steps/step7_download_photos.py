"""
Step 7: Download Processed Photos.

Downloads processed photos from URLs and saves them locally.
Quota limits are checked here, but updates are handled in Step 8.

Input:
    - cleaned_urls from step6
    - unique_str, address, email from pipeline context

Output:
    - List of local file paths
"""

import os
import logging
from typing import List, Optional
from urllib.parse import urlparse

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import log
from core.quota_manager import load_quota, find_or_create_quota, check_quota

logger = logging.getLogger(__name__)


def execute(
    client: HttpClient,
    settings: Settings,
    cleaned_urls: List[str],
    unique_str: str,
    address: str,
    email: str,
    job_id: Optional[str] = None,
    auth_mode: str = "quota"
) -> List[str]:
    """
    Execute Step 7: Download processed photos.
    Check quota limits before download if auth_mode is 'quota'.
    """
    step = 7
    downloaded_paths = []

    if not cleaned_urls:
        log(logger, "INFO", step, "No photos to download")
        return []

    file_count = len(cleaned_urls)

    if auth_mode == "quota":
        # Load and check quota
        records = load_quota(settings.quota_file)
        quota = find_or_create_quota(
            records, email, settings.limit_count, settings.limit_file
        )

        quota_error = check_quota(quota, file_count)
        if quota_error:
            log(logger, "ERROR", step, quota_error)
            return []
    else:
        log(logger, "INFO", step, "Key mode active, skipping quota check before download.")

    # Setup output directory
    output_dir = os.path.join(settings.get_user_dir(email), "temp", job_id or unique_str)
    os.makedirs(output_dir, exist_ok=True)

    log(logger, "INFO", step, f"Downloading {file_count} photos")

    import time
    for i, url in enumerate(cleaned_urls):
        try:
            # Extract filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = f"photo_{i}.jpg"
            
            # Prefix with index to ensure uniqueness (v4.1 fix for collisions)
            unique_filename = f"{i:03d}_{filename}"
            output_path = os.path.join(output_dir, unique_filename)
            
            if i > 0:
                time.sleep(1) # Prevent AWS block
                
            max_retries = 3
            success = False
            for attempt in range(max_retries):
                try:
                    # Download file
                    response = client.get(url, stream=True)
                    response.raise_for_status()
                    
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    success = True
                    break
                except Exception as e:
                    log(logger, "WARNING", step, f"Download failed, attempt {attempt+1}/{max_retries}: {e}")
                    time.sleep(2 * (attempt + 1))
            
            if success:
                downloaded_paths.append(output_path)
                log(logger, "INFO", step, f"Successfully downloaded ({i+1}/{file_count}): {unique_filename}")
            else:
                log(logger, "ERROR", step, f"Failed to download after {max_retries} attempts: {url}")
            
        except Exception as e:
            log(logger, "ERROR", step, f"Unexpected error while downloading {url}: {e}")

    # Notice: Quota update is now handled in Step 8 (Post-Zip)
    return downloaded_paths
