"""Daily beej mantra Shorts (content/beej_mantras.py)."""
from datetime import date
from pathlib import Path

import pytest

from mahanavi.config import get_settings
from mahanavi.content import beej_mantras as bm
from mahanavi.images.request_card_renderer import SAFE_BOTTOM, SAFE_L, SAFE_R, SAFE_TOP, RequestCardRenderer


@pytest.mark.parametrize("d,tithi,key", [
    (date(2026, 10, 11), "Shukla Pratipada", "durga"),      # Navaratri
    (date(2026, 10, 12), "Shukla Dwitiya", "bala"),
    (date(2026, 10, 13), "Shukla Tritiya", "gayatri"),
    (date(2026, 10, 14), "Shukla Chaturthi", "annapurna"),
    (date(2026, 10, 15), "Shukla Panchami", "lalita"),
    (date(2026, 10, 16), "Shukla Shashthi", "lakshmi"),
    (date(2026, 10, 18), "Shukla Ashtami", "durgadevi"),
    (date(2026, 10, 19), "Shukla Navami", "mahishasuramardini"),
    (date(2026, 10, 20), "Shukla Dashami", "rajarajeshwari"),  # Vijayadashami
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


def test_navaratri_never_repeats_a_mantra():
    seen = []
    for day in range(11, 21):
        dei, _, _ = bm.pick(date(2026, 10, day), "Shukla Pratipada")
        seen.append(dei.mantra_te)
    assert len(seen) == len(set(seen))


def test_every_short_is_under_five_seconds():
    """Owner rule (2026-10-14): any Short on any channel is under 5 seconds."""
    s = get_settings()
    for name in ("alert", "rashi_mantra", "purana", "purana_concept", "gita_sloka"):
        assert getattr(s, f"{name}_short_duration_seconds") < 5
    for ch in ("mahanavi", "mantra_sangam", "trance_beats"):
        assert bm.build(ch, date(2026, 10, 14), "").total_seconds < 5


def test_every_deity_has_six_benefit_lines_in_both_languages():
    from mahanavi.content.beej_benefits import BENEFITS
    assert set(BENEFITS) == set(bm.DEITIES)
    for key, (te, hi) in BENEFITS.items():
        assert len(te) == 6 and len(hi) == 6, key
        assert all(":" in line for line in te + hi), key


@pytest.mark.parametrize("channel", ["mahanavi", "mantra_sangam"])
def test_benefit_lines_big_inside_safe_zone_and_never_overlap(channel: str, tmp_path: Path):
    """All 22 deities, both languages: six benefit lines drawn, in the safe zone, no two text boxes overlapping."""
    r = RequestCardRenderer(get_settings())
    for key in bm.DEITIES:
        spec = bm.build(channel, date(2026, 10, 24), "Shukla Chaturthi")
        spec = type(spec)(**{**spec.__dict__, "slides": (type(spec.slides[0])(
            "mantra", 4.9, spec.slides[0].label, bm.DEITIES[key].mantra_hi if spec.lang == "hi" else bm.DEITIES[key].mantra_te,
            bm.DEITIES[key].translit, spec.slides[0].meaning,
            __import__("mahanavi.content.beej_benefits", fromlist=["x"]).benefits_for(key, spec.lang == "hi")),)})
        rendered = r.render_all(spec, tmp_path / key)[0]
        boxes = sorted(rendered.boxes, key=lambda b: b[1])
        for x0, y0, x1, y1 in boxes:
            assert x0 >= SAFE_L - 4 and x1 <= SAFE_R + 4 and y0 >= SAFE_TOP and y1 <= SAFE_BOTTOM, key
        for a, b in zip(boxes, boxes[1:]):
            assert b[1] >= a[3] - 6, (key, a, b)  # next line starts below the previous one (small glyph slack)
        # benefit lines are large: 6 of them fit with a line height of at least ~40px
        assert sum(1 for b in boxes if b[1] > 800) >= 6, key
