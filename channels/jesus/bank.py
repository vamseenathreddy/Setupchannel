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


SUBSCRIBE_EN = "Subscribe for daily Bible quotes and quiz"
SUBSCRIBE_TE = "రోజూ బైబిల్ వచనం, క్విజ్ కోసం సబ్‌స్క్రైబ్ చేయండి"


def quote_row(v: dict) -> dict:
    return {
        "id": v["id"], "category": "quote", "special": "", "source": v["ref_en"],
        "text_primary": f"{v['text_en']} - {v['ref_en']}",
        "text_secondary": f"{v['text_te']} - {v['ref_te']}",
        "apply_en": v["apply_en"], "apply_te": v["apply_te"],
        "ref_en": v["ref_en"], "ref_te": v["ref_te"], "verse_en": v["text_en"], "verse_te": v["text_te"],
        "theme": v.get("theme", ""),
        "sub_en": "Comment your thoughts on this video!\n" + SUBSCRIBE_EN,
        "sub_te": "ఈ వీడియోపై మీ అభిప్రాయాన్ని కామెంట్ చేయండి!\n" + SUBSCRIBE_TE,
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
        "sub_en": "Comment your answer!\n" + SUBSCRIBE_EN, "sub_te": "మీ సమాధానం కామెంట్ చేయండి!\n" + SUBSCRIBE_TE,
        "answer": v["ref_en"], "answer_te": v["ref_te"], "ref_en": v["ref_en"], "ref_te": v["ref_te"],
        "theme": v.get("theme", ""),
    }
    for letter, opt in zip(letters, options):
        row[f"opt_{letter.lower()}"] = f"{letter}) {opt}"
    row["opts_ab"] = f"{row['opt_a']}     {row['opt_b']}"
    row["opts_cd"] = f"{row['opt_c']}     {row['opt_d']}"
    row["correct_letter"] = letters[options.index(v["ref_en"])]
    return row


TRIVIA = Path(__file__).resolve().parent / "data" / "quiz_bank.json"


def load_trivia() -> list[dict]:
    return json.loads(TRIVIA.read_text(encoding="utf-8"))["questions"]


def next_trivia(used_ids) -> dict:
    qs = load_trivia()
    for q in qs:
        if q["id"] not in used_ids:
            return q
    return qs[len(used_ids) % len(qs)]


def trivia_row(q: dict) -> dict:
    """Real Bible question (who/what/how many) with 4 English options; stable shuffle per id."""
    opts = list(q["options"])
    random.Random(q["id"]).shuffle(opts)
    letters = "ABCD"
    row = {
        "id": q["id"], "category": "quiz", "special": "", "source": q["ref_en"],
        "quiz_label": "BIBLE QUIZ",
        "question_en": q["q_en"], "question_te": q["q_te"],
        "text_primary": q["q_en"], "text_secondary": q["q_te"],
        "answer": q["answer"], "answer_te": q["answer_te"], "ref_en": q["ref_en"], "ref_te": q["ref_te"],
        "sub_en": "Comment your answer!", "sub_te": "మీ సమాధానం కామెంట్ చేయండి!",
        "theme": "",
    }
    for letter, opt in zip(letters, opts):
        row[f"opt_{letter.lower()}"] = f"{letter}) {opt}"
    row["correct_letter"] = letters[opts.index(q["answer"])]
    return row


PLAYLISTS = Path(__file__).resolve().parent / "data" / "playlists.json"


def playlist_id(kind: str, configured: str | None) -> str | None:
    """Configured (env/secret) playlist id wins; else the committed channels/jesus/data/playlists.json
    ({"quotes": "PL...", "quiz": "PL..."}); else None (video simply isn't added to a playlist)."""
    if configured:
        return configured
    if PLAYLISTS.exists():
        return json.loads(PLAYLISTS.read_text(encoding="utf-8")).get(kind) or None
    return None
