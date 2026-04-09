import requests
import os
import time
import logging
from typing import List, Dict, Optional, Any, Callable
from .utils import get_hwid

logger = logging.getLogger(__name__)

class ApiClient:
    def __init__(self, base_url: Optional[str] = None):
        # Use provided base_url, or fallback to environment variable, then to production URL
        if not base_url:
            base_url = os.getenv("AUTOHDR_API_BASE", "https://autohdr-backend.up.railway.app")
        self.base_url = base_url.rstrip('/')

    def init_session(self, cookie: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Calls /api/session
        """
        payload = {}
        if cookie: payload["cookie"] = cookie
        if email: payload["email"] = email
            
        res = requests.post(f"{self.base_url}/api/session", json=payload)
        res.raise_for_status()
        return res.json()

    def check_key(self, key: str, machine_id: Optional[str] = None) -> bool:
        """
        Calls /api/key/active with machine_id for locking.
        """
        if not machine_id:
            machine_id = get_hwid()
            
        res = requests.post(f"{self.base_url}/api/key/active", json={"key": key, "machine_id": machine_id})
        if res.status_code == 200:
            return res.json().get("valid", False)
        elif res.status_code == 403:
            return False
        res.raise_for_status()
        return False

    def process_photos(self, address: str, file_paths: List[str], key: str, email: str, indoor_model_id: int = 3, machine_id: Optional[str] = None) -> str:
        """
        Calls /api/process to upload files and start processing.
        Includes machine_id for key validation.
        """
        if not machine_id:
            machine_id = get_hwid()
            
        url = f"{self.base_url}/api/process"
        
        # Prepare form data
        data = {
            "address": address,
            "email": email,
            "key": key,
            "machine_id": machine_id,
            "indoor_model_id": indoor_model_id
        }
        
        files_payload = []
        file_handles = []
        try:
            for fp in file_paths:
                f = open(fp, "rb")
                file_handles.append(f)
                files_payload.append(("files", (os.path.basename(fp), f)))
                
            res = requests.post(url, data=data, files=files_payload)
            res.raise_for_status()
            
            return res.json().get("job_id")
        finally:
            for f in file_handles:
                f.close()

    def download_file_with_retry(self, url: str, output_path: str, max_retries: int = 5, on_progress: Optional[Callable] = None) -> bool:
        """
        Downloads a file (e.g. zip) with retry mechanism and slow down.
        """
        if not url.startswith("http"):
            url = self.base_url + url
            
        for attempt in range(max_retries):
            try:
                # Add tiny delay between attempts or download to avoid block if hammering
                if attempt > 0:
                    time.sleep(2 * attempt)
                    
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    total_length = r.headers.get('content-length')
                    
                    with open(output_path, 'wb') as f:
                        if total_length is None:
                            f.write(r.content)
                        else:
                            dl = 0
                            total_length = int(total_length)
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    dl += len(chunk)
                                    f.write(chunk)
                                    if on_progress:
                                        on_progress(dl, total_length)
                return True
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}/{max_retries} failed: {e}")
                
        return False

    def stop_job(self, job_id: str) -> bool:
        """
        Calls /api/stop/{job_id} to cancel a running job.
        """
        try:
            res = requests.post(f"{self.base_url}/api/stop/{job_id}")
            res.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to stop job {job_id}: {e}")
            return False
