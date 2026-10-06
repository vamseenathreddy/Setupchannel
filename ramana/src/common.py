"""Shared helpers: content bank IO, special days, duplicate detection."""
import csv
import os
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "content.csv"
SPECIAL = ROOT / "data" / "special_days.csv"
FIELDS = ["id", "category", "telugu", "english", "source", "verified", "special", "used", "scheduled_for"]
CATEGORIES = ("quote", "qa", "life")
ID_PREFIX = {"quote": "q", "qa": "a", "life": "l"}


def load_rows():
    with open(CONTENT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(rows):
    """Atomic write so a crash never leaves a half written content bank."""
    fd, tmp = tempfile.mkstemp(dir=CONTENT.parent, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, CONTENT)


def load_specials():
    out = []
    with open(SPECIAL, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines):
        out.append({k: (v or "").strip() for k, v in r.items()})
    return out


def special_for(date):
    """Return the special day dict for a datetime.date, or None. Full dates win over MM-DD."""
    full, short = date.strftime("%Y-%m-%d"), date.strftime("%m-%d")
    specials = load_specials()
    for key in (full, short):
        for s in specials:
            if s["date"] == key:
                return s
    return None


def norm(text):
    return re.sub(r"[^a-z0-9ఀ-౿ ]", "", text.lower()).strip()


def is_duplicate(new_row, rows, en_threshold=0.80, te_threshold=0.85):
    """Exact or near duplicate against every row ever stored (used or not)."""
    en, te = norm(new_row["english"]), norm(new_row["telugu"])
    for r in rows:
        if en and SequenceMatcher(None, en, norm(r["english"])).ratio() >= en_threshold:
            return True
        if te and SequenceMatcher(None, te, norm(r["telugu"])).ratio() >= te_threshold:
            return True
    return False


def unused_pool(rows):
    return [r for r in rows if not r["special"] and not r["used"]]
