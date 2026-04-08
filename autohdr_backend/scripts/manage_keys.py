"""
Admin script to manage keys.
Usage:
    python manage_keys.py add --key MY_KEY --days 30
    python manage_keys.py list
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import key_manager
from config.settings import Settings

def main():
    parser = argparse.ArgumentParser(description="AutoHDR Backend Key Management")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add or update a key by name")
    add_parser.add_argument("--name", required=True, help="Name associated with the key")
    add_parser.add_argument("--days", type=int, help="Number of days until expiration (optional)")
    add_parser.add_argument("--forever", action="store_true", help="Key never expires")

    # List command
    subparsers.add_parser("list", help="List all keys")

    args = parser.parse_args()
    settings = Settings.from_env()

    if args.command == "add":
        expiry = None
        if not args.forever and args.days:
            expiry_dt = datetime.utcnow() + timedelta(days=args.days)
            expiry = expiry_dt.isoformat() + "Z"
            
        record, status = key_manager.add_or_update_key_by_name(settings.keys_file, args.name, expiry)
        
        if status == "new":
            print(f"--- SUCCESS: Created New Key ---")
            print(f"Name:    {record.name}")
            print(f"Key:     {record.key}")
            print(f"Expires: {record.expires_at if record.expires_at else 'Never'}")
        elif status == "valid":
            print(f"--- NOTICE: Key Still Valid ---")
            print(f"Name:    {record.name}")
            print(f"Key:     {record.key}")
            print(f"Expires: {record.expires_at if record.expires_at else 'Never'}")
        elif status == "updated":
            print(f"--- SUCCESS: Updated Expired/Inactive Key ---")
            print(f"Name:    {record.name}")
            print(f"Key:     {record.key}")
            print(f"Expires: {record.expires_at if record.expires_at else 'Never'}")

    elif args.command == "list":
        keys = key_manager.load_keys(settings.keys_file)
        print(f"{'Name':<15} | {'Key':<12} | {'Active':<8} | {'Expires At'}")
        print("-" * 65)
        for k in keys:
            print(f"{k.name:<15} | {k.key:<12} | {str(k.is_active):<8} | {k.expires_at if k.expires_at else 'Never'}")


if __name__ == "__main__":
    main()
