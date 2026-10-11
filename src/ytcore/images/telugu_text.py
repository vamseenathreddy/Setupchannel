"""
Telugu text constants and formatting helpers used by the image renderer.

Kept separate from renderer.py so the Telugu vocabulary (labels, month
names, deity names) can be reviewed/edited by a Telugu speaker without
touching any Pillow/layout code.
"""

from __future__ import annotations

from datetime import date

from ytcore.core.models import Deity

TELUGU_WEEKDAYS: dict[int, str] = {
    0: "సోమవారం",   # Monday
    1: "మంగళవారం",  # Tuesday
    2: "బుధవారం",    # Wednesday
    3: "గురువారం",   # Thursday
    4: "శుక్రవారం",   # Friday
    5: "శనివారం",    # Saturday
    6: "ఆదివారం",    # Sunday
}

TELUGU_MONTHS: dict[int, str] = {
    1: "జనవరి", 2: "ఫిబ్రవరి", 3: "మార్చి", 4: "ఏప్రిల్",
    5: "మే", 6: "జూన్", 7: "జూలై", 8: "ఆగస్టు",
    9: "సెప్టెంబర్", 10: "అక్టోబర్", 11: "నవంబర్", 12: "డిసెంబర్",
}

DEITY_TELUGU_NAMES: dict[Deity, str] = {
    Deity.SHIVA: "శివుడు",
    Deity.HANUMAN: "హనుమంతుడు",
    Deity.GANESHA: "గణేశుడు",
    Deity.SAI: "సాయిబాబా",
    Deity.LAKSHMI: "లక్ష్మీదేవి",
    Deity.VENKATESWARA: "వేంకటేశ్వర స్వామి",
    Deity.SURYA: "సూర్యభగవానుడు",
    Deity.DATTATREYA: "దత్తాత్రేయ స్వామి",
}

# Order matters here — this is the display order in the Panchang panel.
PANCHANG_LABELS: dict[str, str] = {
    "tithi": "తిథి",
    "nakshatram": "నక్షత్రం",
    "karana": "కరణం",
    "yoga": "యోగం",
    "sunrise": "సూర్యోదయం",
    "sunset": "సూర్యాస్తమయం",
    "moonrise": "చంద్రోదయం",
    "moonset": "చంద్రాస్తమయం",
    "varjyam": "వర్జ్యం",
    "rahu_kalam": "రాహు కాలం",
    "yamagandam": "యమగండం",
    "gulika_kalam": "గుళిక కాలం",
    "durmuhurtham": "దుర్ముహూర్తం",
    "abhijit_muhurtham": "అభిజిత్ ముహూర్తం",
    "amrit_kaal": "అమృత కాలం",
}

# Standard Telugu names for the 15 tithis. Keys match the English names
# used by panchang/dummy_provider.py, PLUS additional standard Sanskrit
# spelling variants confirmed to differ in real Prokerala output (e.g.
# Prokerala returns "Dwitiya"/"Tritiya", not "Vidhiya"/"Thadiya") — a
# lookup miss falls back to the original text (see translate_tithi)
# rather than crashing, but every variant found in real output should be
# added here rather than relied upon to fall back.
TITHI_TELUGU: dict[str, str] = {
    "Padyami": "పాడ్యమి", "Pratipada": "పాడ్యమి",
    "Vidhiya": "విదియ", "Dwitiya": "ద్వితీయ",
    "Thadiya": "తదియ", "Tritiya": "తృతీయ",
    "Chavithi": "చవితి", "Chaturthi": "చతుర్థి",
    "Panchami": "పంచమి",
    "Shashti": "షష్ఠి", "Shashthi": "షష్ఠి",
    "Sapthami": "సప్తమి", "Saptami": "సప్తమి",
    "Ashtami": "అష్టమి", "Navami": "నవమి", "Dashami": "దశమి",
    "Ekadashi": "ఏకాదశి", "Dwadashi": "ద్వాదశి", "Trayodashi": "త్రయోదశి",
    "Chaturdashi": "చతుర్దశి",
    "Pournami/Amavasya": "పౌర్ణమి/అమావాస్య",
    "Purnima": "పౌర్ణమి", "Amavasya": "అమావాస్య",
}

