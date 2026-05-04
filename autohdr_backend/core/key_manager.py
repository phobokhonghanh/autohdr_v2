"""
Key Manager - Utilities for tracking and validating executable keys.
"""

import json
import os
import logging
from typing import List, Optional
from models.schemas import KeyRecord
from config.settings import Settings
from core.s3_storage import S3Storage

logger = logging.getLogger(__name__)

# Initialize S3 Storage
settings = Settings.from_env()
s3_storage = S3Storage(settings)

def load_keys(keys_file: str) -> List[KeyRecord]:
    """Load the key records from S3."""
    key = os.path.basename(keys_file)
    try:
        content = s3_storage.get_object(key)
        
        # Distinguish between "File not found" and "S3 Error"
        if content is None:
            # If s3_storage.get_object returns None, it means:
            # 1. NoSuchKey (handled by returning None in s3_storage)
            # 2. OR All retries failed (auth error, network error, etc.)
            
            # We can't easily tell here without more info from s3_storage,
            # but let's assume if it's None, we should at least check if we can continue.
            logger.warning(f"Could not retrieve S3 key: {key}. It might not exist or there's an error.")
            return []
        
        logger.info(f"Successfully loaded content for S3 key: {key} (length: {len(content)})")
        data = json.loads(content)
        records = [KeyRecord.from_dict(item) for item in data]
        logger.info(f"Parsed {len(records)} records from S3 key: {key}")
        return records
    except Exception as e:
        logger.error(f"Critical failure loading keys from S3 ({key}): {e}", exc_info=True)
        # Instead of returning [], we should probably raise here to prevent data loss
        # during a subsequent save_keys call.
        raise

def save_keys(keys_file: str, records: List[KeyRecord]) -> None:
    """Save key records to S3."""
    key = os.path.basename(keys_file)
    try:
        content = json.dumps([record.to_dict() for record in records], ensure_ascii=False, indent=2)
        success = s3_storage.put_object(key, content)
        if not success:
            raise IOError(f"Failed to save keys to S3 after retries.")
    except Exception as e:
        logger.error(f"Failed to save keys to S3 ({key}): {e}")
        raise # We raise here to let the caller know it failed

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

def delete_key(keys_file: str, key_to_delete: str) -> bool:
    """Delete a key by its name or key value.
    Returns True if deleted, False if not found.
    """
    records = load_keys(keys_file)
    original_count = len(records)
    records = [r for r in records if r.key != key_to_delete and r.name != key_to_delete]
    
    if len(records) < original_count:
        save_keys(keys_file, records)
        return True
    return False

def import_keys(keys_file: str, new_keys_data: list) -> int:
    """Import valid keys from JSON array, skipping existing records by name.
    Targeting uniqueness by 'name' as requested.
    Returns the number of keys successfully imported.
    """
    records = load_keys(keys_file)
    existing_names = {r.name for r in records if r.name}
    
    imported_count = 0
    for item in new_keys_data:
        try:
            if not isinstance(item, dict):
                continue
            new_record = KeyRecord.from_dict(item)
            if new_record.name and new_record.name not in existing_names:
                records.append(new_record)
                existing_names.add(new_record.name)
                imported_count += 1
        except Exception as e:
            logger.warning(f"Failed to import key item {item}: {e}")
            continue
            
    if imported_count > 0:
        save_keys(keys_file, records)
        
    return imported_count
