"""
Shared test fixtures for AutoHDR backend tests.

Provides common fixtures like settings, HTTP client, and pipeline context
used across all test files.
"""

import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from core.http_client import HttpClient
from models.schemas import PipelineContext, PresignedUrl


@pytest.fixture
def settings():
    """Create a test Settings instance with default test values."""
    return Settings(
        base_url="https://www.autohdr.com",
        cookie="test_cookie=value",
        user_agent="TestAgent/1.0",
        output_dir="/tmp/autohdr_test_output",
        quota_file="/tmp/autohdr_test_quota.json",
        user_id="12345",
        email="test@example.com",
        firstname="Test",
        lastname="User",
        address="Test Address",
        limit_count=100,
        limit_file=10,
        retry_max_attempts=3,
        retry_initial_delay=0.01,
        retry_backoff_factor=1.5,
        photoshoot_limit=20,
        photoshoot_page_size=10,
    )


@pytest.fixture
def http_client(settings):
    """Create a test HttpClient instance."""
    return HttpClient(settings)


@pytest.fixture
def sample_context():
    """Create a sample PipelineContext for testing."""
    return PipelineContext(
        file_paths=["/tmp/test_photo1.jpg", "/tmp/test_photo2.png"],
        address="Test Address 123",
        email="test@example.com",
        firstname="Test",
        lastname="User",
        user_id="12345",
        unique_str="83b93a60-aef6-409a-9f0d-7c1683c06e3f",
        filenames=["test_photo1.jpg", "test_photo2.png"],
        presigned_urls=[
            PresignedUrl(
                filename="test_photo1.jpg",
                url="https://s3.amazonaws.com/bucket/test_photo1.jpg?sig=xxx",
            ),
            PresignedUrl(
                filename="test_photo2.png",
                url="https://s3.amazonaws.com/bucket/test_photo2.png?sig=xxx",
            ),
        ],
    )


@pytest.fixture
def sample_presigned_response():
    """Sample API response for step1 presigned URLs."""
    return {
        "presignedUrls": [
            {
                "filename": "test_photo1.jpg",
                "url": "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/raw/test_photo1.jpg?AWSAccessKeyId=AKIA&Signature=xxx",
            },
            {
                "filename": "test_photo2.png",
                "url": "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/raw/test_photo2.png?AWSAccessKeyId=AKIA&Signature=yyy",
            },
        ]
    }


@pytest.fixture
def sample_photoshoots_response():
    """Sample API response for step5 photoshoots."""
    return {
        "total_count": 2,
        "photoshoots": [
            {
                "id": 907761,
                "user_id": 12345,
                "name": "83b93a60-aef6-409a-9f0d-7c1683c06e3f",
                "creation_date_utc": "2026-04-01T04:09:06",
                "address": "Test Address 123",
                "status": "success",
                "location": "post_processing",
            },
            {
                "id": 907345,
                "user_id": 12345,
                "name": "other-uuid",
                "creation_date_utc": "2026-04-01T03:15:02",
                "address": "Other Address",
                "status": "success",
                "location": "post_processing",
            },
        ],
    }


@pytest.fixture
def sample_processed_photos_response():
    """Sample API response for step6 processed photos."""
    return [
        {
            "url": "https://image-upload-autohdr-j.s3.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/processed/test_photo1.jpg?response-content-disposition=inline&AWSAccessKeyId=AKIA&Signature=xxx",
            "id": 23985654,
            "human_edit_requested": False,
            "downloaded": False,
            "order_index": 0,
        },
        {
            "url": "https://image-upload-autohdr-j.s3.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/processed/test_photo2.png?response-content-disposition=inline&AWSAccessKeyId=AKIA&Signature=yyy",
            "id": 23985655,
            "human_edit_requested": False,
            "downloaded": False,
            "order_index": 1,
        },
    ]
