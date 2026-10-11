"""Local (no API) panchang must agree with the Prokerala values Channel A posted for 2026-10-08 (Hyderabad)."""
import re
from datetime import date, datetime

from mahanavi.panchang.local_provider import HYDERABAD, LocalPanchangProvider


def _mins(s):
    return datetime.strptime(s.strip(), "%I:%M %p").hour * 60 + datetime.strptime(s.strip(), "%I:%M %p").minute


def _close(a, b, tol=4):
    ra = [_mins(x) for x in re.split(r"\s-\s", a)]
    rb = [_mins(x) for x in re.split(r"\s-\s", b)]
    return all(abs(x - y) <= tol for x, y in zip(ra, rb))


def test_matches_prokerala_for_2026_10_08_hyderabad():
    p = LocalPanchangProvider(*HYDERABAD).fetch(date(2026, 10, 8))
    assert p.varjyam == "05:33 AM - 07:08 AM, 04:32 AM - 06:08 AM"  # exact
    assert _close(p.rahu_kalam, "01:31 PM - 02:59 PM")
    assert _close(p.yamagandam, "06:11 AM - 07:39 AM")
    assert _close(p.gulika_kalam, "09:07 AM - 10:35 AM")
    d1, d2 = p.durmuhurtham.split(", ")
    assert _close(d1, "10:06 AM - 10:53 AM") and _close(d2, "02:48 PM - 03:35 PM")


def test_wednesday_has_no_abhijit_and_every_day_computes():
    prov = LocalPanchangProvider()
    assert prov.fetch(date(2026, 10, 14)).abhijit_muhurtham == ""
    for i in range(1, 15):
        p = prov.fetch(date(2026, 11, i))
        assert p.rahu_kalam and p.durmuhurtham and p.varjyam
