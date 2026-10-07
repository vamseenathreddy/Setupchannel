"""Verse bank for Jesus Worship Waves and the row builders for its two daily Shorts.

data/verses.json holds the verses (one per day, bank order, never repeated). The morning
Quote Short and the evening Quiz Short are built from the SAME verse: the quiz row is derived
from whatever verse the morning Short posted today (read from the quote state file).
"""
import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "verses.json"


def load_verses() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))["verses"]


def next_unused(used_ids) -> dict | None:
    for v in load_verses():
        if v["id"] not in used_ids:
            return v
    return None


def by_id(verse_id: str) -> dict | None:
    return next((v for v in load_verses() if v["id"] == verse_id), None)


def quote_row(v: dict) -> dict:
    return {
        "id": v["id"], "category": "quote", "special": "", "source": v["ref_en"],
        "text_primary": f"{v['text_en']} - {v['ref_en']}",
        "text_secondary": f"{v['text_te']} - {v['ref_te']}",
        "apply_en": v["apply_en"], "apply_te": v["apply_te"],
        "ref_en": v["ref_en"], "ref_te": v["ref_te"], "verse_en": v["text_en"], "verse_te": v["text_te"],
        "theme": v.get("theme", ""),
    }


def quiz_row(v: dict) -> dict:
    """4 options: the true reference plus 3 other real references from the bank (stable shuffle
    seeded by the verse id so a re-render gives the same card)."""
    rng = random.Random(v["id"])
    others = [x["ref_en"] for x in load_verses() if x["id"] != v["id"]]
    options = rng.sample(others, 3) + [v["ref_en"]]
    rng.shuffle(options)
    letters = "ABCD"
    row = {
        "id": v["id"], "category": "quiz", "special": "", "source": v["ref_en"],
        "quiz_label": "BIBLE QUIZ",
        "text_primary": v["text_en"], "text_secondary": v["text_te"],
        "question_en": "Which book and chapter is this verse from?",
        "question_te": "ఈ వచనం ఏ పుస్తకం, ఏ అధ్యాయంలోనిది?",
        "cta_en": "Comment your answer! See this morning's Short.",
        "cta_te": "మీ సమాధానం కామెంట్ చేయండి!",
        "answer": v["ref_en"], "answer_te": v["ref_te"], "ref_en": v["ref_en"], "ref_te": v["ref_te"],
        "theme": v.get("theme", ""),
    }
    for letter, opt in zip(letters, options):
        row[f"opt_{letter.lower()}"] = f"{letter}) {opt}"
    row["opts_ab"] = f"{row['opt_a']}     {row['opt_b']}"
    row["opts_cd"] = f"{row['opt_c']}     {row['opt_d']}"
    row["correct_letter"] = letters[options.index(v["ref_en"])]
    return row
