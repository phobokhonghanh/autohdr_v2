import sys
import os
import logging
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.key_manager import load_keys, add_or_update_key_by_name, s3_storage
from config.settings import Settings
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_persistence():
    settings = Settings.from_env()
    keys_file = settings.keys_file
    
    print(f"--- S3 Persistence Test ---")
    
    # 1. Check current state
    # initial_records = load_keys(keys_file)
    # print(f"Initial records on S3: {len(initial_records)}")
    
    # 2. Add two unique keys
    # timestamp = datetime.now().strftime("%H%M%S")
    # key1_name = f"Key_A_{timestamp}"
    # key2_name = f"Key_B_{timestamp}"
    
    # print(f"\nAdding {key1_name}...")
    # add_or_update_key_by_name(keys_file, key1_name)
    
    # print(f"Adding {key2_name}...")
    # add_or_update_key_by_name(keys_file, key2_name)
    
    # 3. Load again and verify accumulation
    final_records = load_keys(keys_file)
    print(f"\nFinal records on S3: {len(final_records)}")
    
    # Display raw content from S3
    raw_content = s3_storage.get_object(os.path.basename(keys_file))
    print("\n--- Raw Content from S3 ---")
    if raw_content:
        print(raw_content)
    else:
        print("Empty or not found")
    print("---------------------------\n")
    
    # names = [r.name for r in final_records]
    # if key1_name in names and key2_name in names:
    #     print(f"✅ SUCCESS: Both new keys persisted and accumulated!")
    # else:
    #     print(f"❌ FAILURE: Keys missing. Current names: {names}")

if __name__ == "__main__":
    test_persistence()
