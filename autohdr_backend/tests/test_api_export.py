import requests
import json
import os
from dotenv import load_dotenv

# Load settings from .env
load_dotenv()
ADMIN_PASSWORD = os.getenv("AUTOHDR_PROXY_PASS", "kynz3mn88kj")
API_URL = "http://127.0.0.1:8000/api/admin/keys/export"

def test_export_api():
    print(f"Testing Admin Export API at {API_URL}...")
    
    payload = {
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Export successful!")
            
            # Save the exported data to a file for verification
            filename = "exported_keys_test.json"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"File saved as: {filename}")
            
            # Print the content
            print("\n--- Exported Data ---")
            data = response.json()
            print(json.dumps(data, indent=2))
            print("---------------------\n")
            
        else:
            print(f"❌ FAILURE: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_export_api()
