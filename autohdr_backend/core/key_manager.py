"""
Key Manager - Utilities for tracking and validating executable keys.
"""

import json
import os
import logging
from typing import List, Optional
from models.schemas import KeyRecord

logger = logging.getLogger(__name__)

def load_keys(keys_file: str) -> List[KeyRecord]:
    """Load the key records from the JSON file."""
    if not os.path.exists(keys_file):
        return []
    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [KeyRecord.from_dict(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []

def save_keys(keys_file: str, records: List[KeyRecord]) -> None:
    """Save key records to the JSON file."""
    os.makedirs(os.path.dirname(keys_file) if os.path.dirname(keys_file) else ".", exist_ok=True)
    with open(keys_file, "w", encoding="utf-8") as f:
        json.dump([record.to_dict() for record in records], f, ensure_ascii=False, indent=2)

import random
import string

def random_key_string(length: int = 10) -> str:
    """Generate a random alphanumeric string of a given length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def check_key(keys_file: str, key_str: str, machine_id: Optional[str] = None) -> bool:
    """
    Check if the given key is valid, not expired, and matches machine_id.
    If machine_id is provided and the key has no machine_id assigned yet, 
    it will be assigned (activation/first-use binding).
    """
    records = load_keys(keys_file)
    for record in records:
        if record.key == key_str:
            if record.is_expired():
                logger.warning(f"Key expired or inactive: {key_str}")
                return False
            
            # Machine locking logic
            if record.machine_id:
                if machine_id and record.machine_id != machine_id:
                    logger.warning(f"Key {key_str} already used on another machine: {record.machine_id} != {machine_id}")
                    return False
            elif machine_id:
                # First use: Bind machine_id
                record.machine_id = machine_id
                save_keys(keys_file, records)
                logger.info(f"Key {key_str} bound to machine: {machine_id}")
                
            return True
                
    logger.warning(f"Key not found: {key_str}")
    return False

def add_or_update_key_by_name(keys_file: str, name: str, expires_at: Optional[str] = None):
    """
    Add or update a key by name.
    Returns: (record, status_code)
    status_code: 
      'new': Key was created
      'valid': Key exists and is still valid
      'updated': Key exists but was expired/inactive, now updated
    """
    records = load_keys(keys_file)
    for record in records:
        if record.name == name:
            if not record.is_expired():
                return record, "valid"
            else:
                # Update expiry for existing name
                record.expires_at = expires_at
                record.is_active = True
                save_keys(keys_file, records)
                return record, "updated"
            
    # Not found: Generate new 10-char key
    new_key = random_key_string(10)
    new_record = KeyRecord(key=new_key, name=name, is_active=True, expires_at=expires_at)
    records.append(new_record)
    save_keys(keys_file, records)
    return new_record, "new"
