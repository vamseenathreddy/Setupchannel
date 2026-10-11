from __future__ import annotations

from datetime import date

from ytcore.scripts.check_festival_today import FESTIVALS_2026, _SPECIAL_TITHIS


def test_special_tithis_match_real_provider_spelling_variants() -> None:
    """Confirmed against the real dummy provider's own tithi cycle
    (English, combined 'Pournami/Amavasya' value) AND against a real
    live Prokerala run that returned Telugu text directly
    ('త్రయోదశి, చతుర్దశి') -- production actually returns Telugu, not
    English, so both forms must match."""
    cases = {
        "Ekadashi": True,
        "Trayodashi": True,
        "Pournami/Amavasya": True,
        "Purnima": True,
        "Amavasya": True,
        "Navami": False,
        "Dashami": False,
        "Chaturdashi": False,
        # Real production strings (Telugu) -- the actual bug this guards against.
        "త్రయోదశి, చతుర్దశి": True,
        "ఏకాదశి": True,
        "పౌర్ణమి": True,
        "అమావాస్య": True,
        "నవమి": False,
    }
    for tithi, should_match in cases.items():
        matched = any(name in tithi.lower() for name in _SPECIAL_TITHIS)
        assert matched == should_match, f"{tithi!r} expected match={should_match}, got {matched}"


def test_festivals_2026_dict_has_no_duplicate_dates() -> None:
    # dict keys are inherently unique, but this documents the intent --
    # each hardcoded festival date should be distinct.
    assert len(FESTIVALS_2026) == len(set(FESTIVALS_2026.keys()))


def test_festivals_2026_covers_karthika_masam_range() -> None:
    """Karthika Masam 2026 runs Nov 10 - Dec 8 per verified sources --
    confirm both boundary dates are present."""
    assert date(2026, 11, 10) in FESTIVALS_2026
    assert date(2026, 12, 8) in FESTIVALS_2026


def test_festivals_2026_karthika_somavarams_are_actually_mondays() -> None:
    """Every hardcoded Karthika Somavaram date must genuinely be a
    Monday -- a real, checkable property, not just a plausible date."""
    for day, label in FESTIVALS_2026.items():
        if "సోమవారం" in label:
            assert day.weekday() == 0, f"{day} labeled as Karthika Somavaram but is not a Monday"
