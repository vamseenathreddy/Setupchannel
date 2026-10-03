from __future__ import annotations

from datetime import date

import pytest

from mahanavi.core.interfaces import PanchangProvider
from mahanavi.core.models import PanchangData
from mahanavi.exceptions import PanchangFetchError
from mahanavi.panchang.dummy_provider import DummyPanchangProvider
from mahanavi.panchang.fallback_provider import FallbackPanchangProvider


class _AlwaysFailsProvider(PanchangProvider):
    """Stands in for a Prokerala account whose monthly quota is exhausted."""

    def __init__(self, message: str = "quota exceeded") -> None:
        self.message = message
        self.calls = 0

    def fetch(self, for_date: date) -> PanchangData:
        self.calls += 1
        raise PanchangFetchError(self.message)


class _AlwaysSucceedsProvider(PanchangProvider):
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, for_date: date) -> PanchangData:
        self.calls += 1
        return DummyPanchangProvider().fetch(for_date)


def test_empty_provider_list_raises_value_error() -> None:
    with pytest.raises(ValueError):
        FallbackPanchangProvider([])


def test_first_provider_success_does_not_touch_second() -> None:
    first = _AlwaysSucceedsProvider()
    second = _AlwaysFailsProvider()
    provider = FallbackPanchangProvider([first, second])

    result = provider.fetch(date(2026, 9, 26))

    assert result.date_ == date(2026, 9, 26)
    assert first.calls == 1
    assert second.calls == 0


def test_falls_back_to_second_provider_when_first_fails() -> None:
    first = _AlwaysFailsProvider("primary account quota exceeded")
    second = _AlwaysSucceedsProvider()
    provider = FallbackPanchangProvider([first, second])

    result = provider.fetch(date(2026, 9, 26))

    assert result.date_ == date(2026, 9, 26)
    assert first.calls == 1
    assert second.calls == 1


def test_raises_with_all_errors_when_every_provider_fails() -> None:
    first = _AlwaysFailsProvider("primary account quota exceeded")
    second = _AlwaysFailsProvider("secondary account quota exceeded")
    provider = FallbackPanchangProvider([first, second])

    with pytest.raises(PanchangFetchError) as excinfo:
        provider.fetch(date(2026, 9, 26))

    assert "primary account quota exceeded" in str(excinfo.value)
    assert "secondary account quota exceeded" in str(excinfo.value)


def test_tries_three_providers_in_order() -> None:
    first = _AlwaysFailsProvider("one")
    second = _AlwaysFailsProvider("two")
    third = _AlwaysSucceedsProvider()
    provider = FallbackPanchangProvider([first, second, third])

    result = provider.fetch(date(2026, 9, 26))

    assert result.date_ == date(2026, 9, 26)
    assert first.calls == 1
    assert second.calls == 1
    assert third.calls == 1


def test_on_fallback_called_with_failed_index_and_succeeded_label() -> None:
    first = _AlwaysFailsProvider("primary account quota exceeded")
    second = _AlwaysSucceedsProvider()
    calls: list[tuple[int, str]] = []
    provider = FallbackPanchangProvider([first, second], on_fallback=lambda i, label: calls.append((i, label)))

    provider.fetch(date(2026, 9, 26))

    assert len(calls) == 1
    assert calls[0][0] == 1
    assert "_AlwaysSucceedsProvider" in calls[0][1]


def test_on_fallback_not_called_when_first_provider_succeeds() -> None:
    first = _AlwaysSucceedsProvider()
    second = _AlwaysFailsProvider()
    calls: list[tuple[int, str]] = []
    provider = FallbackPanchangProvider([first, second], on_fallback=lambda i, label: calls.append((i, label)))

    provider.fetch(date(2026, 9, 26))

    assert calls == []


def test_on_fallback_exception_does_not_break_the_fetch() -> None:
    first = _AlwaysFailsProvider()
    second = _AlwaysSucceedsProvider()

    def _broken_callback(i: int, label: str) -> None:
        raise RuntimeError("Telegram is down")

    provider = FallbackPanchangProvider([first, second], on_fallback=_broken_callback)

    result = provider.fetch(date(2026, 9, 26))

    assert result.date_ == date(2026, 9, 26)
