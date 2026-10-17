"""Standing rule (2026-10-08): every YouTube title mixes English with the channel's own language
(Telugu or Hindi). Never pure Telugu / pure Hindi."""
import ast
import glob
import re

import pytest

FILES = (glob.glob("src/mahanavi/content/*.py") + glob.glob("channels/*/metadata.py")
         + glob.glob("channels/*/channel_config.py") + ["ramana/src/metadata.py"])


def _title_lists():
    for f in FILES:
        tree = ast.parse(open(f, encoding="utf-8").read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Tuple)):
                names = [t.id for t in n.targets if isinstance(t, ast.Name)]
                if any("TITLE" in x.upper() for x in names):
                    for e in n.value.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            yield f, names[0], e.value


@pytest.mark.parametrize("f,name,title", list(_title_lists()))
def test_title_has_english_word(f, name, title):
    assert re.search(r"[A-Za-z]{3,}", re.sub(r"\{[^}]*\}", "", title)), f"{f}:{name}: {title!r} has no English word"


def test_dated_titles_are_unique_per_day_and_carry_date_and_tithi():
    from datetime import date, timedelta

    from mahanavi.content.alert_seo import dated_title

    start = date(2026, 10, 17)
    for kind in ("rahu_kalam", "shubha_ghadiyalu", "durmuhurtham"):
        titles = {dated_title(kind, start + timedelta(days=i), "Shukla Saptami", (start + timedelta(days=i)).toordinal())
                  for i in range(120)}
        assert len(titles) == 120  # no repeat across 120 days
        t = dated_title(kind, start, "Shukla Saptami", start.toordinal())
        assert "అక్టోబర్" in t and "శుద్ధ సప్తమి" in t and len(t) <= 100


def test_special_tithi_leads_the_title():
    from datetime import date

    from mahanavi.content.alert_seo import dated_title

    d = date(2026, 10, 20)
    assert dated_title("rahu_kalam", d, "Shukla Ekadashi", d.toordinal()).startswith("శుద్ధ ఏకాదశి")
    assert dated_title("durmuhurtham", d, "Amavasya", d.toordinal()).startswith("అమావాస్య")


def test_mantra_sangam_dated_titles_unique_and_carry_tithi():
    import datetime as dt

    from channels.mantra_sangam import metadata_timings as m

    start = dt.date(2026, 10, 17)
    for kind in ("rahu", "shubh", "durm"):
        titles = set()
        for i in range(60):
            d = start + dt.timedelta(days=i)
            row = {"category": kind, "date_iso": d.isoformat(), "tithi_hi": "शुक्ल सप्तमी", "tithi_special": False}
            t = m.title(row)
            assert len(t) <= 100 and "शुक्ल सप्तमी" in t
            titles.add(t)
        assert len(titles) == 60
    special = m.title({"category": "rahu", "date_iso": "2026-10-22", "tithi_hi": "शुक्ल एकादशी", "tithi_special": True})
    assert special.startswith("शुक्ल एकादशी")
