import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.key_manager import load_keys, save_keys, add_or_update_key_by_name
from models.schemas import KeyRecord
from config.settings import Settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_s3_keys():
    settings = Settings.from_env()
    keys_file = settings.keys_file
    
    print(f"Testing S3 Key Storage...")
    print(f"Target Bucket: {settings.s3_bucket}")
    print(f"Target Key (S3 Object Name): {os.path.basename(keys_file)}")
    
    # 1. Add/Update a test key with expiration
    test_name = "AI_Test_Key_With_Expiry"
    from datetime import datetime, timedelta
    expiry_date = (datetime.now() + timedelta(days=365)).isoformat()
    
    print(f"\n1. Adding/Updating key for: {test_name}")
    record, status = add_or_update_key_by_name(keys_file, test_name, expires_at=expiry_date)
    print(f"Status: {status}")
    print(f"Record: {record.to_dict()}")
    
    # 2. Load keys
    print(f"\n2. Loading keys from S3...")
    records = load_keys(keys_file)
    print(f"Total records found: {len(records)}")
    for r in records:
        print(f" - {r.name}: {r.key} (Active: {r.is_active})")
        
    # 3. Verify the added key is there
    found = any(r.name == test_name for r in records)
    if found:
        print(f"\n✅ SUCCESS: Test key '{test_name}' found in S3 storage!")
    else:
        print(f"\n❌ FAILURE: Test key '{test_name}' NOT found in S3 storage.")

if __name__ == "__main__":
    test_s3_keys()
