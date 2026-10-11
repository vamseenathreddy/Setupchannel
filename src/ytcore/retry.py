"""
Generic retry-with-exponential-backoff decorator.

Used by any module that talks to an external system that can transiently
fail: Panchang API/scraper, YouTube/Telegram/Facebook/Instagram uploaders.
Centralizing this in one place means retry behaviour (attempt count,
backoff curve, logging) is consistent everywhere and configured once via
Settings.max_retries / Settings.retry_backoff_seconds.
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from ytcore.exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def retry_with_backoff(
    max_retries: int,
    backoff_seconds: float,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Retry a function on the given exception types, with exponential backoff.

    attempt 1 fails -> wait backoff_seconds
    attempt 2 fails -> wait backoff_seconds * 2
    attempt 3 fails -> wait backoff_seconds * 4
    ...
    After max_retries retries (i.e. max_retries + 1 total attempts), raises
    RetryExhaustedError wrapping the last exception.

    max_retries=0 means "try once, no retries" — useful in tests.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= max_retries:
                        logger.error(
                            "'%s' failed after %d attempt(s): %s",
                            func.__qualname__,
                            attempt + 1,
                            exc,
                        )
                        raise RetryExhaustedError(
                            f"{func.__qualname__} failed after {attempt + 1} attempt(s)",
                            last_error=exc,
                        ) from exc

                    sleep_time = backoff_seconds * (2 ** attempt)
                    logger.warning(
                        "'%s' failed (attempt %d/%d): %s — retrying in %.1fs",
                        func.__qualname__,
                        attempt + 1,
                        max_retries + 1,
                        exc,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    attempt += 1

        return wrapper

    return decorator
