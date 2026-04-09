"""
Retry module with exponential backoff.

Provides a reusable retry mechanism used by pipeline steps.
The backoff follows the spec:
    - Initial delay: 15 seconds
    - After each retry: delay *= 3/2 (1.5x)
    - Maximum retries: 5 (default)
"""

import time
import logging
from typing import Callable, TypeVar, Optional, Any

from core.logger import log

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[..., T],
    logger: logging.Logger,
    step: int,
    max_retries: int = 10,
    initial_delay: float = 15.0,
    backoff_factor: float = 1.5,
    on_retry_message: Optional[str] = None,
    retry_if_falsy: bool = False,
    check_stop_func: Optional[Callable[[], bool]] = None,
    *args: Any,
    **kwargs: Any,
) -> Optional[T]:
    """
    Execute a function with retry logic and exponential backoff.

    The delay between retries increases by a factor of `backoff_factor`
    after each attempt. Logs retry count and approximate wait time in minutes.

    Args:
        func: The callable to execute. Should return a value or raise an exception.
        logger: Logger instance for logging retry information.
        step: Step number for log formatting.
        max_retries: Maximum number of retry attempts (default: 5).
        initial_delay: Initial delay in seconds before first retry (default: 15.0).
        backoff_factor: Multiplier for delay after each retry (default: 1.5).
        on_retry_message: Optional custom message prefix for retry logs.
        retry_if_falsy: If True, treat False or None as failure and trigger retry.
        check_stop_func: Optional callable that returns True if the process should stop.
        *args: Positional arguments passed to func.
        **kwargs: Keyword arguments passed to func.

    Returns:
        The return value of func if successful, or None if all retries exhausted.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        # Check for stop signal before attempt
        if check_stop_func and check_stop_func():
            log(logger, "ERROR", step, "Tiến trình bị dừng bởi người dùng (Stop signal received)")
            raise InterruptedError("Pipeline stopped by user")

        try:
            result = func(*args, **kwargs)
            
            # Additional check for logical success if requested
            if retry_if_falsy and not result:
                raise ValueError(f"Falsy result: {result}")
                
            return result
        except InterruptedError:
            # Re-raise interruption immediately
            raise
        except Exception as e:
            last_exception = e
            minutes_approx = delay / 60
            retry_msg = on_retry_message or "Đang retry"
            log(
                logger,
                "INFO",
                step,
                f"{retry_msg} - Lần thử {attempt}/{max_retries}, "
                f"đợi {delay:.0f}s (~{minutes_approx:.1f} phút) | Lỗi: {e}",
            )
            
            if attempt < max_retries:
                # Check for stop signal during sleep (more responsive)
                sleep_start = time.time()
                while time.time() - sleep_start < delay:
                    if check_stop_func and check_stop_func():
                        log(logger, "ERROR", step, "Tiến trình bị dừng trong khi đang đợi retry")
                        raise InterruptedError("Pipeline stopped by user")
                    time.sleep(1) # Check every 1 second
                
                delay *= backoff_factor

    log(
        logger,
        "ERROR",
        step,
        f"Đã retry {max_retries} lần nhưng vẫn thất bại. "
        f"Lỗi cuối: {last_exception}",
    )
    return None

