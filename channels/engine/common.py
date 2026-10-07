"""Shared content-bank IO for every "Pattern A" static-content-bank channel in this repo
(Jesus Worship Waves, InfoShorts Telugu, Divine Mantra Sangam, Devotional Trance Beats --
and Ramana Maharshi TV could migrate to this shared engine later, though it currently keeps
its own copy of this logic under ramana/src/ since it shipped first and works).

Row schema (content.csv), same for every channel using this engine:
  id, category, text_primary, text_secondary, source, special, used, scheduled_for

text_primary is whatever goes TOP/BIG on the Short; text_secondary goes below, smaller (or is
left blank for a channel that is intentionally one language only, e.g. the two Hindi-only
channels). Which language is "primary" is a per-channel choice (see each channel's
render_config.py) -- this file never assumes a specific language.

Unlike ramana/src/common.py (which hardcodes its own data/content.csv path), every function
here takes the content/special CSV paths explicitly, since this module is shared by several
channels with different content banks.
"""
import csv
import os
import tempfile
from pathlib import Path

FIELDS = ["id", "category", "text_primary", "text_secondary", "source", "special", "used", "scheduled_for"]


def load_rows(content_csv: Path):
    with open(content_csv, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(rows, content_csv: Path):
    """Atomic write so a crash never leaves a half written content bank."""
    content_csv = Path(content_csv)
    fd, tmp = tempfile.mkstemp(dir=content_csv.parent, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, content_csv)


def load_specials(special_csv: Path | None):
    if not special_csv or not Path(special_csv).exists():
        return []
    out = []
    with open(special_csv, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        return out
    for r in csv.DictReader(lines):
        out.append({k: (v or "").strip() for k, v in r.items()})
    return out


def special_for(date, special_csv: Path | None):
    """Return the special day dict for a datetime.date, or None. Full dates win over MM-DD."""
    full, short = date.strftime("%Y-%m-%d"), date.strftime("%m-%d")
    specials = load_specials(special_csv)
    for key in (full, short):
        for s in specials:
            if s["date"] == key:
                return s
    return None


def unused_pool(rows, used_ids):
    return [r for r in rows if not r["special"] and r["id"] not in set(used_ids)]
