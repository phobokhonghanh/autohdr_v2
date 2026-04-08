import pytest
import os
import json
from datetime import datetime, timedelta
from core import key_manager
from models.schemas import KeyRecord

@pytest.fixture
def keys_file(tmp_path):
    return os.path.join(tmp_path, "keys.json")

def test_add_and_check_key_valid(keys_file):
    # Add a key valid for 1 hour
    future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    key_manager.add_key(keys_file, "valid_key", future_time)
    
    assert key_manager.check_key(keys_file, "valid_key") is True

def test_add_and_check_key_expired(keys_file):
    # Add a key expired 1 hour ago
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    key_manager.add_key(keys_file, "expired_key", past_time)
    
    assert key_manager.check_key(keys_file, "expired_key") is False

def test_add_and_check_key_no_expiration(keys_file):
    # Add a key with no expiration
    key_manager.add_key(keys_file, "infinite_key", None)
    
    assert key_manager.check_key(keys_file, "infinite_key") is True

def test_inactive_key(keys_file):
    key_manager.add_key(keys_file, "inactive_key", None)
    
    # Manually turn it off
    records = key_manager.load_keys(keys_file)
    records[0].is_active = False
    key_manager.save_keys(keys_file, records)
    
    assert key_manager.check_key(keys_file, "inactive_key") is False
