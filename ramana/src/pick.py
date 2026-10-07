"""Deterministic content choice. The same date and the same state always give the same row,
so re-running a day can never pick something different or repeat an item."""
import datetime as dt
import random

ROTATION = {0: "quote", 1: "qa", 2: "life", 3: "quote", 4: "qa", 5: "life", 6: "quote"}  # Mon..Sun
WARMUP_DAYS = 14                      # the first Shorts avoid death related rows
SENSITIVE = ("death", "mahasamadhi", "passed away", "died")
LOW_STOCK = 7


def unused_pool(rows, used_ids):
    return [r for r in rows if not r["special"] and r["id"] not in set(used_ids)]


def choose_row(rows, date: dt.date, used_ids, slot=None):
    """Return (row, reason). Special day rows win, then the weekday rotation, then any unused row."""
    key_full, key_short = date.strftime("%Y-%m-%d"), date.strftime("%m-%d")
    for r in rows:  # special days are posted once a day, by the first (quote) slot only
        if slot in (None, "quote") and r["special"] in (key_full, key_short):
            return r, "special-day"
    pool = unused_pool(rows, used_ids)
    if len(used_ids) < WARMUP_DAYS:
        pool = [r for r in pool if not any(w in r["english"].lower() for w in SENSITIVE)] or pool
    if not pool:
        return None, "empty"
    want = slot or ROTATION[date.weekday()]
    cat_pool = [r for r in pool if r["category"] == want]
    reason = f"rotation:{want}" if cat_pool else "fallback"
    cat_pool = sorted(cat_pool or pool, key=lambda r: r["id"])
    return random.Random(date.toordinal()).choice(cat_pool), reason


def low_stock(rows, used_ids):
    return len(unused_pool(rows, used_ids)) < LOW_STOCK
