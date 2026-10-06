#!/usr/bin/env python3
"""
Daily orchestrator that re-schedules cron-job.org's 4 gated-series jobs
to fire at TODAY's precise, randomly-chosen target time instead of
ticking repeatedly through a wide window.

WHY THIS EXISTS: rashi_mantra_gate.py / purana_concept_gate.py /
gita_sloka_gate.py / purana_short_gate.py each compute a
date-seeded "today's target minute" and rely on cron-job.org pinging
the workflow repeatedly (every 15 min as of 2026-10-06) through the
whole window so SOME tick lands at-or-after that target before the
window's hard cutoff. Most of those ticks are wasted no-ops (each
still costs 1 billed GitHub Actions minute on this private repo).

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
}


def _todays_target(series_key: str, today_ordinal: int) -> tuple[int, int]:
    cfg = SERIES[series_key]
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
        target_hour, target_minute = _todays_target(series_key, today_ordinal)
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
            _api_request("PUT", f"/jobs/{job_id}", api_key, {"job": {"schedule": schedule}})
            print(f"[cronjob-reschedule] {series_key}: rescheduled OK", file=sys.stderr)
        except RuntimeError as exc:
            print(f"[cronjob-reschedule] {series_key}: reschedule FAILED: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
