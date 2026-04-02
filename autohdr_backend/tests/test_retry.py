"""Tests for the retry module."""

import pytest

from core.retry import retry_with_backoff
from core.logger import get_logger


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    def test_success_on_first_try(self):
        """Should return result immediately on success."""
        def success_func():
            return "ok"

        logger = get_logger("test_retry")
        result = retry_with_backoff(
            success_func, logger, step=1, max_retries=3,
            initial_delay=0.01, backoff_factor=1.5,
        )
        assert result == "ok"

    def test_success_after_retries(self):
        """Should succeed after a few failed attempts."""
        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "recovered"

        logger = get_logger("test_retry2")
        result = retry_with_backoff(
            fail_then_succeed, logger, step=2, max_retries=5,
            initial_delay=0.01, backoff_factor=1.5,
        )
        assert result == "recovered"
        assert call_count == 3

    def test_all_retries_exhausted(self):
        """Should return None when all retries fail."""
        def always_fail():
            raise Exception("Permanent failure")

        logger = get_logger("test_retry3")
        result = retry_with_backoff(
            always_fail, logger, step=3, max_retries=3,
            initial_delay=0.01, backoff_factor=1.5,
        )
        assert result is None

    def test_custom_retry_message(self):
        """Should use custom retry message in logs."""
        call_count = 0

        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("fail")
            return "ok"

        logger = get_logger("test_retry4")
        result = retry_with_backoff(
            fail_once, logger, step=5, max_retries=3,
            initial_delay=0.01, backoff_factor=1.5,
            on_retry_message="Server đang xử lý",
        )
        assert result == "ok"
