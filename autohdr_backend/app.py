"""
AutoHDR Backend API Service.

Exposes the AutoHDR pipeline as a REST API for the frontend.
Provides endpoints for session validation, processing, and log retrieval.
"""

import os
import json
import uuid
import logging
import asyncio
import shutil
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import zipfile
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import LogCollector, get_logger, log, add_file_handler, job_id_context
from core import quota_manager
from core.retry import retry_with_backoff
from models.schemas import PipelineContext
from steps import (
    step0_session,
    step1_presigned_urls,
    step2_upload_files,
    step3_finalize_upload,
    step4_associate_and_run,
    step5_poll_status,
    step6_get_processed_urls,
    step7_download_photos,
    step8_zip_files,
)

app = FastAPI(title="AutoHDR API Service")
logger = get_logger("autohdr_api")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hdr-trick.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves the resources directory statically
app.mount("/resources", StaticFiles(directory="resources"), name="resources")

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        log(logger, "ERROR", 0, f"Lỗi hệ thống không xác định: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(e)}
        )

# Global dictionary to store logs for each run
# In a production app, use Redis or a database.
processing_jobs: Dict[str, Dict] = {}

class SessionRequest(BaseModel):
    cookie: Optional[str] = None
    email: Optional[str] = None

class ProcessRequest(BaseModel):
    cookie: Optional[str] = None
    email: Optional[str] = None
    address: str
    indoor_model_id: Optional[int] = 3

@app.post("/api/session")
async def resolve_session(req: SessionRequest):
    """Resolve session info from cookie or email."""
    settings = Settings.from_env()
    resolved_settings = step0_session.execute(
        settings=settings,
        cookie=req.cookie,
        email=req.email,
    )
    
    if not resolved_settings.cookie:
        raise HTTPException(status_code=401, detail="Authentication failed or expired")
    
    return {
        "email": resolved_settings.email,
        "user_id": resolved_settings.user_id,
        "firstname": resolved_settings.firstname,
        "lastname": resolved_settings.lastname,
    }

class KeyRequest(BaseModel):
    key: str
    machine_id: Optional[str] = None

@app.post("/api/key/active")
async def verify_key(req: KeyRequest):
    """Verify if a key is active and matches machine_id (locking)."""
    settings = Settings.from_env()
    from core import key_manager
    is_valid = key_manager.check_key(settings.keys_file, req.key, req.machine_id)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Key is invalid, expired, or used on another machine")
    return {"status": "ok", "valid": True}


# --- Admin API (Key Management) ---

class AdminKeyListRequest(BaseModel):
    password: str

class AdminKeyAddRequest(BaseModel):
    name: str
    password: str
    days: Optional[int] = 30
    forever: Optional[bool] = False

@app.post("/api/admin/keys/list")
async def admin_list_keys(req: AdminKeyListRequest):
    """List all keys (Admin only)."""
    settings = Settings.from_env()
    if req.password != settings.proxy_pass:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin password")
    
    from core import key_manager
    keys = key_manager.load_keys(settings.keys_file)
    return [k.to_dict() for k in keys]

@app.post("/api/admin/keys/add")
async def admin_add_key(req: AdminKeyAddRequest):
    """Add or update a key (Admin only)."""
    settings = Settings.from_env()
    if req.password != settings.proxy_pass:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin password")
    
    from core import key_manager
    from datetime import datetime, timedelta
    
    expiry = None
    if not req.forever and req.days:
        expiry_dt = datetime.utcnow() + timedelta(days=req.days)
        expiry = expiry_dt.isoformat() + "Z"
        
    record, status = key_manager.add_or_update_key_by_name(settings.keys_file, req.name, expiry)
    return {
        "status": status,
        "record": record.to_dict()
    }


