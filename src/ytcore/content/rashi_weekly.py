"""Weekly Rashi mantra table (Sunday to Saturday), chosen from that week's planet positions.

One mantra per rashi per week. The planet is picked with the traditional "house from your moon-sign"
(gochara) rule using sidereal (Lahiri) positions from the local Swiss Ephemeris, taken at the middle of
the week (Wednesday noon IST). Slow, heavy planets are checked first (Saturn, Jupiter, Rahu, Mars,
Sun, Mercury, Venus): the first planet standing in a difficult house for that rashi gives the week's
mantra (to pacify it). Saturn uses the same Sade Sati / Ashtama / Kantaka houses as the old daily
series. If nothing is difficult, the Guru (Jupiter) mantra is used to increase the good. Everything is deterministic, so a re-run for the same week gives the same table.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import swisseph as swe

IST = ZoneInfo("Asia/Kolkata")

RASHIS = [  # (telugu, hindi, english)
    ("మేషం", "मेष", "Aries"), ("వృషభం", "वृषभ", "Taurus"), ("మిథునం", "मिथुन", "Gemini"),
    ("కర్కాటకం", "कर्क", "Cancer"), ("సింహం", "सिंह", "Leo"), ("కన్య", "कन्या", "Virgo"),
    ("తుల", "तुला", "Libra"), ("వృశ్చికం", "वृश्चिक", "Scorpio"), ("ధనుస్సు", "धनु", "Sagittarius"),
    ("మకరం", "मकर", "Capricorn"), ("కుంభం", "कुंभ", "Aquarius"), ("మీనం", "मीन", "Pisces"),
]

# planet key -> (swisseph id, telugu mantra, hindi mantra, English name, DIFFICULT houses counted from the rashi)
PLANETS = {
    "saturn": (swe.SATURN, "ఓం శనయే నమః", "ॐ शनये नमः", "Saturn", {12, 1, 2, 8, 4}),
    "rahu": (swe.MEAN_NODE, "ఓం రాహవే నమః", "ॐ राहवे नमः", "Rahu", {1, 5, 8, 12}),
    "jupiter": (swe.JUPITER, "ఓం గురవే నమః", "ॐ गुरवे नमः", "Jupiter", {1, 3, 4, 6, 8, 10, 12}),
    "mars": (swe.MARS, "ఓం అంగారకాయ నమః", "ॐ अंगारकाय नमः", "Mars", {1, 2, 4, 5, 7, 8, 9, 10, 12}),
    "sun": (swe.SUN, "ఓం సూర్యాయ నమః", "ॐ सूर्याय नमः", "Sun", {1, 2, 4, 5, 7, 8, 9, 12}),
    "mercury": (swe.MERCURY, "ఓం బుధాయ నమః", "ॐ बुधाय नमः", "Mercury", {1, 3, 5, 7, 9, 12}),
    "venus": (swe.VENUS, "ఓం శుక్రాయ నమః", "ॐ शुक्राय नमः", "Venus", {6, 7, 10}),
}
PRIORITY = ["saturn", "jupiter", "rahu", "mars", "sun", "mercury", "venus"]


def week_start(day: dt.date) -> dt.date:
    """The Sunday on or before `day`."""
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


def planet_signs(start: dt.date) -> dict[str, int]:
    """Sidereal sign index (0 = Mesha) of each planet at Wednesday noon IST of the week."""
    mid = dt.datetime.combine(start + dt.timedelta(days=3), dt.time(12, 0), tzinfo=IST)
    utc = mid.astimezone(dt.timezone.utc)
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    out = {}
    for key, (pid, *_rest) in PLANETS.items():
        lon = swe.calc_ut(jd, pid, flags)[0][0]
        out[key] = int(lon // 30) % 12
    return out


def pick_planet(rashi_index: int, signs: dict[str, int]) -> str:
    for key in PRIORITY:
        house = (signs[key] - rashi_index) % 12 + 1
        if house in PLANETS[key][4]:
            return key  # a difficult house: chant to pacify this planet
    return "jupiter"  # nothing difficult this week: Guru mantra to increase the good


def weekly_rows(day: dt.date, lang: str = "te") -> list[dict]:
    """12 rows for the week containing `day`: name (te/hi), English name, planet, mantra."""
    start = week_start(day)
    signs = planet_signs(start)
    rows = []
    for i, (te, hi, en) in enumerate(RASHIS):
        key = pick_planet(i, signs)
        _pid, m_te, m_hi, planet_en, _fav = PLANETS[key]
        rows.append({"index": i, "name": te if lang == "te" else hi, "name_en": en,
                     "planet": planet_en, "mantra": m_te if lang == "te" else m_hi})
    return rows


TE_MONTHS = ["", "జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జూలై", "ఆగస్టు", "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"]
HI_MONTHS = ["", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]


def date_range_text(start: dt.date, lang: str = "te") -> str:
    end = start + dt.timedelta(days=6)
    months = TE_MONTHS if lang == "te" else HI_MONTHS
    if start.month == end.month:
        return f"{start.day} - {end.day} {months[end.month]} {end.year}"
    return f"{start.day} {months[start.month]} - {end.day} {months[end.month]} {end.year}"