# Standard Telugu names for the 27 nakshatrams, PLUS additional standard
# Sanskrit spelling variants (e.g. Prokerala returns "Chitra", not
# "Chitta") — same fallback behavior as TITHI_TELUGU.
NAKSHATRAM_TELUGU: dict[str, str] = {
    "Ashwini": "అశ్విని", "Bharani": "భరణి", "Krittika": "కృత్తిక",
    "Rohini": "రోహిణి",
    "Mrigashira": "మృగశిర", "Mrigasira": "మృగశిర",
    "Ardra": "ఆరుద్ర",
    "Punarvasu": "పునర్వసు",
    "Pushyami": "పుష్యమి", "Pushya": "పుష్యమి",
    "Ashlesha": "ఆశ్లేష",
    "Makha": "మఖ", "Magha": "మఖ",
    "Pubba": "పుబ్బ", "Purva Phalguni": "పుబ్బ",
    "Uttara": "ఉత్తర", "Uttara Phalguni": "ఉత్తర",
    "Hasta": "హస్త",
    "Chitta": "చిత్త", "Chitra": "చిత్త",
    "Swati": "స్వాతి",
    "Vishakha": "విశాఖ", "Vishaka": "విశాఖ",
    "Anuradha": "అనూరాధ",
    "Jyeshta": "జ్యేష్ఠ", "Jyeshtha": "జ్యేష్ఠ",
    "Moola": "మూల",
    "Poorvashada": "పూర్వాషాఢ", "Purva Ashadha": "పూర్వాషాఢ",
    "Uttarashada": "ఉత్తరాషాఢ", "Uttara Ashadha": "ఉత్తరాషాఢ",
    "Sravanam": "శ్రవణం", "Shravana": "శ్రవణం",
    "Dhanishta": "ధనిష్ఠ", "Dhanishtha": "ధనిష్ఠ",
    "Shatabhisham": "శతభిషం", "Shatabhisha": "శతభిషం",
    "Poorvabhadra": "పూర్వాభాద్ర", "Purva Bhadrapada": "పూర్వాభాద్ర",
    "Uttarabhadra": "ఉత్తరాభాద్ర", "Uttara Bhadrapada": "ఉత్తరాభాద్ర",
    "Revati": "రేవతి",
}


# Standard Telugu names for the 7 karanas. High confidence — this is a
# short, extremely standard list. 3 of these (Garija, Vanija->Panaji
# spelling, Vishti->Bhadra) are additionally confirmed against a real
# Prokerala API response (2026-09-14); the other 4 are standard
# transliteration, not yet cross-checked against a live response.
KARANA_TELUGU: dict[str, str] = {
    "Bava": "బవ", "Balava": "బాలవ", "Kaulava": "కౌలవ", "Taitila": "తైతిల",
    "Garija": "గరజి", "Vanija": "పణజి", "Vishti": "భద్ర", "Vishti / Bhadra": "భద్ర",
}

# Standard Telugu names for the 27 yogas. Only 3 of these (Shukla,
# Brahma, Indra) are confirmed against a real Prokerala API response
# (2026-09-14, all with a "-ము" suffix); the rest are best-effort
# standard transliteration following that same pattern, NOT yet
# cross-checked against live API output — worth a native Telugu
# speaker's once-over before treating this list as fully authoritative,
# same caveat as when TITHI_TELUGU/NAKSHATRAM_TELUGU were first built.
YOGA_TELUGU: dict[str, str] = {
    "Vishkambha": "విష్కంభము", "Vishkumbha": "విష్కంభము",
    "Priti": "ప్రీతి", "Ayushman": "ఆయుష్మాన్",
    "Saubhagya": "సౌభాగ్యము", "Shobhana": "శోభనము", "Atiganda": "అతిగండము",
    "Sukarma": "సుకర్మము", "Dhriti": "ధృతి",
    "Shula": "శూలము", "Shoola": "శూలము",
    "Ganda": "గండము", "Vriddhi": "వృద్ధి", "Dhruva": "ధ్రువము",
    "Vyaghata": "వ్యాఘాతము", "Harshana": "హర్షణము", "Vajra": "వజ్రము",
    "Siddhi": "సిద్ధి", "Vyatipata": "వ్యతీపాతము",
    "Variyana": "వరీయాన్", "Variyan": "వరీయాన్",
    "Parigha": "పరిఘ", "Shiva": "శివము", "Siddha": "సిద్ధము",
    "Sadhya": "సాధ్యము", "Shubha": "శుభము",
    "Shukla": "శుక్రము", "Sukla": "శుక్ల",
    "Brahma": "బ్రహ్మము", "Indra": "ఐంద్రము", "Vaidhriti": "వైధృతి", "Vaidhruthi": "వైధృతి",
}


def format_telugu_date(for_date: date) -> str:
    """Return e.g. '20 జూలై 2026, సోమవారం' for the given date.

    Day/year use plain English numbers per explicit request — Telugu
    numerals are never used anywhere in the rendered output, only month
    and weekday names stay in Telugu script.
    """
    month = TELUGU_MONTHS[for_date.month]
    weekday = TELUGU_WEEKDAYS[for_date.weekday()]
    return f"{for_date.day} {month} {for_date.year}, {weekday}"


def translate_tithi(tithi: str) -> str:
    """Telugu name for a tithi; returns the original text unchanged if not
    in TITHI_TELUGU (e.g. an unexpected value from a real Panchang API)."""
    return TITHI_TELUGU.get(tithi, tithi)


def translate_nakshatram(nakshatram: str) -> str:
    """Telugu name for a nakshatram; same fallback behavior as translate_tithi."""
    return NAKSHATRAM_TELUGU.get(nakshatram, nakshatram)


def translate_karana(karana: str) -> str:
    """Telugu name for a karana; same fallback behavior as translate_tithi."""
    return KARANA_TELUGU.get(karana, karana)


def translate_yoga(yoga: str) -> str:
    """Telugu name for a yoga; same fallback behavior as translate_tithi."""
    return YOGA_TELUGU.get(yoga, yoga)