def run_pipeline_task(job_id: str, file_paths: List[str], address: str, settings: Settings, cookie: Optional[str], email: Optional[str], indoor_model_id: int = 3, key: Optional[str] = None):
    """Background task to run the full pipeline and capture logs in a thread."""
    # Set the job_id in context for logging isolation (v5)
    token = job_id_context.set(job_id)
    
    job = processing_jobs[job_id]
    job["status"] = "processing"
    
    # Setup log collector
    collector = LogCollector(job_id=job_id)
    root_logger = logging.getLogger()
    
    # Ensure root logger correctly captures INFO logs from all modules
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(collector)
    
    # Start capturing to user-specific and dated log file
    user_email = email or settings.email
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(settings.get_user_logs_dir(user_email), f"{today}.log")
    file_handler = add_file_handler(root_logger, log_path, mode="a", job_id=job_id)
    
    # Add a starting separator for this run in the file
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"Run ID: {job_id} | Time: {datetime.now().strftime('%H:%M:%S')} | Address: {address}\n")
        f.write(f"{'='*50}\n")
    
    # Crucial: Point job["logs"] to the collector's list for realtime updates
    job["logs"] = collector.records
    
    try:
        # File count limit check at the start of pipeline (v5)
        if len(file_paths) > settings.limit_file:
             raise Exception(f"Vượt quá giới hạn số lượng file ({len(file_paths)}/{settings.limit_file})")

        # Step 0 (Execute again to capture logs in this job context)
        log(root_logger, "INFO", 0, "Init session")
        settings = retry_with_backoff(step0_session.execute, root_logger, 0, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 0", True, settings, cookie, email)
        if not settings or not settings.cookie: raise Exception("Step 0 failed: Not found cookie after retries")

        # Initialize Context
        context = PipelineContext(
            file_paths=file_paths,
            address=address,
            email=settings.email,
            firstname=settings.firstname,
            lastname=settings.lastname,
            user_id=settings.user_id,
            auth_mode="key" if key else "quota"
        )
        
        client = HttpClient(settings)
        
        # Step 1
        log(root_logger, "INFO", 1, "Generate presigned URLs")
        context = retry_with_backoff(step1_presigned_urls.execute, root_logger, 1, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 1", True, client, context, settings.get_user_input_dir(user_email))
        if not context: raise Exception("Step 1 failed after retries")

        # Step 2
        log(root_logger, "INFO", 2, "Upload files to S3")
        if not retry_with_backoff(step2_upload_files.execute, root_logger, 2, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 2", True, client, context): raise Exception("Step 2 failed after retries")
        
        # Step 3
        log(root_logger, "INFO", 3, "Finalize upload")
        if not step3_finalize_upload.execute(client, context.unique_str): raise Exception("Step 3 failed")
        
        # Cleanup input files locally
        for fp in file_paths:
            if os.path.exists(fp): 
                try: os.remove(fp)
                except Exception as e: pass
        log(root_logger, "INFO", 3, "Cleaned up local temporary input files")
        
        # Step 4
        log(root_logger, "INFO", 4, "Run processing pipeline")
        if not retry_with_backoff(step4_associate_and_run.execute, root_logger, 4, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 4", True,
            client=client, unique_str=context.unique_str, email=context.email,
            firstname=context.firstname, lastname=context.lastname,
            address=context.address, files_count=len(context.filenames),
            indoor_model_id=indoor_model_id
        ): raise Exception("Step 4 failed after retries")
        
        # Step 5
        log(root_logger, "INFO", 5, "Poll processing status")
        photoshoot_id = retry_with_backoff(step5_poll_status.execute, root_logger, 5, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 5", True, client, settings, context.unique_str, context.address)
        if not photoshoot_id: raise Exception("Step 5 failed after retries")
        context.photoshoot_id = photoshoot_id
        
        # Step 6
        log(root_logger, "INFO", 6, "Get processed URLs")
        context.processed_urls = retry_with_backoff(step6_get_processed_urls.execute, root_logger, 6, settings.retry_max_attempts, settings.retry_initial_delay, settings.retry_backoff_factor, "Retrying Step 6", True,
            client, context.photoshoot_id, context.unique_str, context.filenames, settings.photoshoot_page_size
        )
        if not context.processed_urls: raise Exception("Step 6 failed after retries")
        
        if key:
            # EXE Mode: Return direct URLs, skip server-side download
            log(root_logger, "INFO", 7, "EXE mode: Returning direct S3 URLs to client. Skipping server download/zip.")
            result_urls = context.processed_urls
        else:
            # Web Mode: Server downloads and zips
            # Step 7
            log(root_logger, "INFO", 7, "Download processed photos")
            downloaded_paths = step7_download_photos.execute(
                client, settings, context.processed_urls, context.unique_str, context.address, context.email, job_id, context.auth_mode
            )
            if not downloaded_paths: raise Exception("Step 7 failed: No photos downloaded")
            
            log(root_logger, "INFO", 8, "Zipping and cleaning up")
            result_urls = step8_zip_files.execute(settings, user_email, job_id, downloaded_paths, context.unique_str)
            if not result_urls: raise Exception("Step 8 failed: No results generated")
            
            # Cleanup stale temp data (3 days policy)
            step8_zip_files.cleanup_stale_data(settings, user_email, days=3)
        
        job["status"] = "completed"
        job["results"] = result_urls
        job["unique_str"] = context.unique_str
        
    except Exception as e:
        log(root_logger, "ERROR", 0, f"Pipeline failed: {str(e)}")
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        # Update Quota: ONLY after successful completion and result delivery
        # We also need to ensure 'context' was successfully initialized
        if job.get("status") == "completed" and job.get("results") and 'context' in locals():
            if getattr(context, 'auth_mode', 'quota') == 'quota':
                try:
                    # Use the count of processed URLs (what the user actually gets)
                    success_count = len(context.processed_urls)
                    target_email = user_email if 'user_email' in locals() else settings.email
                    quota_manager.update_user_quota(settings.quota_file, target_email, success_count, context.unique_str)
                    log(root_logger, "INFO", 0, f"Quota updated in finally: +{success_count} photos for {target_email}")
                except Exception as e:
                    log(root_logger, "ERROR", 0, f"Failed to update quota in finally: {e}")
            else:
                log(root_logger, "INFO", 0, "Key mode used, skipping quota update.")

        root_logger.removeHandler(collector)
        root_logger.removeHandler(file_handler)
        file_handler.close()
        
        # Reset context
        job_id_context.reset(token)
        
        # Add ending separator to the file
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = os.path.join(settings.get_user_logs_dir(user_email), f"{today}.log")
        with open(log_path, "a", encoding="utf-8") as f:
            status_text = job.get('status', 'unknown').upper()
            f.write(f"\nRun ID: {job_id} | Status: {status_text}\n")
            f.write(f"{'='*50}\n\n")

@app.post("/api/process")
async def process_photos(
    background_tasks: BackgroundTasks,
    address: str = Form(...),
    cookie: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    key: Optional[str] = Form(None),
    machine_id: Optional[str] = Form(None),
    indoor_model_id: Optional[int] = Form(3),
    files: List[UploadFile] = File(...)
):
    """Upload files locally and trigger the pipeline in background."""
    log(logger, "INFO", 0, f"Nhận yêu cầu xử lý từ: {email or 'unknown'}, mode: {'KEY' if key else 'QUOTA'}")
    
    settings = Settings.from_env()
    
    # If key is provided, validate it first
    if key:
        from core import key_manager
        if not key_manager.check_key(settings.keys_file, key, machine_id):
            raise HTTPException(status_code=403, detail="Key is invalid, expired, or used on another machine")

    # Immediate file count check (v5)
    if len(files) > settings.limit_file:
         raise HTTPException(status_code=400, detail=f"Vượt quá giới hạn số lượng file ({len(files)}/{settings.limit_file})")

    resolved_settings = step0_session.execute(settings, cookie, email)
    
    if not resolved_settings.cookie:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Validate indoor_model_id
    if indoor_model_id not in [1, 3]:
        indoor_model_id = 3  # Force default if invalid
    
    job_id = str(uuid.uuid4())
    user_email = resolved_settings.email
    
    # Create temp directory for uploads
    temp_dir = os.path.join(settings.get_user_dir(user_email), "temp", job_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    file_paths = []
    for file in files:
        path = os.path.join(temp_dir, file.filename)
        # Use buffered reading to avoid OOM for large files and keep event loop alive
        try:
            with open(path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    buffer.write(chunk)
            file_paths.append(path)
        except Exception as e:
            log(logger, "ERROR", 0, f"Lỗi khi lưu file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Could not save file: {file.filename}")
    
    processing_jobs[job_id] = {
        "status": "pending",
        "logs": [],
        "address": address,
        "job_id": job_id
    }
    
    background_tasks.add_task(run_pipeline_task, job_id, file_paths, address, resolved_settings, cookie, email, indoor_model_id, key)
    
    return {"job_id": job_id}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get status and logs of a processing job (one-shot)."""
    job = processing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/stream/{job_id}")
async def stream_job(job_id: str, offset: int = 0):
    """SSE endpoint that streams log lines and status changes in real-time."""
    job = processing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_log_count = offset
        last_status = None
        heartbeat_interval = 15  # seconds
        last_heartbeat = asyncio.get_event_loop().time()

        while True:
            # Send heartbeat to keep connection alive (Railway/proxies)
            now = asyncio.get_event_loop().time()
            if now - last_heartbeat >= heartbeat_interval:
                yield ": keepalive\n\n"
                last_heartbeat = now
            current_job = processing_jobs.get(job_id)
            if not current_job:
                break

            # Stream new log lines
            logs = current_job.get("logs", [])
            if len(logs) > last_log_count:
                for line in logs[last_log_count:]:
                    yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"
                last_log_count = len(logs)

            # Stream status changes
            current_status = current_job.get("status")
            if current_status != last_status:
                last_status = current_status
                status_data = {"status": current_status}
                if current_status == "completed":
                    status_data["results"] = current_job.get("results", [])
                    status_data["unique_str"] = current_job.get("unique_str", "")
                elif current_status == "failed":
                    status_data["error"] = current_job.get("error", "")
                yield f"event: status\ndata: {json.dumps(status_data)}\n\n"

            # If terminal state, send final logs and close
            if current_status in ("completed", "failed"):
                # One final flush of any remaining logs
                logs = current_job.get("logs", [])
                if len(logs) > last_log_count:
                    for line in logs[last_log_count:]:
                        yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/jobs/active")
async def get_active_jobs():
    """Return list of active (pending/processing) job IDs."""
    active = []
    for job_id, job in processing_jobs.items():
        if job.get("status") in ("pending", "processing"):
            active.append({"job_id": job_id, "status": job["status"], "address": job.get("address", "")})
    return {"active_jobs": active}


@app.get("/health")
async def health_check():
    """Health check for deployment platforms."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

