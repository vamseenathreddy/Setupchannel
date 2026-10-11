from __future__ import annotations

from datetime import date

from ytcore.panchang.dummy_provider import DummyPanchangProvider


def test_returns_panchang_data_for_any_date() -> None:
    provider = DummyPanchangProvider()
    result = provider.fetch(date(2026, 7, 20))
    assert result.date_ == date(2026, 7, 20)
    assert result.source == "dummy"
    assert result.tithi
    assert result.nakshatram


def test_deterministic_for_same_date() -> None:
    provider = DummyPanchangProvider()
    r1 = provider.fetch(date(2026, 7, 20))
    r2 = provider.fetch(date(2026, 7, 20))
    assert r1 == r2


def test_varies_by_date() -> None:
    provider = DummyPanchangProvider()
    r1 = provider.fetch(date(2026, 7, 20))
    r2 = provider.fetch(date(2026, 7, 21))
    # At least one of tithi/nakshatram should differ across consecutive days.
    assert (r1.tithi, r1.nakshatram) != (r2.tithi, r2.nakshatram)


def test_rahu_kalam_varies_by_weekday() -> None:
    provider = DummyPanchangProvider()
    monday = provider.fetch(date(2026, 7, 6))     # Monday
    tuesday = provider.fetch(date(2026, 7, 7))     # Tuesday
    assert monday.rahu_kalam != tuesday.rahu_kalam
