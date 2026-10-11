"""
One-off script: calls the real Prokerala API once for today's date and
prints the raw JSON response, so you can verify (or correct)
ProkeralaPanchangProvider's parsing against real data.

NOT part of the daily pipeline — run this by hand once after setting
MAHANAVI_PROKERALA_CLIENT_ID / MAHANAVI_PROKERALA_CLIENT_SECRET in your
.env, to confirm the response shape before relying on the real provider.

Usage:
    python -m ytcore.scripts.prokerala_smoke_test
    python -m ytcore.scripts.prokerala_smoke_test --date 2026-09-13

The printed JSON contains no sensitive information (just Panchang data
for a date/location) — safe to paste into chat if you want help
adjusting the field parsing in prokerala_provider.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta, timezone

from ytcore.config import get_settings

_IST = timezone(timedelta(hours=5, minutes=30))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    for_date = date.fromisoformat(args.date) if args.date else date.today()

    settings = get_settings()
    if not settings.prokerala_client_id or not settings.prokerala_client_secret:
        print(
            "MAHANAVI_PROKERALA_CLIENT_ID / MAHANAVI_PROKERALA_CLIENT_SECRET "
            "are not set in your .env. Add them, then re-run this script.",
            file=sys.stderr,
        )
        return 1

    try:
        from prokerala_api import ApiClient
    except ImportError:
        print("Run: pip install prokerala-api", file=sys.stderr)
        return 1

    client = ApiClient(settings.prokerala_client_id, settings.prokerala_client_secret)
    dt = datetime.combine(for_date, time(12, 0), tzinfo=_IST)
    params = {
        "ayanamsa": 1,
        "coordinates": f"{settings.panchang_latitude},{settings.panchang_longitude}",
        "datetime": dt.isoformat(),
        "la": "te",
    }

    print(f"Requesting Panchang for {for_date.isoformat()} at "
          f"{settings.panchang_latitude},{settings.panchang_longitude} ...")

    # Try both the basic and /advanced endpoint variants — Prokerala's own
    # SDK examples show this "/advanced" suffix pattern elsewhere (e.g.
    # v2/astrology/kundli/advanced), and the basic panchang endpoint's
    # response (confirmed via a real call) has no auspicious/inauspicious
    # muhurtam breakdown at all, which we need.
    for endpoint in ("v2/astrology/panchang", "v2/astrology/panchang/advanced"):
        print(f"\n--- {endpoint} ---")
        try:
            payload = client.get(endpoint, params)
        except Exception as exc:  # the client library's own ApiError/subclasses
            print(f"Request failed: {exc}", file=sys.stderr)
            continue
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
