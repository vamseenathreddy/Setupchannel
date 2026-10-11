from __future__ import annotations

from datetime import date, time

import pytest
import requests_mock

from ytcore.exceptions import PanchangFetchError
from ytcore.panchang.scraper_provider import ScraperPanchangProvider

URL_TEMPLATE = "https://fake-panchang-site.test/panchang/{date}"

SELECTORS = {
    "tithi": "#tithi",
    "nakshatram": "#nakshatram",
    "varjyam": "#varjyam",
    "rahu_kalam": "#rahu-kalam",
    "yamagandam": "#yamagandam",
    "gulika_kalam": "#gulika-kalam",
    "durmuhurtham": "#durmuhurtham",
    "abhijit_muhurtham": "#abhijit-muhurtham",
    "sunrise": "#sunrise",
    "sunset": "#sunset",
}

FIXTURE_HTML = """
<html><body>
    <div id="tithi">Panchami</div>
    <div id="nakshatram">Rohini</div>
    <div id="varjyam">10:12 AM - 11:42 AM</div>
    <div id="rahu-kalam">07:30 AM - 09:00 AM</div>
    <div id="yamagandam">10:30 AM - 12:00 PM</div>
    <div id="gulika-kalam">01:30 PM - 03:00 PM</div>
    <div id="durmuhurtham">08:06 AM - 08:52 AM</div>
    <div id="abhijit-muhurtham">11:48 AM - 12:38 PM</div>
    <div id="sunrise">05:58 AM</div>
    <div id="sunset">06:45 PM</div>
</body></html>
"""


def _provider(max_retries: int = 0) -> ScraperPanchangProvider:
    return ScraperPanchangProvider(
        url_template=URL_TEMPLATE,
        selectors=SELECTORS,
        max_retries=max_retries,
        backoff_seconds=0,
    )


def test_fetch_success() -> None:
    url = URL_TEMPLATE.format(date="2026-07-20")
    with requests_mock.Mocker() as m:
        m.get(url, text=FIXTURE_HTML)
        result = _provider().fetch(date(2026, 7, 20))

    assert result.tithi == "Panchami"
    assert result.nakshatram == "Rohini"
    assert result.sunrise == time(5, 58)
    assert result.sunset == time(18, 45)
    assert result.source == "scraper"


def test_missing_selector_raises() -> None:
    with pytest.raises(PanchangFetchError):
        ScraperPanchangProvider(
            url_template=URL_TEMPLATE,
            selectors={"tithi": "#tithi"},  # missing all other required fields
        )


def test_selector_matching_nothing_raises() -> None:
    broken_html = "<html><body><div id='tithi'>Panchami</div></body></html>"
    url = URL_TEMPLATE.format(date="2026-07-20")
    with requests_mock.Mocker() as m:
        m.get(url, text=broken_html)
        with pytest.raises(PanchangFetchError):
            _provider().fetch(date(2026, 7, 20))


def test_http_error_raises_after_retries() -> None:
    url = URL_TEMPLATE.format(date="2026-07-20")
    with requests_mock.Mocker() as m:
        m.get(url, status_code=404)
        with pytest.raises(PanchangFetchError):
            _provider(max_retries=1).fetch(date(2026, 7, 20))
    assert m.call_count == 2
