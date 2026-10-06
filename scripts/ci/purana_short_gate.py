#!/usr/bin/env python3
"""
CI gate for the Purana Story Short's daily posting window.

WHY THIS EXISTS: per explicit request (2026-10-02), this series should
post once a day, directly public, at a TIME THAT VARIES DAY TO DAY
within a 5:00-6:00 PM IST window -- "not fixed time everyday" (the same
bot-detection concern already raised for the night alert Shorts, and
the same answer: a visible pattern of posting at the exact same minute
every single day is what a cron: trigger alone would produce, so the
randomness has to live here, in a gate that many calls pass through,
not in the trigger itself).

HOW THE RANDOM TIME IS CHOSEN: deterministic per calendar day --
random.Random(seeded by today's date ordinal).uniform(0, 59) minutes
past 5:00 PM IST. Deterministic (not re-rolled on every tick) so
repeated gate checks on the same day agree on the same target time,
but different FROM DAY TO DAY since the seed changes daily -- the same
reasoning already used elsewhere in this repo for non-repeating
rotation (content/purana_selector.py, images/selector.py), just applied
to a time-of-day instead of a content choice.

HOW IT'S DRIVEN: the external cron-job.org trigger (same pattern as the
night alert Shorts' watchdog) calls this workflow's workflow_dispatch
endpoint repeatedly through the window (e.g. every 15 minutes, 17:00-
17:55 IST) rather than once at a fixed minute -- this gate decides, on
each call, whether TODAY's randomly chosen target minute has been
reached yet, and whether today's post has already gone out (the
"last_run_date_purana_short.txt" marker, synced from Drive, same
pattern as the alert Shorts' per-Short markers). A call before the
target minute, or after today's post is already done, is a safe no-op.

MANUAL OVERRIDE: workflow_dispatch can set BYPASS_GATE=true (via the
workflow's `bypass_gate` input) to post immediately regardless of the
time window and today's marker -- for manual testing/review runs from
the Actions UI. Never set by the recurring cron-job.org calls
themselves.

Prints exactly one of: post | none
and, if running under GitHub Actions, also writes it as `target=...` to
$GITHUB_OUTPUT for the workflow's `if:` conditions to use.
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DATA_DIR = Path("data")
WINDOW_START_HOUR = 17  # 5:00 PM IST
# The cron-job.org watchdog now ticks every 15 minutes through the window (5:00, 5:15, 5:30,
# 5:45, 5:55 PM IST) instead of every 5 minutes, to cut billed GitHub Actions minutes on this
# private repo. The random target must land no later than the second-to-last tick (5:50 leaves
# the 5:55 tick as a guaranteed catch before the 6:00 PM cutoff) -- same fix already applied to
# gita_sloka_gate.py after its 2026-10-06 missed post.
WINDOW_SPAN_MINUTES = 50  # target lands somewhere in 5:00-5:50 PM, posting completes before 6 PM


def _already_posted_today(today: str) -> bool:
    marker = DATA_DIR / "last_run_date_purana_short.txt"
    return marker.exists() and marker.read_text().strip() == today


def _todays_target_time(today_ordinal: int) -> dt_time:
    offset_minutes = random.Random(today_ordinal).uniform(0, WINDOW_SPAN_MINUTES)
    total_minutes = WINDOW_START_HOUR * 60 + offset_minutes
    return dt_time(int(total_minutes // 60), int(total_minutes % 60))


def _decide(now: datetime, bypass_gate: bool) -> tuple[str, dt_time]:
    today = now.date().isoformat()
    target = _todays_target_time(now.date().toordinal())

    if bypass_gate:
        return "post", target

    if _already_posted_today(today):
        return "none", target

    if now.time() < target:
        return "none", target

    # Window safety cap: if something delayed every tick past 6 PM,
    # skip rather than post very late -- same "a very late post reads
    # worse than a missed one" principle already applied to the alert
    # Shorts' 3 AM window close.
    if now.time() >= dt_time(18, 0):
        return "none", target

    return "post", target


def main() -> int:
    now = datetime.now(IST)
    bypass_gate = os.environ.get("BYPASS_GATE", "").strip().lower() == "true"
    decision, todays_target_time = _decide(now, bypass_gate)

    print(decision)
    print(
        f"[purana-short-gate] now_ist={now.isoformat()} todays_target={todays_target_time.isoformat()} "
        f"bypass_gate={bypass_gate} -> decision={decision}",
        file=sys.stderr,
    )

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(f"target={decision}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
