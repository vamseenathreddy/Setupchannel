import csv
import re
import glob
from pathlib import Path

from channels.trance_beats import metadata as m

DATA = Path(__file__).resolve().parents[1] / "channels" / "trance_beats" / "data"


def test_every_row_metadata_within_youtube_limits():
    ids = set()
    for fn in glob.glob(str(DATA / "*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8")):
            assert r["id"] not in ids, f"duplicate id {r['id']}"
            ids.add(r["id"])
            b = m.bundle(r, None)
            assert len(b["title"]) <= 100
            assert re.search(r"Bhagavad Gita|Bhagavatam|Krishna Mantra|Bhajan|Kirtan|Teaching", b["title"]), b["title"]
            assert sum(m.tag_cost(t) + 1 for t in b["tags"]) <= 500
            assert len(b["description"]) < 4900
            assert len(m.hashtags(r, None)) <= 15
            assert b["language"] == "hi"


def test_gita_verse_reference_becomes_tags():
    r = {"id": "g1", "category": "gita", "text_primary": "x", "text_secondary": "(गीता 2.47)", "source": "s"}
    assert "Bhagavad Gita 2.47" in m.tags(r, None)
