"""Deterministic content choice, shared by every Pattern-A channel (see common.py's module
docstring). The same date and the same used_ids always give the same row, so re-running a day
can never pick something different or repeat an item.

Generalized from ramana/src/pick.py: ROTATION (which category each weekday prefers) and
WARMUP_DAYS/SENSITIVE are passed in per channel instead of being hardcoded to Ramana's own
quote/qa/life categories, since every channel's category set differs.
"""
import datetime as dt
import random

LOW_STOCK = 7


def unused_pool(rows, used_ids):
    return [r for r in rows if not r["special"] and r["id"] not in set(used_ids)]


def choose_row(rows, date: dt.date, used_ids, rotation: dict[int, str], sensitive_words=(), warmup_days=0):
    """Return (row, reason). Special day rows win, then the weekday rotation, then any unused row.

    rotation: {0: "category_a", 1: "category_b", ...} Mon..Sun, same shape as ramana's ROTATION.
    sensitive_words/warmup_days: optional -- if given, the first `warmup_days` posts (by
    used_ids count) avoid rows whose text_primary/text_secondary contain any sensitive word
    (case-insensitive), same safety behavior as ramana's WARMUP_DAYS/SENSITIVE.
    """
    key_full, key_short = date.strftime("%Y-%m-%d"), date.strftime("%m-%d")
    for r in rows:
        if r["special"] in (key_full, key_short):
            return r, "special-day"
    pool = unused_pool(rows, used_ids)
    if sensitive_words and len(used_ids) < warmup_days:
        def _has_sensitive(r):
            text = f"{r.get('text_primary', '')} {r.get('text_secondary', '')}".lower()
            return any(w in text for w in sensitive_words)
        pool = [r for r in pool if not _has_sensitive(r)] or pool
    if not pool:
        return None, "empty"
    want = rotation.get(date.weekday())
    cat_pool = [r for r in pool if r["category"] == want] if want else []
    reason = f"rotation:{want}" if cat_pool else "fallback"
    cat_pool = sorted(cat_pool or pool, key=lambda r: r["id"])
    return random.Random(date.toordinal()).choice(cat_pool), reason


def low_stock(rows, used_ids):
    return len(unused_pool(rows, used_ids)) < LOW_STOCK
