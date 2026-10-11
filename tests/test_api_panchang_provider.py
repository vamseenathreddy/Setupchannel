from __future__ import annotations

from datetime import date, time

import pytest
import requests_mock

from ytcore.exceptions import PanchangFetchError
from ytcore.panchang.api_provider import ApiPanchangProvider

BASE_URL = "https://fake-panchang-api.test/v1/panchang"

VALID_PAYLOAD = {
    "tithi": "Panchami",
    "nakshatram": "Rohini",
    "varjyam": "10:12 AM - 11:42 AM",
    "rahu_kalam": "07:30 AM - 09:00 AM",
    "yamagandam": "10:30 AM - 12:00 PM",
    "gulika_kalam": "01:30 PM - 03:00 PM",
    "durmuhurtham": "08:06 AM - 08:52 AM",
    "abhijit_muhurtham": "11:48 AM - 12:38 PM",
    "sunrise": "05:58 AM",
    "sunset": "06:45 PM",
}


def _provider(max_retries: int = 0) -> ApiPanchangProvider:
    return ApiPanchangProvider(
        base_url=BASE_URL,
        api_key="test-key",
        latitude=17.385,
        longitude=78.4867,
        max_retries=max_retries,
        backoff_seconds=0,
    )


def test_fetch_success() -> None:
    with requests_mock.Mocker() as m:
        m.get(BASE_URL, json=VALID_PAYLOAD)
        provider = _provider()
        result = provider.fetch(date(2026, 7, 20))

    assert result.tithi == "Panchami"
    assert result.nakshatram == "Rohini"
    assert result.sunrise == time(5, 58)
    assert result.sunset == time(18, 45)
    assert result.source == "api"


def test_fetch_sends_expected_params() -> None:
    with requests_mock.Mocker() as m:
        m.get(BASE_URL, json=VALID_PAYLOAD)
        provider = _provider()
        provider.fetch(date(2026, 7, 20))

    request = m.request_history[0]
    assert request.qs["date"] == ["2026-07-20"]
    assert request.qs["key"] == ["test-key"]


def test_missing_field_raises_panchang_fetch_error() -> None:
    incomplete = dict(VALID_PAYLOAD)
    del incomplete["nakshatram"]
    with requests_mock.Mocker() as m:
        m.get(BASE_URL, json=incomplete)
        provider = _provider()
        with pytest.raises(PanchangFetchError):
            provider.fetch(date(2026, 7, 20))


def test_http_error_raises_panchang_fetch_error_after_retries() -> None:
    with requests_mock.Mocker() as m:
        m.get(BASE_URL, status_code=500)
        provider = _provider(max_retries=1)
        with pytest.raises(PanchangFetchError):
            provider.fetch(date(2026, 7, 20))
    # initial attempt + 1 retry = 2 calls
    assert m.call_count == 2


def test_missing_base_url_raises_immediately() -> None:
    with pytest.raises(PanchangFetchError):
        ApiPanchangProvider(
            base_url="",
            api_key=None,
            latitude=0.0,
            longitude=0.0,
        )
