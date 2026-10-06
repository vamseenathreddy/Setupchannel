#!/usr/bin/env python3
"""
CI gate for the Purana Concept Short's daily posting window.

Same design as purana_short_gate.py (see that script's docstring for the
full rationale -- randomized daily target time within a window, to avoid
the bot-detection-flavored "exact same minute every day" pattern a bare
cron: trigger would produce), applied to a different, wider window: 11
AM-1 PM IST (a 2-hour span), per explicit request (2026-10-02: "rotate
above 6 concepts daily from all 18 puranas in another short between 11
am to 1 pm").

HOW IT'S DRIVEN: an external cron-job.org watchdog calls this workflow's
workflow_dispatch endpoint repeatedly through the window (e.g. every 15
minutes, 11:00 AM-12:55 PM IST) -- this gate decides, on each call,
whether today's randomly-chosen target minute (somewhere in the full
11:00 AM-12:50 PM range) has been reached yet, and whether today's post
has already gone out (the "last_run_date_purana_concept.txt" marker,
synced from Drive).

MANUAL OVERRIDE: workflow_dispatch can set BYPASS_GATE=true (via the
workflow's `bypass_gate` input) to post immediately regardless of the
time window and today's marker -- for manual testing/review runs only.

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
WINDOW_START_HOUR = 11  # 11:00 AM IST
# The cron-job.org watchdog now ticks every 15 minutes through the window (11:00, 11:15, ...,
# 12:45, 12:55 IST) instead of every 5 minutes, to cut billed GitHub Actions minutes on this
# private repo. The random target must land no later than the second-to-last tick (12:50 leaves
# the 12:55 tick as a guaranteed catch before the 1:00 PM cutoff) -- same fix already applied to
# gita_sloka_gate.py after its 2026-10-06 missed post.
WINDOW_SPAN_MINUTES = 110  # target lands somewhere in 11:00 AM-12:50 PM, posting completes before 1 PM


def _already_posted_today(today: str) -> bool:
    marker = DATA_DIR / "last_run_date_purana_concept.txt"
    return marker.exists() and marker.read_text().strip() == today


def _todays_target_time(today_ordinal: int) -> dt_time:
    # A distinct salt from purana_short_gate.py's seed so the two series'
    # randomly-chosen minutes-past-the-hour don't correlate day to day
    # (not a security concern, just avoids both windows' targets always
    # landing at, say, "the 23rd minute" together by coincidence of
    # using the same bare date ordinal as the seed).
    offset_minutes = random.Random(today_ordinal * 2 + 1).uniform(0, WINDOW_SPAN_MINUTES)
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

    # Window safety cap: a very late post reads worse than a missed one
    # -- same principle already applied to the other gated Shorts.
    if now.time() >= dt_time(13, 0):
        return "none", target

    return "post", target


def main() -> int:
    now = datetime.now(IST)
    bypass_gate = os.environ.get("BYPASS_GATE", "").strip().lower() == "true"
    decision, todays_target_time = _decide(now, bypass_gate)

    print(decision)
    print(
        f"[purana-concept-gate] now_ist={now.isoformat()} todays_target={todays_target_time.isoformat()} "
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
