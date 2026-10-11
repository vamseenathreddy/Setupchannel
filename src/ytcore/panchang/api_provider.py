"""
ApiPanchangProvider: fetches Panchang data from a configurable REST API.

This is written against a generic JSON contract rather than one specific
vendor, since Panchang API providers vary and you may switch between them.
Point MAHANAVI_PANCHANG_API_BASE_URL at your provider and, if its response
field names differ from the ones below, adjust `_FIELD_MAP` — no other
code needs to change.

Expected request:
    GET {base_url}?date=YYYY-MM-DD&lat={lat}&lon={lon}&key={api_key}

Expected response (JSON), field names configurable via _FIELD_MAP:
    {
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
        "karana": "Kaulava (up to 07:08 AM), Taitila (up to 07:03 PM), Garija",
        "yoga": "Sukla (up to 01:42 PM), Brahma",
        "amrit_kaal": "07:03 AM - 08:40 AM",
        "moonrise": "07:47 AM",
        "moonset": "07:42 PM",
        "festivals": ["Uttara Karte", "Varaha Jayanti"],
        "marriage_muhurats": "There is no muhurat on this day"
    }
The last seven fields (karana onward) are OPTIONAL — if your provider
doesn't return them, either omit them from _FIELD_MAP or leave the JSON
key absent; they default to empty/None rather than raising.
"""

from __future__ import annotations

import logging
from datetime import date, time
from typing import Any

import requests

from ytcore.core.interfaces import PanchangProvider
from ytcore.core.models import PanchangData
from ytcore.exceptions import PanchangFetchError, RetryExhaustedError
from ytcore.panchang.utils import parse_time_string
from ytcore.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Maps our PanchangData field names -> the JSON key returned by the API.
# Adjust this dict if your chosen provider uses different key names.
_FIELD_MAP: dict[str, str] = {
    "tithi": "tithi",
    "nakshatram": "nakshatram",
    "varjyam": "varjyam",
    "rahu_kalam": "rahu_kalam",
    "yamagandam": "yamagandam",
    "gulika_kalam": "gulika_kalam",
    "durmuhurtham": "durmuhurtham",
    "abhijit_muhurtham": "abhijit_muhurtham",
    "sunrise": "sunrise",
    "sunset": "sunset",
}

# Optional fields — looked up the same way as _FIELD_MAP, but a missing
# key (or a missing entry here) defaults instead of raising.
_OPTIONAL_FIELD_MAP: dict[str, str] = {
    "karana": "karana",
    "yoga": "yoga",
    "amrit_kaal": "amrit_kaal",
    "moonrise": "moonrise",
    "moonset": "moonset",
    "marriage_muhurats": "marriage_muhurats",
}
_OPTIONAL_FESTIVALS_KEY = "festivals"


class ApiPanchangProvider(PanchangProvider):
    """Fetches Panchang data from a configurable JSON REST API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        latitude: float,
        longitude: float,
        max_retries: int = 3,
        backoff_seconds: float = 5.0,
        timeout_seconds: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        if not base_url:
            raise PanchangFetchError(
                "ApiPanchangProvider requires MAHANAVI_PANCHANG_API_BASE_URL to be set."
            )
        self._base_url = base_url
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

        # Wrap the network call with retry behaviour configured per-instance,
        # so tests can use max_retries=0 for fast, deterministic failure paths.
        self._fetch_raw = retry_with_backoff(
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
            exceptions=(requests.RequestException,),
        )(self._fetch_raw_uncached)

    def fetch(self, for_date: date) -> PanchangData:
        try:
            payload = self._fetch_raw(for_date)
        except RetryExhaustedError as exc:
            raise PanchangFetchError(
                f"Panchang API request failed for {for_date} after retries."
            ) from exc

        try:
            return self._parse_payload(payload, for_date)
        except KeyError as exc:
            raise PanchangFetchError(
                f"Panchang API response missing expected field: {exc}. "
                "Check _FIELD_MAP in api_provider.py against the actual response shape."
            ) from exc

    def _fetch_raw_uncached(self, for_date: date) -> dict[str, Any]:
        params: dict[str, Any] = {
            "date": for_date.isoformat(),
            "lat": self._latitude,
            "lon": self._longitude,
        }
        if self._api_key:
            params["key"] = self._api_key

        response = self._session.get(self._base_url, params=params, timeout=self._timeout_seconds)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return payload

    @staticmethod
    def _parse_payload(payload: dict[str, Any], for_date: date) -> PanchangData:
        def get(field: str) -> str:
            return str(payload[_FIELD_MAP[field]])

        def get_optional(field: str) -> str:
            json_key = _OPTIONAL_FIELD_MAP.get(field)
            if json_key is None or json_key not in payload:
                return ""
            return str(payload[json_key])

        def get_optional_time(field: str) -> time | None:
            raw = get_optional(field)
            if not raw:
                return None
            try:
                return parse_time_string(raw)
            except ValueError:
                logger.warning("Could not parse optional field '%s' value %r as a time — leaving unset.", field, raw)
                return None

        festivals_raw = payload.get(_OPTIONAL_FESTIVALS_KEY, [])
        festivals = [str(item) for item in festivals_raw] if isinstance(festivals_raw, list) else []

        return PanchangData(
            date_=for_date,
            tithi=get("tithi"),
            nakshatram=get("nakshatram"),
            varjyam=get("varjyam"),
            rahu_kalam=get("rahu_kalam"),
            yamagandam=get("yamagandam"),
            gulika_kalam=get("gulika_kalam"),
            durmuhurtham=get("durmuhurtham"),
            abhijit_muhurtham=get("abhijit_muhurtham"),
            sunrise=parse_time_string(get("sunrise")),
            sunset=parse_time_string(get("sunset")),
            karana=get_optional("karana"),
            yoga=get_optional("yoga"),
            amrit_kaal=get_optional("amrit_kaal"),
            moonrise=get_optional_time("moonrise"),
            moonset=get_optional_time("moonset"),
            festivals=festivals,
            marriage_muhurats=get_optional("marriage_muhurats"),
            source="api",
        )
