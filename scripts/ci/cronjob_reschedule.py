#!/usr/bin/env python3
"""
Daily orchestrator that re-schedules cron-job.org's gated-series jobs
to fire at TODAY's precise, randomly-chosen target time instead of
ticking repeatedly through a wide window.

WHY THIS EXISTS: rashi_mantra_gate.py / purana_concept_gate.py /
gita_sloka_gate.py / purana_short_gate.py / ramana_gate.py each compute
a date-seeded "today's target minute" and rely on cron-job.org pinging
the workflow repeatedly (every 15 min as of 2026-10-06, every 5 min for
Ramana's own suggested setup) through the whole window so SOME tick
lands at-or-after that target before the window's hard cutoff. Most of
those ticks are wasted no-ops (each still costs 1 billed GitHub Actions
minute on this private repo).

Ramana Maharshi TV (ramana/, added 2026-10) was folded in as a 5th
entry here rather than standing up its own separate cron-job.org
pinger (its own .github/workflows/post_ramana.yml -- not used verbatim
in this repo -- suggested 12 pings/day on its own, ~6 Actions minutes/
day, the exact same "repeated ping" cost this orchestrator exists to
eliminate for the other 4 series). Its target-time formula is NOT the
same shape as the other 4 (sha256-hash-based, not
random.Random(seed).uniform(...) -- see ramana/scripts/ci/ramana_gate.py's
target_time()), so it uses the "custom" override below instead of
start_hour/span/seed_fn.

This script runs once a day, very early (before any window opens),
computes the SAME target time each gate script would compute for
today (identical seed/formula -- see SERIES below, copied from the
gate scripts), and uses the cron-job.org REST API to reschedule each
job to fire only at [target, safety-net-near-cutoff] today -- 2
pings/day/series instead of 5-9. The gate scripts themselves are NOT
changed: they still do the real "post vs none" decision, so if this
orchestrator's precise ping is somehow missed, the safety-net ping
(scheduled a few minutes before each gate's hard cutoff) still has a
chance to catch it -- same safety principle already used throughout
this repo, just applied one level up.

If THIS script fails to run on a given day (its own single daily
GitHub-native schedule tick is itself best-effort, same caveat GitHub
documents for any `schedule:` trigger), cron-job.org simply keeps
yesterday's schedule for that job until the next successful run resets
it -- a graceful degradation (one day's post happens at a predictable
time) rather than a missed post.

Requires CRONJOB_ORG_API_KEY (a cron-job.org API key, Account ->
Settings -> API Keys) as an environment variable / GitHub secret.
NEVER commit the raw key to this repo -- it must live only in GitHub
Actions secrets.

Usage: python3 scripts/ci/cronjob_reschedule.py [--dry-run]
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
API_BASE = "https://api.cron-job.org"

# One entry per cron-job.org-driven gated series. start_hour/span/seed_fn
# are copied verbatim from each series' scripts/ci/*_gate.py so this
# orchestrator computes EXACTLY the same target the gate would compute
# for today. safety_hour/safety_minute is a second, fixed ping placed a
# few minutes before that gate's hard cutoff, as a fallback.
SERIES = {
    "rashi_mantra": {
        "url_fragment": "post-rashi-mantra.yml",
        "start_hour": 8,
        "span": 50,
        "seed_fn": lambda o: o,
        "safety_hour": 8,
        "safety_minute": 55,
    },
    "purana_concept": {
        "url_fragment": "post-concept-short.yml",
        "start_hour": 11,
        "span": 110,
        "seed_fn": lambda o: o * 2 + 1,
        "safety_hour": 12,
        "safety_minute": 55,
    },
    "gita_sloka": {
        "url_fragment": "post-gita-sloka.yml",
        "start_hour": 15,
        "span": 50,
        "seed_fn": lambda o: o * 3 + 2,
        "safety_hour": 15,
        "safety_minute": 55,
    },
    "purana_story": {
        "url_fragment": "post-purana-short.yml",
        "start_hour": 17,
        "span": 50,
        "seed_fn": lambda o: o,
        "safety_hour": 17,
        "safety_minute": 55,
    },
    # Copied verbatim from ramana/scripts/ci/ramana_gate.py's target_time():
    # sha256(f"ramana-gate-{date.isoformat()}") % 41 minutes inside a
    # 05:00-05:40 IST window. "custom" bypasses the generic
    # seed_fn/random.Random formula below since this one is hash-based,
    # not a uniform draw. safety ping placed at 07:55, a few minutes
    # before ramana_gate.py's LATEST=08:00 hard cutoff.
    "ramana": {
        "url_fragment": "post-ramana-short.yml",
        "custom": lambda today: _ramana_target_minutes(today),
        "safety_hour": 7,
        "safety_minute": 55,
    },
}


def _ramana_target_minutes(today) -> tuple[int, int]:
    offset = int(hashlib.sha256(f"ramana-gate-{today.isoformat()}".encode()).hexdigest(), 16) % 41
    total_minutes = 5 * 60 + offset
    return total_minutes // 60, total_minutes % 60


def _todays_target(series_key: str, today, today_ordinal: int) -> tuple[int, int]:
    cfg = SERIES[series_key]
    if "custom" in cfg:
        hour, minute = cfg["custom"](today)
        return int(hour), int(minute)
    offset_minutes = random.Random(cfg["seed_fn"](today_ordinal)).uniform(0, cfg["span"])
    total_minutes = cfg["start_hour"] * 60 + offset_minutes
    return int(total_minutes // 60), int(total_minutes % 60)


def _api_request(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc


def _find_job_id(jobs: list[dict], url_fragment: str) -> int | None:
    for job in jobs:
        if url_fragment in job.get("url", ""):
            return job.get("jobId")
    return None


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    api_key = os.environ.get("CRONJOB_ORG_API_KEY", "").strip()
    if not api_key:
        print("[cronjob-reschedule] CRONJOB_ORG_API_KEY is not set", file=sys.stderr)
        return 1

    today = datetime.now(IST).date()
    today_ordinal = today.toordinal()

    print(f"[cronjob-reschedule] computing schedules for {today.isoformat()} (IST)", file=sys.stderr)

    try:
        listing = _api_request("GET", "/jobs", api_key)
    except RuntimeError as exc:
        print(f"[cronjob-reschedule] failed to list jobs: {exc}", file=sys.stderr)
        return 1

    jobs = listing.get("jobs", [])
    if not jobs:
        print("[cronjob-reschedule] cron-job.org returned no jobs -- check the API key", file=sys.stderr)
        return 1

    exit_code = 0
    for series_key, cfg in SERIES.items():
        target_hour, target_minute = _todays_target(series_key, today, today_ordinal)
        hours = sorted({target_hour, cfg["safety_hour"]})
        minutes = sorted({target_minute, cfg["safety_minute"]})

        job_id = _find_job_id(jobs, cfg["url_fragment"])
        if job_id is None:
            print(
                f"[cronjob-reschedule] {series_key}: no cron-job.org job found matching "
                f"'{cfg['url_fragment']}' -- skipped",
                file=sys.stderr,
            )
            exit_code = 1
            continue

        print(
            f"[cronjob-reschedule] {series_key}: job_id={job_id} target={target_hour:02d}:{target_minute:02d} "
            f"safety={cfg['safety_hour']:02d}:{cfg['safety_minute']:02d} -> "
            f"hours={hours} minutes={minutes}",
            file=sys.stderr,
        )

        if dry_run:
            continue

        schedule = {
            "timezone": "Asia/Kolkata",
            "hours": hours,
            "minutes": minutes,
            "mdays": [-1],
            "months": [-1],
            "wdays": [-1],
        }
        try:
            _api_request("PATCH", f"/jobs/{job_id}", api_key, {"job": {"schedule": schedule}})
            print(f"[cronjob-reschedule] {series_key}: rescheduled OK", file=sys.stderr)
        except RuntimeError as exc:
            print(f"[cronjob-reschedule] {series_key}: reschedule FAILED: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
