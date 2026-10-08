import re
from datetime import date

import pytest

from channels.mantra_sangam import metadata_timings, timings


@pytest.mark.parametrize("kind", timings.KINDS)
def test_rows_and_metadata(kind):
    for day in (date(2026, 10, 8), date(2026, 10, 14), date(2026, 11, 3)):  # includes a Wednesday
        row = timings.timing_row(kind, day)
        assert row["t_time"] and row["t_title"] and row["t_sub"] and row["t_opinion"]
        meta = metadata_timings.bundle(row)
        t = meta["title"]
        assert len(t) <= 100
        assert re.search(r"[ऀ-ॿ]", t) and re.search(r"[A-Za-z]{3,}", t), t  # Hindi AND English
        assert meta["language"] == "hi"
        assert sum(len(x) + (2 if " " in x else 0) for x in meta["tags"]) <= 500
        assert len([h for h in metadata_timings.hashtags(row)]) <= 15


def test_wednesday_shubh_uses_brahma_muhurat():
    row = timings.timing_row("shubh", date(2026, 10, 14))
    assert row["t_label"] == "ब्रह्म मुहूर्त"
