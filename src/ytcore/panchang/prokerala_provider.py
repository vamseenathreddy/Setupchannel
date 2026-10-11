"""
ProkeralaPanchangProvider: fetches REAL Panchang data from Prokerala's
official Astrology API (https://api.prokerala.com/) — the "unlimited
days, real data" alternative to DummyPanchangProvider.

Uses Prokerala's own official Python client (`pip install prokerala-api`)
for OAuth2 client-credentials auth and token caching — we don't hand-roll
that ourselves. Get a free client ID/secret at https://api.prokerala.com/
(forever-free tier: 5,000 credits/month, 5 requests/minute — comfortably
covers one request per day).

*** CONFIRMED AGAINST A REAL LIVE RESPONSE (2026-09-14) ***
Endpoint: v2/astrology/panchang/advanced (the plain v2/astrology/panchang
endpoint also works, but doesn't include the auspicious/inauspicious
muhurtam breakdown at all — confirmed via a real call).

Real response shape, wrapped in {"status": "ok", "data": {...}}:
  - tithi, nakshatra, karana, yoga: each a LIST of {"name": <Telugu>,
    "start": <ISO8601>, "end": <ISO8601>, ...} — a day can span two
    entries when one transitions partway through (both are included).
  - sunrise, sunset, moonrise, moonset: top-level ISO8601 strings.
  - auspicious_period / inauspicious_period: each a LIST (NOT a dict
    keyed by English field names, as originally guessed before seeing a
    real response) of {"id", "name": <Telugu>, "type", "period": [{start,
    end}, ...]} — "period" can have MULTIPLE entries (Durmuhurtham
    genuinely has two separate windows most days). Matched here by
    Telugu name substring rather than "id", since id stability isn't
    documented anywhere and the Telugu name is right there anyway (and
    is exactly the label text we want to show).

*** COST FIX (2026-09-15): switched default language from Telugu to
English. Confirmed via Prokerala's own credit-usage dashboard (400
credits burned after only 4 test calls) and their public pricing table:
Panchang Advanced costs 100 credits in English vs 200 in "other
languages" (Telugu included) — a straight 2x cost for the same request.
At Telugu pricing, one call per day alone would cost ~6,000 credits/
month, already over the 5,000/month free tier before adding anything
else. Requesting English and translating tithi/nakshatram/karana/yoga
ourselves (see images/telugu_text.py) halves the daily cost to ~3,000/
month with no loss of Telugu output quality.

*** UNVERIFIED: the auspicious/inauspicious period "name" matching
below (_AUSPICIOUS_MATCH / _INAUSPICIOUS_MATCH) was confirmed against a
REAL Telugu-language response, but NOT yet against a real English
response — the English wording used below is a reasonable guess (e.g.
"Abhijit Muhurat", "Rahu Kaal"), not confirmed. Run
scripts/prokerala_smoke_test.py once more and check the English
response's auspicious_period/inauspicious_period "name" fields match
what's expected here before trusting this for a real post.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from ytcore.core.interfaces import PanchangProvider
from ytcore.core.models import PanchangData
from ytcore.exceptions import PanchangFetchError
from ytcore.images.telugu_text import (
    translate_karana,
    translate_nakshatram,
    translate_tithi,
    translate_yoga,
)

logger = logging.getLogger(__name__)

# Prokerala's API requires an explicit timezone offset in the datetime
# param (confirmed via a real 400 error: "Value should be a string in
# ISO 8601 ... Example: 2004-02-12T15:19:21+05:30" — a naive datetime's
# .isoformat() omits the offset entirely, which it rejects outright).
_IST = timezone(timedelta(hours=5, minutes=30))

# Substrings matched against the "name" field of each auspicious/
# inauspicious period entry. English wording is a reasonable guess (see
# module docstring's UNVERIFIED note) — not yet confirmed against a real
# English-language response the way the Telugu versions were.
_AUSPICIOUS_MATCH = {
    "abhijit_muhurtham": "Abhijit",
    "amrit_kaal": "Amrit",
}
_INAUSPICIOUS_MATCH = {
    "rahu_kalam": "Rahu",
    "yamagandam": "Yamagand",
    "gulika_kalam": "Gulik",
    "durmuhurtham": "Dur Muhurat",
    "varjyam": "Varjyam",
}


class ProkeralaPanchangProvider(PanchangProvider):
    """Fetches real Panchang data from Prokerala's official Astrology API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        latitude: float,
        longitude: float,
        ayanamsa: int = 1,  # Lahiri — the standard ayanamsa for Indian Panchang
        language: str = "en",  # English — half the credit cost of Telugu; we translate ourselves (see telugu_text.py)
        token_cache_path: Path | None = None,
    ) -> None:
        if not client_id or not client_secret:
            raise PanchangFetchError(
                "ProkeralaPanchangProvider requires MAHANAVI_PROKERALA_CLIENT_ID "
                "and MAHANAVI_PROKERALA_CLIENT_SECRET to be set."
            )
        try:
            from prokerala_api import ApiClient
        except ImportError as exc:
            raise PanchangFetchError(
                "The 'prokerala-api' package is required for ProkeralaPanchangProvider. "
                "Install it with: pip install prokerala-api"
            ) from exc

        self._client = ApiClient(client_id, client_secret)
        if token_cache_path is not None:
            token_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._client.TOKEN_FILE = str(token_cache_path)
        self._latitude = latitude
        self._longitude = longitude
        self._ayanamsa = ayanamsa
        self._language = language

    def fetch(self, for_date: date) -> PanchangData:
        # Midday avoids ambiguity around how the API might interpret
        # "which day" a datetime near midnight belongs to.
        dt = datetime.combine(for_date, time(12, 0), tzinfo=_IST)
        params = {
            "ayanamsa": self._ayanamsa,
            "coordinates": f"{self._latitude},{self._longitude}",
            "datetime": dt.isoformat(),
            "la": self._language,
        }
        try:
            payload = self._client.get("v2/astrology/panchang/advanced", params)
        except Exception as exc:  # the client library's own ApiError/subclasses
            raise PanchangFetchError(f"Prokerala API request failed for {for_date}: {exc}") from exc

        try:
            return self._parse_payload(payload, for_date)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise PanchangFetchError(
                f"Unexpected Prokerala API response shape: {exc}. "
                "Run scripts/prokerala_smoke_test.py and compare the raw JSON "
                "against the parsing in ProkeralaPanchangProvider._parse_payload — "
                "the response schema may differ from what's expected here."
            ) from exc

    def _parse_payload(self, payload: dict[str, Any], for_date: date) -> PanchangData:
        # Confirmed via a real response: content is nested under "data".
        data = payload.get("data", payload) if isinstance(payload, dict) else payload

        def all_names(key: str, translate: Callable[[str], str]) -> str:
            entries = data.get(key) or []
            names = [
                translate(str(e.get("name", "")))
                for e in entries if isinstance(e, dict) and e.get("name")
            ]
            return ", ".join(names)

        def find_period(entries: list[Any], name_substring: str) -> str:
            # Accumulate across ALL matching entries, not just the first —
            # a field like Varjyam can appear as multiple separate list
            # entries (e.g. one spanning into the previous day, one for
            # today), not always as a single entry with multiple periods.
            ranges = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if name_substring in str(entry.get("name", "")):
                    for p in entry.get("period") or []:
                        start = _format_period_time(p.get("start", ""))
                        end = _format_period_time(p.get("end", ""))
                        if start and end:
                            ranges.append(f"{start} - {end}")
            return ", ".join(ranges)

        auspicious = data.get("auspicious_period") or []
        inauspicious = data.get("inauspicious_period") or []

        return PanchangData(
            date_=for_date,
            tithi=all_names("tithi", translate_tithi),
            nakshatram=all_names("nakshatra", translate_nakshatram),
            varjyam=find_period(inauspicious, _INAUSPICIOUS_MATCH["varjyam"]),
            rahu_kalam=find_period(inauspicious, _INAUSPICIOUS_MATCH["rahu_kalam"]),
            yamagandam=find_period(inauspicious, _INAUSPICIOUS_MATCH["yamagandam"]),
            gulika_kalam=find_period(inauspicious, _INAUSPICIOUS_MATCH["gulika_kalam"]),
            durmuhurtham=find_period(inauspicious, _INAUSPICIOUS_MATCH["durmuhurtham"]),
            abhijit_muhurtham=find_period(auspicious, _AUSPICIOUS_MATCH["abhijit_muhurtham"]),
            sunrise=_parse_iso_time(str(data.get("sunrise", ""))),
            sunset=_parse_iso_time(str(data.get("sunset", ""))),
            karana=all_names("karana", translate_karana),
            yoga=all_names("yoga", translate_yoga),
            amrit_kaal=find_period(auspicious, _AUSPICIOUS_MATCH["amrit_kaal"]),
            moonrise=_parse_iso_time_optional(data.get("moonrise")),
            moonset=_parse_iso_time_optional(data.get("moonset")),
            festivals=[],  # not part of this endpoint's response
            marriage_muhurats="",  # not part of this endpoint's response
            source="prokerala",
        )


def _parse_iso_time(raw: str) -> time:
    if not raw:
        raise ValueError("Prokerala response had an empty sunrise/sunset value.")
    return datetime.fromisoformat(raw).time()


def _parse_iso_time_optional(raw: object) -> time | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw)).time()
    except ValueError:
        logger.warning("Could not parse Prokerala moonrise/moonset value %r — leaving unset.", raw)
        return None


def _format_period_time(raw: str) -> str:
    """Format an auspicious/inauspicious period boundary as 'HH:MM AM/PM'.
    Falls back to the raw string unchanged if it's not a parseable ISO
    datetime — safer than raising, since this is decorative text."""
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw).strftime("%I:%M %p")
    except ValueError:
        return raw
