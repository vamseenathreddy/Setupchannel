from __future__ import annotations

import pytest

from ytcore.exceptions import RetryExhaustedError
from ytcore.retry import retry_with_backoff


def test_succeeds_on_first_try() -> None:
    calls = []

    @retry_with_backoff(max_retries=3, backoff_seconds=0)
    def flaky() -> str:
        calls.append(1)
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 1


def test_succeeds_after_transient_failures() -> None:
    calls = []

    @retry_with_backoff(max_retries=3, backoff_seconds=0)
    def flaky() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("transient")
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 3


def test_raises_retry_exhausted_after_max_attempts() -> None:
    calls = []

    @retry_with_backoff(max_retries=2, backoff_seconds=0)
    def always_fails() -> None:
        calls.append(1)
        raise ValueError("permanent")

    with pytest.raises(RetryExhaustedError):
        always_fails()
    assert len(calls) == 3  # initial attempt + 2 retries


def test_only_retries_specified_exceptions() -> None:
    @retry_with_backoff(max_retries=3, backoff_seconds=0, exceptions=(ValueError,))
    def raises_type_error() -> None:
        raise TypeError("not retried")

    with pytest.raises(TypeError):
        raises_type_error()


def test_zero_retries_means_single_attempt() -> None:
    calls = []

    @retry_with_backoff(max_retries=0, backoff_seconds=0)
    def always_fails() -> None:
        calls.append(1)
        raise ValueError("fail")

    with pytest.raises(RetryExhaustedError):
        always_fails()
    assert len(calls) == 1
