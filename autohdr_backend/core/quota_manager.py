"""
Quota Manager - Shared utilities for tracking user download quotas.
"""

import json
import os
import logging
from typing import List, Optional
from models.schemas import QuotaRecord

logger = logging.getLogger(__name__)

def load_quota(quota_file: str) -> List[dict]:
    """Load the quota records from the JSON file."""
    if not os.path.exists(quota_file):
        return []
    try:
        with open(quota_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_quota(quota_file: str, records: List[dict]) -> None:
    """Save quota records to the JSON file."""
    os.makedirs(os.path.dirname(quota_file) if os.path.dirname(quota_file) else ".", exist_ok=True)
    with open(quota_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def find_or_create_quota(
    records: List[dict],
    email: str,
    limit_count: int,
    limit_file: int,
) -> QuotaRecord:
    """Find an existing quota record or create a new one."""
    for record in records:
        if record.get("email") == email:
            return QuotaRecord.from_dict(record)
    return QuotaRecord(email=email, limit_count=limit_count, limit_file=limit_file)

def update_quota_in_records(records: List[dict], quota: QuotaRecord) -> List[dict]:
    """Update or insert a quota record in the list."""
    for i, record in enumerate(records):
        if record.get("email") == quota.email:
            records[i] = quota.to_dict()
            return records
    records.append(quota.to_dict())
    return records

def check_quota(quota: QuotaRecord, file_count: int) -> Optional[str]:
    """Check if the download is within quota limits."""
    if file_count > quota.limit_file:
        return f"Số file vượt quá limit file ({file_count} > {quota.limit_file})"
    remaining = quota.limit_count - (quota.count + file_count)
    if remaining < 0:
        return (
            f"Số file vượt quá limited, bạn có thể tải nó trong phần xem ảnh đã xử lý "
            f"(count={quota.count}, download={file_count}, limit={quota.limit_count})"
        )
    return None

def update_user_quota(quota_file: str, email: str, success_count: int, unique_str: str):
    """Updates the user quota record in the JSON file."""
    records = load_quota(quota_file)
    # We assume the record exists or we create it with defaults
    # In Step 8, we should have the limits from Settings
    # But for a simple update, we just need the email
    for record in records:
        if record.get("email") == email:
            quota = QuotaRecord.from_dict(record)
            quota.count += success_count
            if unique_str not in quota.unique_str:
                quota.unique_str.append(unique_str)
            records = update_quota_in_records(records, quota)
            save_quota(quota_file, records)
            return quota
    return None
