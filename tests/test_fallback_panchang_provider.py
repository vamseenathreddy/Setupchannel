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
