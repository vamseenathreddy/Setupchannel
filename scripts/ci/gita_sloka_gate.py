#!/usr/bin/env python3
"""
CI gate for the Bhagavad Gita Sloka Short's daily posting window.

Same randomized-daily-target-time design as purana_short_gate.py /
purana_concept_gate.py, applied to a third window: 3-4 PM IST, per
explicit request (2026-10-02: "shorts card at 3 to 4 pm daily").

HOW IT'S DRIVEN: an external cron-job.org watchdog calls this
workflow's workflow_dispatch endpoint repeatedly through the window
(e.g. every 5 minutes, 3:00-3:55 PM IST) -- this gate decides, on each
call, whether today's randomly-chosen target minute (somewhere in the
full 3:00-3:59 PM range) has been reached yet, and whether today's post
has already gone out (the "last_run_date_gita_sloka.txt" marker, synced
from Drive).

MANUAL OVERRIDE: workflow_dispatch can set BYPASS_GATE=true to post
immediately regardless of the time window and today's marker -- for
manual testing/review runs only.

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
WINDOW_START_HOUR = 15  # 3:00 PM IST
WINDOW_SPAN_MINUTES = 59  # target lands somewhere in 3:00-3:59 PM, posting completes before 4 PM


def _already_posted_today(today: str) -> bool:
    marker = DATA_DIR / "last_run_date_gita_sloka.txt"
    return marker.exists() and marker.read_text().strip() == today


def _todays_target_time(today_ordinal: int) -> dt_time:
    # A distinct salt (x3+2) from the other two gates' seeds, same
    # reasoning as purana_concept_gate.py's salt -- avoids all three
    # windows' randomly-chosen minutes correlating day to day purely by
    # coincidence of sharing the same bare date-ordinal seed.
    offset_minutes = random.Random(today_ordinal * 3 + 2).uniform(0, WINDOW_SPAN_MINUTES)
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

    if now.time() >= dt_time(16, 0):
        return "none", target

    return "post", target


def main() -> int:
    now = datetime.now(IST)
    bypass_gate = os.environ.get("BYPASS_GATE", "").strip().lower() == "true"
    decision, todays_target_time = _decide(now, bypass_gate)

    print(decision)
    print(
        f"[gita-sloka-gate] now_ist={now.isoformat()} todays_target={todays_target_time.isoformat()} "
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
