from __future__ import annotations

from datetime import date

from ytcore.core.models import Deity
from ytcore.images.telugu_text import (
    DEITY_TELUGU_NAMES,
    NAKSHATRAM_TELUGU,
    PANCHANG_LABELS,
    TITHI_TELUGU,
    YOGA_TELUGU,
    format_telugu_date,
    translate_nakshatram,
    translate_tithi,
    translate_yoga,
)


def test_format_telugu_date_monday() -> None:
    result = format_telugu_date(date(2026, 7, 20))  # a Monday
    assert result.startswith("20 జూలై 2026")
    assert result.endswith("సోమవారం")


def test_format_telugu_date_sunday() -> None:
    result = format_telugu_date(date(2026, 7, 26))  # a Sunday
    assert result.endswith("ఆదివారం")


def test_format_telugu_date_uses_no_telugu_numerals() -> None:
    result = format_telugu_date(date(2026, 9, 13))
    telugu_digits = "౦౧౨౩౪౫౬౭౮౯"
    assert not any(ch in result for ch in telugu_digits)


def test_all_deities_have_telugu_names() -> None:
    for deity in Deity:
        assert deity in DEITY_TELUGU_NAMES
        assert DEITY_TELUGU_NAMES[deity]


def test_panchang_labels_cover_all_fields() -> None:
    expected_fields = {
        "tithi", "nakshatram", "karana", "yoga", "varjyam", "rahu_kalam", "yamagandam",
        "gulika_kalam", "durmuhurtham", "abhijit_muhurtham", "sunrise", "sunset",
        "moonrise", "moonset", "amrit_kaal",
    }
    assert set(PANCHANG_LABELS.keys()) == expected_fields


def test_tithi_telugu_covers_known_spelling_variants() -> None:
    assert all(TITHI_TELUGU.values())
    # Both the dummy-provider spelling and the real Prokerala spelling
    # for the same tithi position are present, even though they render
    # slightly different Telugu text -- that's fine, they come from
    # different providers and each is individually correct.
    assert TITHI_TELUGU["Vidhiya"] == "విదియ"
    assert TITHI_TELUGU["Dwitiya"] == "ద్వితీయ"
    assert TITHI_TELUGU["Thadiya"] == "తదియ"
    assert TITHI_TELUGU["Tritiya"] == "తృతీయ"


def test_nakshatram_telugu_covers_known_spelling_variants() -> None:
    assert all(NAKSHATRAM_TELUGU.values())
    assert NAKSHATRAM_TELUGU["Chitta"] == "చిత్త"
    assert NAKSHATRAM_TELUGU["Chitra"] == "చిత్త"


def test_yoga_telugu_covers_sukla_spelling_variant() -> None:
    assert all(YOGA_TELUGU.values())
    assert translate_yoga("Sukla") == "శుక్ల"
    assert translate_yoga("Shukla") == "శుక్రము"


def test_translate_tithi_known_value() -> None:
    assert translate_tithi("Trayodashi") == "త్రయోదశి"


def test_translate_tithi_unknown_value_falls_back() -> None:
    assert translate_tithi("SomeUnknownTithi") == "SomeUnknownTithi"


def test_translate_nakshatram_known_value() -> None:
    assert translate_nakshatram("Moola") == "మూల"


def test_translate_nakshatram_unknown_value_falls_back() -> None:
    assert translate_nakshatram("SomeUnknownNakshatram") == "SomeUnknownNakshatram"


def test_dummy_provider_tithis_all_translatable() -> None:
    from ytcore.panchang.dummy_provider import _TITHIS

    for tithi in _TITHIS:
        assert tithi in TITHI_TELUGU, f"{tithi!r} has no Telugu translation"


def test_dummy_provider_nakshatrams_all_translatable() -> None:
    from ytcore.panchang.dummy_provider import _NAKSHATRAMS

    for nakshatram in _NAKSHATRAMS:
        assert nakshatram in NAKSHATRAM_TELUGU, f"{nakshatram!r} has no Telugu translation"
