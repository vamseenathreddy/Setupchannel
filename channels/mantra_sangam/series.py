"""Hindi bank series for Channel B: Purana stories (70) and Rashi mantras (12).

Hindi version of Channel A's Purana and Rashi Mantra Shorts. Content is a static CSV; each day's
row is the first one not yet in used_ids (the list restarts when every row has been used).
Titles mix Hindi with the English name of the main word, e.g. "गजेंद्र मोक्ष (Gajendra Moksham)".
"""
from ytcore.brandcfg import B_NAME  # noqa: E402
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
CHANNEL = f"{B_NAME}"
OPINION = "इस वीडियो पर अपनी राय कमेंट करें"
SUB = {"purana": "रोज़ एक पुराण कथा के लिए सब्सक्राइब करें", "rashi": "रोज़ राशि मंत्र के लिए सब्सक्राइब करें"}
CSV = {"purana": DATA / "purana.csv", "rashi": DATA / "rashi.csv"}


def _rows(kind):
    with open(CSV[kind], encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_row(kind, r):
    base = {"id": r["id"], "category": kind, "special": "", "text_primary": "", "text_secondary": "",
            "t_comment": "", "t_sub": SUB[kind], "t_opinion": OPINION}
    if kind == "purana":
        base.update(source="Puranas (retold)", t_label="पुराण कथा", t_title=r["title_hi"], t_story=r["story_hi"],
                    t_moral=r["moral_hi"], t_invoke=r.get("invocation_hi", ""), title_hi=r["title_hi"],
                    title_en=r["title_en"], moral_en=r["moral_en"], purana_hi=r["purana_hi"], purana_en=r["purana_en"])
    else:
        base.update(source="Navagraha mantras", t_label="राशि मंत्र", t_title=f"{r['name_hi']} राशि",
                    t_story=f"स्वामी ग्रह: {r['planet_hi']}\n{r['benefit_hi']}", t_moral=r["mantra_hi"],
                    t_invoke=f"जप: {r['count_hi']}", title_hi=r["name_hi"], title_en=r["name_en"],
                    planet_en=r["planet_en"], planet_hi=r["planet_hi"], benefit_hi=r["benefit_hi"])
    return base


def fetch_row_for(kind):
    def fetch(used_ids):
        rows = _rows(kind)
        pool = [r for r in rows if r["id"] not in used_ids]
        return to_row(kind, pool[0] if pool else rows[len(used_ids) % len(rows)])
    return fetch
