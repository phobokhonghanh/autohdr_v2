import pytest
from fastapi.testclient import TestClient
from app import app
from core import key_manager
from config.settings import Settings
from datetime import datetime, timedelta

client = TestClient(app)

def test_api_key_active_valid(tmp_path):
    # Setup dummy keys file
    settings = Settings.from_env()
    
    # We'll just patch the check directly or use the mock
    # A cleaner way is using unittest.mock.patch
    from unittest.mock import patch
    with patch("core.key_manager.check_key", return_value=True):
        response = client.post("/api/key/active", json={"key": "mocked_valid_key"})
        assert response.status_code == 200
        assert response.json()["valid"] is True

def test_api_key_active_invalid():
    from unittest.mock import patch
    with patch("core.key_manager.check_key", return_value=False):
        response = client.post("/api/key/active", json={"key": "mocked_invalid_key"})
        assert response.status_code == 403
