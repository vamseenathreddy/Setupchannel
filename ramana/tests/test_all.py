"""Run with: python -m pytest -q   (from the repo root)"""
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "ci"))

import ramana_gate as gate  # noqa: E402
from src import common, metadata, pick, render  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")
ROWS = common.load_rows()


def special_for_row(r):
    if not r["special"]:
        return None
    return common.special_for(dt.date(2026, int(r["special"][:2]), int(r["special"][3:])))


# ---------- gate ----------
def test_target_minute_is_in_window_and_deterministic():
    for d in range(60):
        date = dt.date(2026, 10, 1) + dt.timedelta(days=d)
        t = gate.target_time(date)
        assert dt.datetime.combine(date, dt.time(0, 0), tzinfo=IST) <= t <= dt.datetime.combine(date, dt.time(0, 50), tzinfo=IST)
        assert t == gate.target_time(date)
    assert len({gate.target_time(dt.date(2026, 10, 1) + dt.timedelta(days=d)).minute for d in range(30)}) > 5


def test_gate_decisions():
    date = dt.date(2026, 10, 7)
    tgt = gate.target_time(date)
    empty = {"posted": {}, "used_ids": []}
    post, msg, _ = gate.decide(tgt - dt.timedelta(minutes=1), empty)
    assert not post and "before target" in msg
    post, msg, _ = gate.decide(tgt, empty)
    assert post and "DECISION: post" in msg
    post, _, _ = gate.decide(tgt + dt.timedelta(minutes=30), empty)
    assert post
    done = {"posted": {"2026-10-07": {"row": "q001", "video_id": "x"}}, "used_ids": ["q001"]}
    post, msg, _ = gate.decide(tgt + dt.timedelta(minutes=5), done)
    assert not post and "already done" in msg
    late = dt.datetime(2026, 10, 7, 2, 0, tzinfo=IST)
    post, msg, _ = gate.decide(late, empty)
    assert not post and "missed window" in msg
    post, _, _ = gate.decide(tgt + dt.timedelta(minutes=1), empty, force=True)
    assert post
    post, _, _ = gate.decide(tgt + dt.timedelta(minutes=1), done, force=True)
    assert not post  # force can never double post


# ---------- picking ----------
def test_pick_is_deterministic_and_never_repeats():
    used, seen = [], set()
    for i in range(31):
        date = dt.date(2026, 10, 7) + dt.timedelta(days=i)
        a, _ = pick.choose_row(ROWS, date, used)
        b, _ = pick.choose_row(ROWS, date, used)
        assert a["id"] == b["id"]
        if a["special"]:
            continue
        assert a["id"] not in seen
        seen.add(a["id"])
        used.append(a["id"])


def test_warmup_skips_death_rows_and_special_day_wins():
    for i in range(200):
        row, _ = pick.choose_row(ROWS, dt.date(2026, 10, 7) + dt.timedelta(days=i % 14), [])
        assert not any(w in row["english"].lower() for w in pick.SENSITIVE)
    row, reason = pick.choose_row(ROWS, dt.date(2027, 4, 14), [])
    assert reason == "special-day" and "Mahasamadhi" in row["english"]


def test_all_pool_rows_are_reachable():
    assert len(pick.unused_pool(ROWS, [])) >= 30


# ---------- metadata ----------
def test_titles_hashtags_tags_descriptions_within_limits():
    for r in ROWS:
        sp = special_for_row(r)
        t = metadata.title(r, sp)
        assert 0 < len(t) <= 100, (r["id"], len(t))
        assert len(metadata.hashtags(r, sp)) <= 15
        tg = metadata.tags(r, sp)
        assert sum(metadata.tag_cost(x) for x in tg) + len(tg) - 1 <= 500
        assert len({x.lower() for x in tg}) == len(tg)
        assert len(metadata.description(r, sp, playlist_url="https://youtube.com/playlist?list=X", contact="a@b.c")) < 5000
        assert len(metadata.localizations(r, sp)["te"]["title"]) <= 100
        assert "Visuals are digitally created" in metadata.description(r, sp)  # disclosure is always present
        assert metadata.srt(r["english"]).startswith("1\n00:00:00,000 --> 00:00:05,000")


def test_title_starts_with_the_text_on_the_short():
    r = next(x for x in ROWS if x["id"] == "q001")
    assert metadata.title(r, None).startswith("Ask yourself: Who am I?")


# ---------- render fit (worst case: every row, every layout) ----------
def test_text_fits_for_every_row_and_layout():
    for r in ROWS:
        for layout in render.LAYOUTS:
            _laid, total, fits, scale = render.fit_text(r, layout, render.TEXT_TOP_H)
            assert fits and scale >= 0.52, (r["id"], scale, total)


def test_telugu_has_no_missing_glyphs():
    from fontTools.ttLib import TTFont
    cmap = TTFont(str(render.FONT_TE)).getBestCmap()
    quotes = "'\"`‘’“”"  # stripped before drawing
    for r in ROWS:
        for ch in r["telugu"].replace("|", " "):
            assert ch in quotes or ord(ch) in cmap or ch in "‌‍", (r["id"], repr(ch))
