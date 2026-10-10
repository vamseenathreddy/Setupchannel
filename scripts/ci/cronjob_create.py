#!/usr/bin/env python3
"""Create (or re-point) cron-job.org jobs that dispatch this repo's posting workflows.

New jobs are CLONED from an existing job (the Rashi Mantra one): same GitHub dispatch URL pattern, headers
(including the GitHub token) and body, only the workflow file name and schedule change. The token is copied
server-side inside this script and never printed.

Static schedules (every 10 minutes through the window) are used for the Ramana Shorts, whose windows are
12-1 AM, 10-11 AM and 5-6 PM IST. Jesus Bible Quiz starts with a wide evening schedule; the daily orchestrator
(cronjob_reschedule.py) narrows it to the day's target minute from then on.

Usage: CRONJOB_ORG_API_KEY=... python3 scripts/ci/cronjob_create.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cronjob_reschedule import _api_request, _find_job_id  # noqa: E402

TEMPLATE_FRAGMENT = "post-rashi-mantra.yml"


def _every_10(start_h, start_m, count):
    """hours/minutes lists covering `count` pings every 10 minutes from start_h:start_m."""
    t = start_h * 60 + start_m
    pts = [(t + 10 * i) for i in range(count)]
    hours = sorted({(p // 60) % 24 for p in pts})
    minutes = sorted({p % 60 for p in pts})
    return hours, minutes


# (workflow file, job title, hours, minutes)
TARGETS = [
    ("daily-shorts.yml", "Mahanavi - Timing Shorts Rahu/Shubh/Durm (12-3 AM)", *_every_10(0, 0, 18)),
    ("post-ramana-short.yml", "Ramana Maharshi TV - quote Short (12-1 AM)", *_every_10(0, 0, 10)),
    ("post-ramana-qa.yml", "Ramana Maharshi TV - Q&A Short (10-11 AM)", *_every_10(10, 0, 10)),
    ("post-ramana-life.yml", "Ramana Maharshi TV - Life Short (5-6 PM)", *_every_10(17, 0, 10)),
    # Jesus posts 3 public Shorts a day (2026-10-10): static 10-minute pings through each window; the gates
    # (channels/jesus/scripts/ci/gate*.py) pick the day's random minute inside it.
    ("post-jesus-worship-waves.yml", "Jesus - Bible Quote Short (12-1 AM)", *_every_10(0, 0, 6)),
    ("post-jesus-bible-quiz.yml", "Jesus - Bible Quiz Short (9-10 AM)", *_every_10(9, 0, 6)),
    ("post-jesus-bible-quote-pm.yml", "Jesus - Bible Quote Short 2 (5-6 PM)", *_every_10(17, 0, 6)),
    # Divine Mantra Sangam (from Sat 10 Oct 2026) and Devotional Trance Beats (2026-10-09): static 10-minute pings.
    ("post-mantra-sangam-rahu.yml", "Mantra Sangam - Rahu Kaal Short (12 AM)", *_every_10(0, 5, 6)),
    ("post-mantra-sangam-shubh.yml", "Mantra Sangam - Shubh Muhurat Short (1 AM)", *_every_10(1, 5, 6)),
    ("post-mantra-sangam-durm.yml", "Mantra Sangam - Durmuhurat Short (2 AM)", *_every_10(2, 5, 6)),
    ("post-mantra-sangam-purana.yml", "Mantra Sangam - Purana Story Short (5 PM)", *_every_10(17, 0, 6)),
    ("post-beej-mahanavi.yml", "Mahanavi - Beej Mantra Short (6 AM)", *_every_10(6, 0, 6)),
    ("post-beej-mantra-sangam.yml", "Mantra Sangam - Beej Mantra Short (6 AM)", *_every_10(6, 0, 6)),
    ("post-beej-trance-beats.yml", "Trance Beats - Beej Mantra Short (6 AM)", *_every_10(6, 0, 6)),
    ("post-trance-bhagavatam.yml", "Trance Beats - Bhagavatam Short (7 AM)", *_every_10(7, 0, 12)),
    ("post-trance-mantra.yml", "Trance Beats - Mantra Short (1 PM)", *_every_10(13, 0, 12)),
    ("post-devotional-trance-beats.yml", "Trance Beats - Gita Short (7 PM)", *_every_10(19, 0, 12)),
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    key = os.environ.get("CRONJOB_ORG_API_KEY", "").strip()
    if not key:
        print("CRONJOB_ORG_API_KEY is not set", file=sys.stderr)
        return 1
    jobs = _api_request("GET", "/jobs", key).get("jobs", [])
    print(f"cron-job.org lists {len(jobs)} jobs")
    for j in jobs:
        print(f"  job {j.get('jobId')}: {j.get('title')!r} -> ...{j.get('url', '')[-45:]} enabled={j.get('enabled')}")
    tmpl_id = _find_job_id(jobs, TEMPLATE_FRAGMENT)
    if tmpl_id is None:
        print(f"no template job matching {TEMPLATE_FRAGMENT}", file=sys.stderr)
        return 1
    tmpl = _api_request("GET", f"/jobs/{tmpl_id}", key).get("jobDetails", {})
    rc = 0
    for fragment, title, hours, minutes in TARGETS:
        schedule = {"timezone": "Asia/Kolkata", "hours": hours, "minutes": minutes,
                    "mdays": [-1], "months": [-1], "wdays": [-1]}
        existing = _find_job_id(jobs, fragment)
        print(f"{fragment}: {'update job %s' % existing if existing else 'create'} hours={hours} minutes={minutes}")
        if dry:
            continue
        time.sleep(1.2)
        try:
            if existing:
                _api_request("PATCH", f"/jobs/{existing}", key, {"job": {"schedule": schedule, "enabled": True}})
            else:
                job = {
                    "url": tmpl["url"].replace(TEMPLATE_FRAGMENT, fragment),
                    "enabled": True,
                    "title": title,
                    "saveResponses": False,
                    "requestMethod": tmpl.get("requestMethod", 1),
                    "schedule": schedule,
                    "extendedData": tmpl.get("extendedData", {}),
                }
                res = _api_request("PUT", "/jobs", key, {"job": job})
                print(f"  created: {json.dumps(res)}")
        except RuntimeError as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
