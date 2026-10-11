import datetime as dt

from ytcore.content import rashi_weekly as w


def test_week_is_sunday_to_saturday():
    assert w.week_start(dt.date(2026, 10, 11)) == dt.date(2026, 10, 11)  # Sunday
    assert w.week_start(dt.date(2026, 10, 17)) == dt.date(2026, 10, 11)  # Saturday
    assert w.week_start(dt.date(2026, 10, 18)) == dt.date(2026, 10, 18)
    assert w.date_range_text(dt.date(2026, 10, 11)) == "11 - 17 అక్టోబర్ 2026"
    cross = w.date_range_text(dt.date(2026, 12, 27))  # week spans two months
    assert "డిసెంబర్" in cross and "జనవరి" in cross and cross.endswith("2027")


def test_rows_cover_all_12_and_match_old_saturn_rule():
    rows = w.weekly_rows(dt.date(2026, 10, 11))
    assert len(rows) == 12 and all(r["mantra"].startswith("ఓం") for r in rows)
    saturn = {r["name_en"] for r in rows if r["planet"] == "Saturn"}
    assert saturn == {"Aries", "Leo", "Sagittarius", "Aquarius", "Pisces"}  # same five as the old daily series


def test_hindi_rows():
    rows = w.weekly_rows(dt.date(2026, 10, 11), "hi")
    assert rows[0]["name"] == "मेष" and rows[0]["mantra"].startswith("ॐ")
