"""
Step 8: Zip Processed Photos & Cleanup.

Zips multiple processed photos into a single archive and manages 
temporary storage cleanup.

Requirement v4.1: 
- Zip multiple files into hdr_{job_id}.zip in resources/users/{email}/temp/{date}/
- Delete the original temp/{job_id}/ folder after zipping.
- Automatically delete temp data older than 3 days.
"""

import os
import shutil
import zipfile
import logging
from datetime import datetime, timedelta
from typing import List
from urllib.parse import quote

from config.settings import Settings
from core.logger import log

logger = logging.getLogger(__name__)

def execute(
    settings: Settings,
    email: str,
    job_id: str,
    local_paths: List[str],
    unique_str: str = ""
) -> List[str]:
    """
    Execute Step 8: Zip files and cleanup temporary storage.

    Args:
        settings: Application settings.
        email: User email address.
        job_id: The unique ID for this processing job.
        local_paths: List of local paths to the downloaded photos.
        unique_str: UUID string (deprecated here, moved to app.py finally).

    Returns:
        List containing the static path to the result (zip or single file).
    """
    step = 8
    
    if not local_paths:
        return []

    # 1. Determine local result and zipping logic
    final_results = []
    log(logger, "INFO", step, f"Step 8 received {len(local_paths)} files to process")

    try:
        if len(local_paths) == 1:
            file_path = local_paths[0]
            # Replace backwards slashes natively on Windows, though this is primarily posix.
            relative_path = os.path.relpath(file_path, "resources").replace("\\", "/")
            final_results = [f"/resources/{quote(relative_path)}"]
            log(logger, "INFO", step, f"Returning single file: {final_results[0]}")
        else:
            # Multiple files: Zip them
            log(logger, "INFO", step, f"Zipping {len(local_paths)} photos into hdr_{job_id}.zip")
            zip_filename = f"hdr_{job_id}.zip"
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            # Save zip in resources/users/{email}/temp/{date}/
            zip_dir = os.path.join(settings.get_user_dir(email), "temp", today_str)
            os.makedirs(zip_dir, exist_ok=True)
            
            zip_path = os.path.join(zip_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in local_paths:
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
            
            # Delete original temp job folder: resources/users/{email}/temp/{job_id}
            temp_job_dir = os.path.dirname(local_paths[0])
            if os.path.exists(temp_job_dir) and job_id in temp_job_dir:
                shutil.rmtree(temp_job_dir)
                log(logger, "INFO", step, f"Cleaned up temporary job folder: {job_id}")

            relative_zip_path = os.path.relpath(zip_path, "resources").replace("\\", "/")
            final_results = [f"/resources/{quote(relative_zip_path)}"]
            log(logger, "INFO", step, f"Returning zip file: {final_results[0]}")

    except Exception as e:
        log(logger, "ERROR", step, f"Zip process failed: {e}")
        # Fallback if zip fails
        final_results = [f"/resources/{quote(os.path.relpath(p, 'resources').replace(chr(92), '/'))}" for p in local_paths]
        log(logger, "INFO", step, f"Fallback: returning {len(final_results)} individual files")

    return final_results

def cleanup_stale_data(settings: Settings, email: str, days: int = 3):
    """
    Delete folders in resources/users/{email}/temp/{date} that are older than X days.
    """
    try:
        temp_base = os.path.join(settings.get_user_dir(email), "temp")
        if not os.path.exists(temp_base):
            return

        threshold_date = datetime.now() - timedelta(days=days)
        
        for item in os.listdir(temp_base):
            item_path = os.path.join(temp_base, item)
            if not os.path.isdir(item_path):
                continue
            
            # Check if name is a date (YYYY-MM-DD)
            try:
                item_date = datetime.strptime(item, "%Y-%m-%d")
                if item_date < threshold_date:
                    shutil.rmtree(item_path)
                    log(logger, "INFO", 0, f"Cleaned up stale temp folder: {item}")
            except ValueError:
                # Not a date folder (like a job_id folder being currently used), skip
                pass
    except Exception as e:
        log(logger, "ERROR", 0, f"Cleanup failed: {e}")
