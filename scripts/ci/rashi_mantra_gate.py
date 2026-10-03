#!/usr/bin/env python3
"""
CI gate for the Rashi Mantra Short's daily posting window.

WHY THIS EXISTS: same pattern as purana_short_gate.py and
purana_concept_gate.py -- the Rashi Mantra series started as a
manual-test-only workflow (no gate at all) and is being moved
(2026-10-03) to a recurring daily post, once a day, at a TIME THAT
VARIES DAY TO DAY within an 8:00-9:00 AM IST window, for the same
anti-bot-pattern reason already applied to every other series in this
repo: posting at the exact same minute every day is a visible,
fixed-cron signature; the randomness has to live in a gate that many
calls pass through, not in the trigger itself.

HOW THE RANDOM TIME IS CHOSEN: deterministic per calendar day --
random.Random(seeded by today's date ordinal).uniform(0, 59) minutes
past 8:00 AM IST. Deterministic so repeated gate checks on the same day
agree on the same target time, but different from day to day since the
seed changes daily.

HOW IT'S DRIVEN: an external cron-job.org watchdog (same pattern as the
other series) calls this workflow's workflow_dispatch endpoint
repeatedly through the window (e.g. every 5 minutes, 08:00-08:55 IST)
-- this gate decides, on each call, whether today's randomly chosen
target minute has been reached yet, and whether today's post has
already gone out (the "last_run_date_rashi_mantra.txt" marker, synced
from Drive -- see drive_state_sync.py's module docstring: this is a
NEW marker file that must be pre-created once in the Drive folder by a
real Google account before this gate's first real run, same as every
other series' marker file was).

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
WINDOW_START_HOUR = 8  # 8:00 AM IST
WINDOW_SPAN_MINUTES = 59  # target lands somewhere in 8:00-8:59 AM, posting completes before 9 AM


def _already_posted_today(today: str) -> bool:
    marker = DATA_DIR / "last_run_date_rashi_mantra.txt"
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

    # Window safety cap: if something delayed every tick past 9 AM,
    # skip rather than post very late -- same principle already
    # applied to the other gated series.
    if now.time() >= dt_time(9, 0):
        return "none", target

    return "post", target


def main() -> int:
    now = datetime.now(IST)
    bypass_gate = os.environ.get("BYPASS_GATE", "").strip().lower() == "true"
    decision, todays_target_time = _decide(now, bypass_gate)

    print(decision)
    print(
        f"[rashi-mantra-gate] now_ist={now.isoformat()} todays_target={todays_target_time.isoformat()} "
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
