"""
DummyPanchangProvider: deterministic, offline Panchang data.

Purpose: lets you run and test the ENTIRE pipeline (image selection ->
rendering -> SEO -> upload) without a live Panchang API/scraper being
wired up yet, and without network flakiness in CI. Values cycle through
plausible-looking Telugu Panchang terms based on the date, so output
differs day to day but is reproducible for the same date.

This is NOT astronomically accurate — do not use it for real posts.
Switch MAHANAVI_PANCHANG_PROVIDER to "api" or "scraper" for production.
"""

from __future__ import annotations

from datetime import date, time

from ytcore.core.interfaces import PanchangProvider
from ytcore.core.models import PanchangData

_TITHIS = [
    "Padyami", "Vidhiya", "Thadiya", "Chavithi", "Panchami",
    "Shashti", "Sapthami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Pournami/Amavasya",
]

_NAKSHATRAMS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushyami", "Ashlesha", "Makha", "Pubba", "Uttara",
    "Hasta", "Chitta", "Swati", "Vishakha", "Anuradha", "Jyeshta",
    "Moola", "Poorvashada", "Uttarashada", "Sravanam", "Dhanishta",
    "Shatabhisham", "Poorvabhadra", "Uttarabhadra", "Revati",
]

_KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti",
]

_YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]


class DummyPanchangProvider(PanchangProvider):
    """Offline, deterministic placeholder implementation of PanchangProvider."""

    def fetch(self, for_date: date) -> PanchangData:
        ordinal = for_date.toordinal()
        tithi = _TITHIS[ordinal % len(_TITHIS)]
        nakshatram = _NAKSHATRAMS[ordinal % len(_NAKSHATRAMS)]
        karana = _KARANAS[ordinal % len(_KARANAS)]
        yoga = _YOGAS[ordinal % len(_YOGAS)]

        return PanchangData(
            date_=for_date,
            tithi=tithi,
            nakshatram=nakshatram,
            varjyam="10:12 AM - 11:42 AM",
            rahu_kalam=self._rahu_kalam_for_weekday(for_date.weekday()),
            yamagandam="10:30 AM - 12:00 PM",
            gulika_kalam="01:30 PM - 03:00 PM",
            durmuhurtham="08:06 AM - 08:52 AM",
            abhijit_muhurtham="11:48 AM - 12:38 PM",
            sunrise=time(5, 58),
            sunset=time(18, 45),
            karana=karana,
            yoga=yoga,
            amrit_kaal="07:03 AM - 08:40 AM",
            moonrise=time(7, 47),
            moonset=time(19, 42),
            festivals=[],  # dummy provider has no real festival calendar
            marriage_muhurats="",  # dummy provider has no real muhurat calculation
            source="dummy",
        )

    @staticmethod
    def _rahu_kalam_for_weekday(weekday: int) -> str:
        # Rahu Kalam window shifts by weekday in real panchang; approximated here.
        windows = {
            0: "07:30 AM - 09:00 AM",  # Monday
            1: "03:00 PM - 04:30 PM",  # Tuesday
            2: "12:00 PM - 01:30 PM",  # Wednesday
            3: "01:30 PM - 03:00 PM",  # Thursday
            4: "10:30 AM - 12:00 PM",  # Friday
            5: "09:00 AM - 10:30 AM",  # Saturday
            6: "04:30 PM - 06:00 PM",  # Sunday
        }
        return windows[weekday]
