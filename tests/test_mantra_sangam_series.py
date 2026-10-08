import re

from channels.mantra_sangam import metadata_series, series


def test_purana_rows_complete_and_hindi():
    rows = series._rows("purana")
    assert len(rows) == 70 and len({r["id"] for r in rows}) == 70
    for r in rows:
        assert r["story_hi"] and r["moral_hi"] and r["title_en"]
        assert not re.search("[ఀ-౿]", "".join(r.values()))


def test_titles_mix_hindi_and_english_and_fit():
    for kind in ("purana", "rashi"):
        for r in series._rows(kind):
            t = metadata_series.title(series.to_row(kind, r))
            assert len(t) <= 100
            assert re.search("[ऀ-ॿ]", t) and re.search("[A-Za-z]{3}", t), t


def test_fetch_row_advances_and_wraps():
    f = series.fetch_row_for("rashi")
    assert f([])["id"] == "r01" and f(["r01"])["id"] == "r02"
    ids = [f"r{i:02d}" for i in range(1, 13)]
    assert f(ids)["id"] == "r01"
