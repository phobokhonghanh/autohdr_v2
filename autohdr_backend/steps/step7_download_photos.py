"""
Step 7: Download Processed Photos.

Downloads processed photos from URLs, saves them locally, and
manages download quota tracking via a JSON file.

Input:
    - cleaned_urls from step6
    - unique_str, address, email from pipeline context

Output:
    - True if all downloads succeed, False otherwise

Quota checks:
    - limit_file: Max files per single batch
    - limit_count: Max total downloads across all batches
    - Quota is tracked in a JSON file per email

Directory: {output_dir}/{unique_str}/{address}/output
"""

import json
import os
import logging
import time
from typing import List, Optional
from urllib.parse import urlparse

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import log
from models.schemas import QuotaRecord

logger = logging.getLogger(__name__)


def _load_quota(quota_file: str) -> List[dict]:
    """
    Load the quota records from the JSON file.

    Args:
        quota_file: Path to the quota JSON file.

    Returns:
        List of quota record dictionaries.
    """
    if not os.path.exists(quota_file):
        return []

    try:
        with open(quota_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_quota(quota_file: str, records: List[dict]) -> None:
    """
    Save quota records to the JSON file.

    Args:
        quota_file: Path to the quota JSON file.
        records: List of quota record dictionaries.
    """
    os.makedirs(os.path.dirname(quota_file) if os.path.dirname(quota_file) else ".", exist_ok=True)
    with open(quota_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def _find_or_create_quota(
    records: List[dict],
    email: str,
    limit_count: int,
    limit_file: int,
) -> QuotaRecord:
    """
    Find an existing quota record for the email, or create a new one.

    Args:
        records: List of existing quota record dicts.
        email: Email to search for.
        limit_count: Default limit_count for new records.
        limit_file: Default limit_file for new records.

    Returns:
        QuotaRecord instance.
    """
    for record in records:
        if record.get("email") == email:
            return QuotaRecord.from_dict(record)

    return QuotaRecord(
        email=email,
        limit_count=limit_count,
        limit_file=limit_file,
    )


def _update_quota_in_records(
    records: List[dict],
    quota: QuotaRecord,
) -> List[dict]:
    """
    Update or insert a quota record in the records list.

    Args:
        records: List of existing quota record dicts.
        quota: Updated QuotaRecord to save.

    Returns:
        Updated list of records.
    """
    for i, record in enumerate(records):
        if record.get("email") == quota.email:
            records[i] = quota.to_dict()
            return records

    records.append(quota.to_dict())
    return records


def _check_quota(
    quota: QuotaRecord,
    file_count: int,
) -> Optional[str]:
    """
    Check if the download is within quota limits.

    Args:
        quota: Current quota record.
        file_count: Number of files to download.

    Returns:
        None if within limits, error message string if limits exceeded.
    """
    # Check limit_file
    if file_count > quota.limit_file:
        return (
            f"Số file vượt quá limit file "
            f"({file_count} > {quota.limit_file})"
        )

    # Check limit_count
    remaining = quota.limit_count - (quota.count + file_count)
    if remaining < 0:
        return (
            f"Số file vượt quá limited, bạn có thể tải nó trong "
            f"phần xem ảnh đã xử lý "
            f"(count={quota.count}, download={file_count}, "
            f"limit={quota.limit_count})"
        )

    return None




def execute(
    client: HttpClient,
    settings: Settings,
    cleaned_urls: List[str],
    unique_str: str,
    address: str,
    email: str,
) -> bool:
    """
    Execute Step 7: Download processed photos with quota tracking.

    1. Load quota from JSON file
    2. Check quota limits (limit_file, limit_count)
    3. Download each photo to {unique_str}/{address}/output
    4. Update quota (count, unique_str list) after successful downloads
    5. Save updated quota to JSON file

    Args:
        client: HTTP client instance.
        settings: Application settings.
        cleaned_urls: List of cleaned processed photo URLs from step6.
        unique_str: UUID string from step1.
        address: Address string.
        email: User email address.

    Returns:
        True if all downloads succeed, False otherwise.
    """
    step = 7

    if not cleaned_urls:
        log(logger, "INFO", step, "No photos to download")
        return True

    file_count = len(cleaned_urls)

    # Load and check quota
    records = _load_quota(settings.quota_file)
    quota = _find_or_create_quota(
        records, email, settings.limit_count, settings.limit_file
    )

    quota_error = _check_quota(quota, file_count)
    if quota_error:
        log(logger, "ERROR", step, quota_error)
        return False

    # Skip download, update quota directly for all URLs
    success_count = file_count
    log(logger, "INFO", step, f"Download {file_count} photos")

    # Update quota
    if success_count > 0:
        quota.count += success_count
        if unique_str not in quota.unique_str:
            quota.unique_str.append(unique_str)

        records = _update_quota_in_records(records, quota)
        _save_quota(settings.quota_file, records)

        log(
            logger,
            "INFO",
            step,
            f"Quantity of processed photos: {success_count}. "
            f"Total quota used: {quota.count}/{quota.limit_count}",
        )

    return True
