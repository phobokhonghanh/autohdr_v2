"""
AutoHDR v2 Backend - Pipeline Orchestrator.

Orchestrates the 8-step HDR image processing pipeline:
    Step 0: Resolve session/authentication (cookie management)
    Step 1: Generate presigned URLs for S3 upload
    Step 2: Upload files to S3
    Step 3: Finalize upload
    Step 4: Associate files with user and trigger processing
    Step 5: Poll for processing completion
    Step 6: Get processed photo URLs
    Step 7: Download processed photos

Usage:
    # First time: provide cookie
    python main.py --files photo1.jpg --address "123 Main St" --cookie "your_cookie"

    # Subsequent runs: provide email only
    python main.py --files photo1.jpg --address "123 Main St" --email "user@email.com"

All configuration is loaded from .env file.
"""

import argparse
import sys
import os
import logging

# Add project root to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from core.http_client import HttpClient
from core.logger import log
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
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace with:
        - files: List of file paths to upload
        - address: Address string for the photoshoot
        - cookie: Optional cookie string for first-time authentication
        - email: Optional email to lookup saved session
        - env: Optional path to .env file
    """
    parser = argparse.ArgumentParser(
        description="AutoHDR v2 - Automated HDR Image Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # First time (with cookie):
    python main.py --files photo1.jpg photo2.png --address "123 Main St" --cookie "your_cookie_string"

    # Subsequent runs (with email):
    python main.py --files photo1.jpg photo2.png --address "123 Main St" --email "user@email.com"

    # Using .env configuration:
    python main.py --files photo1.jpg --address "Test" --env .env.prod
        """,
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="List of image file paths to upload",
    )
    parser.add_argument(
        "--address",
        required=True,
        help="Address string for the photoshoot",
    )
    parser.add_argument(
        "--cookie",
        default=None,
        help="Cookie string for authentication (required for first time use)",
    )
    parser.add_argument(
        "--email",
        default=None,
        help="Email to lookup saved session (for subsequent runs)",
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Path to .env file (default: .env in current directory)",
    )
    return parser.parse_args()


def validate_files(file_paths: list) -> bool:
    """
    Validate that all input files exist.

    Args:
        file_paths: List of file paths to validate.

    Returns:
        True if all files exist, False otherwise.
    """
    all_valid = True
    for fp in file_paths:
        if not os.path.exists(fp):
            log(logger, "ERROR", 0, f"File not found: {fp}")
            all_valid = False
    return all_valid


def run_pipeline(
    file_paths: list,
    address: str,
    settings: Settings,
) -> bool:
    """
    Execute the full pipeline (Step 0 → Step 7).

    Each step depends on the previous step's output. The pipeline
    stops immediately if any step fails.

    Args:
        file_paths: List of image file paths to process.
        address: Address string for the photoshoot.
        settings: Application settings (already resolved by Step 0).

    Returns:
        True if all steps completed successfully, False otherwise.
    """
    # Validate that we have required auth info
    if not settings.cookie:
        log(
            logger,
            "ERROR",
            0,
            "Không có cookie. Vui lòng cung cấp cookie bằng --cookie",
        )
        return False

    if not settings.email or not settings.user_id:
        log(
            logger,
            "ERROR",
            0,
            "Thiếu thông tin user (email/user_id). "
            "Vui lòng cung cấp cookie bằng --cookie",
        )
        return False

    # Initialize HTTP client (with resolved cookie)
    client = HttpClient(settings)

    # Build pipeline context
    context = PipelineContext(
        file_paths=file_paths,
        address=address,
        email=settings.email,
        firstname=settings.firstname,
        lastname=settings.lastname,
        user_id=settings.user_id,
    )

    # === Step 1: Generate Presigned URLs ===
    log(logger, "INFO", 1, "=== Step 1: Generate Presigned URLs ===")
    context = step1_presigned_urls.execute(client, context, settings.output_dir)
    if context is None:
        log(logger, "ERROR", 1, "Pipeline stopped: Step 1 failed")
        return False

    # === Step 2: Upload Files to S3 ===
    log(logger, "INFO", 2, "=== Step 2: Upload Files to S3 ===")
    upload_success = step2_upload_files.execute(client, context)
    if not upload_success:
        log(logger, "ERROR", 2, "Pipeline stopped: Step 2 failed")
        return False

    # === Step 3: Finalize Upload ===
    log(logger, "INFO", 3, "=== Step 3: Finalize Upload ===")
    finalize_success = step3_finalize_upload.execute(client, context.unique_str)
    if not finalize_success:
        log(logger, "ERROR", 3, "Pipeline stopped: Step 3 failed")
        return False

    # === Step 4: Associate and Run ===
    log(logger, "INFO", 4, "=== Step 4: Associate and Run Processing ===")
    process_success = step4_associate_and_run.execute(
        client=client,
        unique_str=context.unique_str,
        email=context.email,
        firstname=context.firstname,
        lastname=context.lastname,
        address=context.address,
        files_count=len(context.filenames),
    )
    if not process_success:
        log(logger, "ERROR", 4, "Pipeline stopped: Step 4 failed")
        return False

    # === Step 5: Poll Status ===
    log(logger, "INFO", 5, "=== Step 5: Poll Photoshoot Status ===")
    photoshoot_id = step5_poll_status.execute(
        client=client,
        settings=settings,
        unique_str=context.unique_str,
        address=context.address,
    )
    if photoshoot_id is None:
        log(logger, "ERROR", 5, "Pipeline stopped: Step 5 failed")
        return False
    context.photoshoot_id = photoshoot_id

    # === Step 6: Get Processed URLs ===
    log(logger, "INFO", 6, "=== Step 6: Get Processed Photo URLs ===")
    context.processed_urls = step6_get_processed_urls.execute(
        client=client,
        photoshoot_id=context.photoshoot_id,
        unique_str=context.unique_str,
        input_filenames=context.filenames,
        page_size=settings.photoshoot_page_size,
    )

    # === Step 7: Download Photos ===
    log(logger, "INFO", 7, "=== Step 7: Download Processed Photos ===")
    download_success = step7_download_photos.execute(
        client=client,
        settings=settings,
        cleaned_urls=context.processed_urls,
        unique_str=context.unique_str,
        address=context.address,
        email=context.email,
    )
    if not download_success:
        log(logger, "ERROR", 7, "Pipeline stopped: Step 7 failed")
        return False

    log(logger, "INFO", 0, "=== Pipeline completed successfully ===")
    return True


def main():
    """
    Main entry point for the AutoHDR pipeline.

    Parses arguments, loads settings, resolves authentication via Step 0,
    validates input files, and runs the pipeline.
    """
    args = parse_args()

    # Load settings from .env
    settings = Settings.from_env(env_path=args.env)

    # === Step 0: Resolve Session ===
    log(logger, "INFO", 0, "=== Step 0: Resolve Session ===")
    settings = step0_session.execute(
        settings=settings,
        cookie=args.cookie,
        email=args.email,
    )

    # Validate files
    if not validate_files(args.files):
        sys.exit(1)

    # Run pipeline
    success = run_pipeline(args.files, args.address, settings)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
