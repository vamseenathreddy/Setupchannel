"""
check_festival_today.py: tells you whether today is worth a special
Community Post or festival-themed Short -- combining two sources:

1. A HARDCODED list of major festival dates for this specific year
   (FESTIVALS_2026 below). These shift every year with the lunar
   calendar, so this list needs a fresh look around each January --
   it will silently go stale otherwise, since nothing here re-derives
   these dates automatically.

2. AUTOMATIC detection of recurring tithi-based observances (Amavasya,
   Purnima, Ekadashi, Pradosham) from the SAME real Panchang data the
   daily Shorts pipeline already fetches. These need no yearly
   updating at all -- they're computed fresh every time this runs,
   for as long as the Panchang provider keeps working.

Usage:
    python -m ytcore.scripts.check_festival_today
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ytcore.config import get_settings
from ytcore.exceptions import AppError
from ytcore.panchang.factory import get_panchang_provider

# Verified against real 2026 sources (Dussehra/Diwali/Karthika Masam
# dates cross-checked across multiple calendar sites in Sept 2026).
# RE-VERIFY AND REPLACE THIS DICT EVERY YEAR -- these dates do not
# carry over to 2027.
FESTIVALS_2026: dict[date, str] = {
    date(2026, 10, 20): "విజయదశమి (Vijaya Dasami / Dussehra)",
    date(2026, 11, 8): "దీపావళి (Deepavali)",
    date(2026, 11, 10): "కార్తీక మాసం ప్రారంభం (Karthika Masam begins)",
    date(2026, 11, 16): "1వ కార్తీక సోమవారం (1st Karthika Somavaram -- Shiva pooja)",
    date(2026, 11, 23): "2వ కార్తీక సోమవారం (2nd Karthika Somavaram -- Shiva pooja)",
    date(2026, 11, 24): "కార్తీక పౌర్ణమి (Karthika Pournami)",
    date(2026, 11, 30): "3వ కార్తీక సోమవారం (3rd Karthika Somavaram -- Shiva pooja)",
    date(2026, 12, 7): "4వ కార్తీక సోమవారం (4th Karthika Somavaram -- Shiva pooja)",
    date(2026, 12, 8): "కార్తీక మాసం ముగింపు (Karthika Masam ends)",
}

# Tithi names that make ANY day worth a Shorts post, regardless of
# month. Keyed on BOTH forms actually seen in real data:
#   - Telugu (Prokerala provider translates English->Telugu internally
#     before this ever reaches us, per prokerala_provider.py's own
#     cost-saving design -- confirmed via a real live run returning
#     "త్రయోదశి, చతుర్దశి" instead of the English "Trayodashi").
#   - English romanized (DummyPanchangProvider returns this directly,
#     untranslated -- used in tests/dummy-provider runs).
# Telugu spellings confirmed against images/telugu_text.py's own
# translation table, the single source of truth for this project.
_SPECIAL_TITHIS: dict[str, str] = {
    "purnima": "పౌర్ణమి (Full Moon) -- good day for a Shorts post",
    "pournami": "పౌర్ణమి (Full Moon) -- good day for a Shorts post",
    "పౌర్ణమి": "పౌర్ణమి (Full Moon) -- good day for a Shorts post",
    "amavasya": "అమావాస్య (New Moon) -- good day for a Shorts post",
    "అమావాస్య": "అమావాస్య (New Moon) -- good day for a Shorts post",
    "ekadashi": "ఏకాదశి -- good day for a Vishnu-themed Shorts post",
    "ఏకాదశి": "ఏకాదశి -- good day for a Vishnu-themed Shorts post",
    "trayodashi": "త్రయోదశి (Pradosham likely this evening) -- good day for a Shiva-themed Shorts post",
    "త్రయోదశి": "త్రయోదశి (Pradosham likely this evening) -- good day for a Shiva-themed Shorts post",
}


def main() -> int:
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    print(f"Checking {today.isoformat()}...\n")

    found_anything = False

    hardcoded_match = FESTIVALS_2026.get(today)
    if hardcoded_match:
        print(f"festival TODAY: {hardcoded_match}")
        found_anything = True

    try:
        provider = get_panchang_provider(settings)
        panchang = provider.fetch(today)
        tithi = panchang.tithi
        matched_special = next(
            (label for name, label in _SPECIAL_TITHIS.items() if name.lower() in tithi.lower()),
            None,
        )
        if matched_special:
            print(f"Today's tithi is special: {tithi} -> {matched_special}")
            found_anything = True
        else:
            print(f"Today's tithi: {tithi} (not one of the recurring special observances)")
    except AppError as exc:
        print(f"(Could not fetch live tithi to check Amavasya/Pournami/Ekadashi/Pradosham: {exc})")

    print()
    if found_anything:
        print("=> Worth running the Community Post and/or a themed Shorts post today.")
    else:
        print("=> No special day today -- regular Shorts only.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
