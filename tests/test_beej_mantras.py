"""Daily beej mantra Shorts (content/beej_mantras.py)."""
from datetime import date
from pathlib import Path

import pytest

from mahanavi.config import get_settings
from mahanavi.content import beej_mantras as bm
from mahanavi.images.request_card_renderer import SAFE_BOTTOM, SAFE_L, SAFE_R, SAFE_TOP, RequestCardRenderer


@pytest.mark.parametrize("d,tithi,key", [
    (date(2026, 10, 11), "Shukla Pratipada", "durga"),      # Navaratri
    (date(2026, 10, 15), "Shukla Panchami", "lakshmi"),
    (date(2026, 10, 18), "Shukla Saptami", "saraswati"),
    (date(2026, 10, 20), "Shukla Dashami", "durga"),         # Vijayadashami
    (date(2026, 10, 10), "Krishna Amavasya", "shani"),       # Shani Amavasya (Saturday)
    (date(2026, 10, 24), "Shukla Chaturthi", "ganesha"),
    (date(2026, 10, 25), "Shukla Pratipada", "surya"),       # Sunday, no tithi rule
    (date(2026, 11, 16), "Krishna Ashtami", "shiva"),        # Karthika Monday beats the tithi
    (date(2026, 10, 29), "Shukla Chaturdashi", "narasimha"),
    (date(2026, 11, 2), "Krishna Chaturdashi", "shiva"),
])
def test_pick(d, tithi, key):
    assert bm.pick(d, tithi)[0].key == key


def test_every_deity_complete():
    for dei in bm.DEITIES.values():
        assert dei.mantra_te.startswith("ఓం") and dei.mantra_hi.startswith("ॐ") and dei.translit.startswith("Om")
        assert dei.gain_te and dei.gain_hi


@pytest.mark.parametrize("channel", sorted(bm.CHANNELS))
def test_build_valid_seo_and_safe_zone(channel: str, tmp_path: Path):
    spec = bm.build(channel, date(2026, 10, 24), "Shukla Chaturthi")
    assert len(spec.title) <= 100 and spec.hashtags[0] == "#Shorts" and len(spec.hashtags) <= 5
    assert len(spec.description()) <= 5000 and len(", ".join(spec.tags)) <= 500
    assert len(spec.slides) == 1 and spec.total_seconds <= 15 and spec.lang == bm.CHANNELS[channel]["lang"]
    for s in RequestCardRenderer(get_settings()).render_all(spec, tmp_path):
        for x0, y0, x1, y1 in s.boxes:
            assert x0 >= SAFE_L - 4 and x1 <= SAFE_R + 4 and y0 >= SAFE_TOP and y1 <= SAFE_BOTTOM


def test_every_day_to_year_end_builds_and_titles_fit():
    from datetime import timedelta
    d = date(2026, 10, 10)
    while d <= date(2026, 12, 31):
        for ch in bm.CHANNELS:
            spec = bm.build(ch, d, "Shukla Saptami")
            assert len(spec.title) <= 100
        d += timedelta(days=1)
