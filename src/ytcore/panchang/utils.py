"""Shared parsing helpers for Panchang providers."""

from __future__ import annotations

from datetime import datetime, time

from ytcore.exceptions import PanchangFetchError

# Common time formats seen across panchang APIs/sites.
_KNOWN_TIME_FORMATS = ("%I:%M %p", "%I:%M%p", "%H:%M")


def parse_time_string(value: str) -> time:
    """Parse a time string like '05:58 AM' or '18:45' into a datetime.time.

    Raises PanchangFetchError if none of the known formats match, since an
    unparsable time means the upstream source's format changed and needs
    attention rather than silently producing wrong data.
    """
    cleaned = value.strip()
    for fmt in _KNOWN_TIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).time()
        except ValueError:
            continue
    raise PanchangFetchError(
        f"Could not parse time string '{value}'. "
        f"Expected one of formats: {_KNOWN_TIME_FORMATS}"
    )
