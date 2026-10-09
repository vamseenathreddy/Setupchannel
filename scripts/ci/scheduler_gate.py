#!/usr/bin/env python3
"""
CI gate for the hourly "Daily Shorts Post" tick.

Runs on EVERY hourly tick (all 24 hours a day) as a cheap,
dependency-free first step, before any heavy pip installs. Decides
whether THIS tick should post one of the two Alert Shorts, and if so,
which one.

WHY HOURLY, ALL DAY, INSTEAD OF ONE PRECISE-TIME CRON: GitHub's own
docs say schedule: events are best-effort and can simply not fire
during high platform load, with no SLA -- confirmed for real across
several nights where a single once-a-night cron silently never fired
at all. Ticking every hour gives many independent chances instead of
one, and because each Short has its own "already posted today" marker
(read below, synced from Drive by the step before this one), a tick
that gets dropped just means the next tick tries again -- nothing is
silently lost the way a single missed fire used to be.

RULES (explicit product decision, not just an engineering default):
  - NEVER fire before 12:00 AM IST. Firing early would fetch and post
    TODAY's Panchang under what is meant to be the next day's post --
    i.e. it would show yesterday's timings in a Short dated today.
  - Only fire inside the 12:00 AM - 3:00 AM IST window. Three hourly
    ticks land inside it (12:00 AM, 1:00 AM, 2:00 AM IST), giving Rahu
    Kalam, Shubha Ghadiyalu, and Durmuhurtham their own separate tick
    each -- resilient to a single missed tick instead of depending on
    exactly one cron fire succeeding. Extended from the original
    12:00-2:00 AM / two-Short window when Durmuhurtham was added as a
    third standalone alert Short (2026-09-30) -- real channel analytics
    showed a standalone "avoid this time" Durmuhurtham video as one of
    the channel's best performers, previously only shown as small
    secondary text on the Rahu Kalam card.
  - Posting order: Rahu Kalam first, then Shubha Ghadiyalu once Rahu
    Kalam's marker for today is set, then Durmuhurtham once both of
    those are set.
  - If the window closes (3:00 AM IST) with any Short(s) still
    unposted, that day's post for the still-missing Short(s) is
    skipped entirely rather than firing late in the afternoon --
    intentional per explicit product decision: a very late post reads
    worse than a missed one for Panchang/muhurtam content.

MANUAL OVERRIDE: workflow_dispatch can set FORCE_TARGET (via the
workflow's `force_target` input) to "rahu_kalam", "shubha_ghadiyalu",
"durmuhurtham", or "both" (rahu_kalam + shubha_ghadiyalu only, kept for
backward compatibility -- durmuhurtham must be requested explicitly by
name) to fire immediately regardless of the time-of-day window and
today's markers -- e.g. for testing or a deliberate manual re-post.
Never set by the scheduled ticks themselves.

Prints exactly one of: none | rahu_kalam | shubha_ghadiyalu |
durmuhurtham | both
and, if running under GitHub Actions, also writes it as `target=...`
to $GITHUB_OUTPUT for the workflow's `if:` conditions to use.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DATA_DIR = Path("data")
WINDOW_START = dt_time(0, 0)  # 12:00 AM IST -- never fire before this
WINDOW_END = dt_time(3, 0)  # 3:00 AM IST -- exclusive upper bound (extended for the 3rd Short, Durmuhurtham)


def _posted_today(which: str, today: str) -> bool:
    marker = DATA_DIR / f"last_run_date_{which}.txt"
    return marker.exists() and marker.read_text().strip() == today


def _decide(now: datetime, force_target: str) -> str:
    today = now.date().isoformat()

    if force_target in ("rahu_kalam", "shubha_ghadiyalu", "durmuhurtham", "both"):
        return force_target

    if not (WINDOW_START <= now.time() < WINDOW_END):
        return "none"

    # Each Short owns its own hour (Rahu 12-1 AM, Shubh 1-2 AM, Durm 2-3 AM IST). A tick never
    # posts a later Short early, so extra pings inside the 12-1 AM hour cannot burn the others.
    h = now.hour  # 0, 1 or 2 inside the window
    for w in ("rahu_kalam", "shubha_ghadiyalu", "durmuhurtham")[:h + 1]:  # earlier misses catch up first
        if not _posted_today(w, today):
            return w
    return "none"


def main() -> int:
    now = datetime.now(IST)
    force_target = os.environ.get("FORCE_TARGET", "").strip()
    target = _decide(now, force_target)

    print(target)
    in_window = WINDOW_START <= now.time() < WINDOW_END
    print(f"[scheduler-gate] now_ist={now.isoformat()} in_window={in_window} "
          f"force_target={force_target or '(none)'} -> target={target}", file=sys.stderr)

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(f"target={target}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
