"""LocalPanchangProvider: panchang computed on this machine with the Swiss Ephemeris (pyswisseph).

No API, no quota, no network -- written 2026-10-08 so the Hindi channel (Channel B)
never spends Prokerala credits. Sunrise/sunset come from the ephemeris; Rahu Kalam, Yamagandam,
Gulika, Durmuhurtham and Abhijit are the standard weekday tables on the day length; tithi,
nakshatra, yoga, karana and Varjyam come from the Lahiri sidereal Sun/Moon longitudes.

Amrit Kaal is intentionally left empty (its per-nakshatra table is not used here).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

from ytcore.core.interfaces import PanchangProvider
from ytcore.core.models import PanchangData
from ytcore.exceptions import PanchangFetchError

# Segment numbers (1..8 of the daytime split in eight), weekday Mon=0..Sun=6
RAHU_SEG = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_SEG = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULIKA_SEG = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
# Durmuhurtham: muhurta numbers (1..15 of the daytime split in fifteen)
DURM = {0: (9, 12), 1: (4,), 2: (8,), 3: (6, 12), 4: (4, 9), 5: (1,), 6: (14,)}
# Varjyam start, in ghatis (of 60) from the start of each nakshatra, Ashwini..Revati
VARJYAM_GHATI = [50, 24, 30, 40, 14, 11, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14, 20, 24, 20, 10, 10, 18, 16, 24, 30]

TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami",
          "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
              "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shula",
         "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
         "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANAS_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
KARANAS_FIXED = {57: "Shakuni", 58: "Chatushpada", 59: "Naga", 0: "Kimstughna"}

DELHI = (28.6139, 77.2090)
HYDERABAD = (17.3850, 78.4867)


def _fmt(t: datetime) -> str:
    return t.strftime("%I:%M %p")


def _rng(a: datetime, b: datetime) -> str:
    return f"{_fmt(a)} - {_fmt(b)}"


class LocalPanchangProvider(PanchangProvider):
    def __init__(self, latitude: float = DELHI[0], longitude: float = DELHI[1], tz: str = "Asia/Kolkata"):
        self.lat, self.lon, self.tz = latitude, longitude, ZoneInfo(tz)

    # ---- astronomy helpers -------------------------------------------------
    def _jd(self, dt_local: datetime) -> float:
        u = dt_local.astimezone(ZoneInfo("UTC"))
        return float(swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600))

    def _from_jd(self, jd: float) -> datetime:
        y, m, d, h = swe.revjul(jd)
        base = datetime(y, m, d, tzinfo=ZoneInfo("UTC")) + timedelta(hours=h)
        return base.astimezone(self.tz)

    def _rise_set(self, d: date, body_flag: int) -> datetime:
        start = datetime(d.year, d.month, d.day, tzinfo=self.tz)
        jd0 = self._jd(start) - 0.0
        res, tret = swe.rise_trans(jd0, swe.SUN, body_flag, (self.lon, self.lat, 0.0), 1013.25, 15.0)
        if res < 0:
            raise PanchangFetchError("could not compute sunrise/sunset")
        return self._from_jd(tret[0])

    def _longitudes(self, dt_local: datetime) -> tuple[float, float]:
        jd = self._jd(dt_local)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_MOSEPH
        sun = swe.calc_ut(jd, swe.SUN, flags)[0][0]
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0]
        return sun, moon

    def _moon_nak_pos(self, dt: datetime) -> float:
        return self._longitudes(dt)[1] / (360 / 27)

    def _find_boundary(self, t0: datetime, target_fn: Callable[[datetime], Any], direction: int, step_min: int = 20) -> datetime:
        """Walk from t0 in `direction` until target_fn() changes value, then bisect to the minute."""
        base = target_fn(t0)
        lo, t = t0, t0
        for _ in range(int(40 * 60 / step_min)):
            t = lo + timedelta(minutes=step_min * direction)
            if target_fn(t) != base:
                a, b = (lo, t) if direction > 0 else (t, lo)
                # bisect between a (value == base side) and b
                inside, outside = (a, b) if direction > 0 else (b, a)
                for _ in range(14):
                    mid = inside + (outside - inside) / 2
                    if target_fn(mid) == base:
                        inside = mid
                    else:
                        outside = mid
                return outside
            lo = t
        raise PanchangFetchError("boundary search failed")

    # ---- main --------------------------------------------------------------
    def fetch(self, for_date: date) -> PanchangData:
        try:
            sunrise = self._rise_set(for_date, swe.CALC_RISE)
            sunset = self._rise_set(for_date, swe.CALC_SET)
            nxt = self._rise_set(for_date + timedelta(days=1), swe.CALC_RISE)
        except Exception as exc:  # noqa: BLE001
            raise PanchangFetchError(f"local panchang failed: {exc}") from exc

        day = sunset - sunrise
        wd = for_date.weekday()
        seg = day / 8
        mu = day / 15

        def seg_range(n: int) -> str:
            return _rng(sunrise + seg * (n - 1), sunrise + seg * n)

        durm = ", ".join(_rng(sunrise + mu * (n - 1), sunrise + mu * n) for n in DURM[wd])
        abhijit = "" if wd == 2 else _rng(sunrise + mu * 7, sunrise + mu * 8)

        sun, moon = self._longitudes(sunrise)
        tithi_no = int(((moon - sun) % 360) // 12)
        paksha = "Shukla" if tithi_no < 15 else "Krishna"
        tithi = TITHIS[tithi_no % 15] if tithi_no not in (14, 29) else ("Purnima" if tithi_no == 14 else "Amavasya")
        tithi = f"{paksha} {tithi}"
        nak_idx = int(moon // (360 / 27)) % 27
        yoga = YOGAS[int(((sun + moon) % 360) // (360 / 27)) % 27]
        karana_no = int(((moon - sun) % 360) // 6)
        karana: str = (KARANAS_FIXED[karana_no] if karana_no in KARANAS_FIXED
                       else KARANAS_MOVABLE[(karana_no - 1) % 7])

        # Varjyam: nakshatra running at sunrise, plus the next one if its Varjyam falls before next sunrise.
        def nak_of(t: datetime) -> int:
            return int(self._moon_nak_pos(t)) % 27

        varjyam = []
        for probe in (sunrise, sunrise + timedelta(hours=14), sunrise + timedelta(hours=26)):
            n = nak_of(probe)
            try:
                start = self._find_boundary(probe, nak_of, -1)
                end = self._find_boundary(probe, nak_of, +1)
            except PanchangFetchError:
                continue
            length = end - start
            vs = start + length * (VARJYAM_GHATI[n] / 60)
            ve = vs + length / 15
            if ve > sunrise and vs < nxt + timedelta(hours=2):
                item = _rng(vs, ve)
                if item not in varjyam:
                    varjyam.append(item)

        return PanchangData(
            date_=for_date, tithi=tithi, nakshatram=NAKSHATRAS[nak_idx], varjyam=", ".join(varjyam),
            rahu_kalam=seg_range(RAHU_SEG[wd]), yamagandam=seg_range(YAMA_SEG[wd]),
            gulika_kalam=seg_range(GULIKA_SEG[wd]), durmuhurtham=durm, abhijit_muhurtham=abhijit,
            sunrise=time(sunrise.hour, sunrise.minute), sunset=time(sunset.hour, sunset.minute),
            karana=karana, yoga=yoga, amrit_kaal="",
            marriage_muhurats="", source="local-swisseph",
        )

    def brahma_muhurta(self, for_date: date) -> str:
        sunrise = self._rise_set(for_date, swe.CALC_RISE)
        return _rng(sunrise - timedelta(minutes=96), sunrise - timedelta(minutes=48))
