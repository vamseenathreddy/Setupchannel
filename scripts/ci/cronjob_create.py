#!/usr/bin/env python3
"""Create (or re-point) cron-job.org jobs that dispatch this repo's posting workflows.

New jobs are CLONED from an existing job (the Rashi Mantra one): same GitHub dispatch URL pattern, headers
(including the GitHub token) and body, only the workflow file name and schedule change. The token is copied
server-side inside this script and never printed.

Static schedules (every 10 minutes through the window) are used for the Ramana Shorts, whose windows are
12-1 AM, 10-11 AM and 5-6 PM IST.
(cronjob_reschedule.py) narrows it to the day's target minute from then on.

Usage: CRONJOB_ORG_API_KEY=... python3 scripts/ci/cronjob_create.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
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
    # Channel B (from Sat 10 Oct 2026) and Channel C (2026-10-09): static 10-minute pings.
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
    rc = 0
    jobs = _api_request("GET", "/jobs", key).get("jobs", [])
    print(f"cron-job.org lists {len(jobs)} jobs")
    for j in jobs:
        print(f"job {j.get('jobId')}: {j.get('title')!r} -> ...{j.get('url', '')[-60:]} enabled={j.get('enabled')}")
    # Keep every ping job pointed at THIS repo, whatever it is called now (GITHUB_REPOSITORY): a rename or a
    # rename-back otherwise leaves jobs calling a name that no longer exists.
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    for j in jobs:
        url = j.get("url", "")
        m = re.search(r"api\.github\.com/repos/([^/]+/[^/]+)/actions", url)
        if repo and m and m.group(1).lower() != repo.lower():
            print(f"::notice::re-pointing job {j.get('jobId')} {j.get('title')!r}: {m.group(1)} -> {repo}")
            if not dry:
                time.sleep(1.2)
                try:
                    _api_request("PATCH", f"/jobs/{j['jobId']}", key, {"job": {"url": url.replace(m.group(1), repo)}})
                except RuntimeError as exc:
                    print(f"::error::FAILED {str(exc)[:300]}")
                    rc = 1
    jobs = _api_request("GET", "/jobs", key).get("jobs", []) if not dry else jobs
    by_repo: dict[str, int] = {}
    for j in jobs:
        mm = re.search(r"api\.github\.com/repos/([^/]+/[^/]+)/actions", j.get("url", ""))
        by_repo[mm.group(1) if mm else "other"] = by_repo.get(mm.group(1) if mm else "other", 0) + 1
    print(f"::notice::SUMMARY jobs per target repo after re-point: {by_repo}")
    tmpl_id = _find_job_id(jobs, TEMPLATE_FRAGMENT)
    if tmpl_id is None:
        print(f"no template job matching {TEMPLATE_FRAGMENT}", file=sys.stderr)
        return 1
    tmpl = _api_request("GET", f"/jobs/{tmpl_id}", key).get("jobDetails", {})
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
            print(f"::error::FAILED {str(exc)[:300]}")
            rc = 1
    if not dry:
        rc = max(rc, _verify(key, repo))
    return rc


def _verify(key: str, repo: str) -> int:
    """One summary annotation: for every target workflow, each matching cron-job.org job's enabled flag,
    repo match, and first/last ping time -- so a mis-pointed or mis-scheduled job shows up immediately."""
    jobs = _api_request("GET", "/jobs", key).get("jobs", [])
    parts, bad = [], 0
    any_ok: dict[str, bool] = {}
    for fragment, _title, hours, minutes in TARGETS:
        want_h = hours
        for j in jobs:
            if fragment not in j.get("url", ""):
                continue
            time.sleep(0.6)
            d = _api_request("GET", f"/jobs/{j['jobId']}", key).get("jobDetails", {})
            sch = d.get("schedule", {})
            ok = (d.get("enabled") and repo.lower() in d.get("url", "").lower()
                  and sorted(sch.get("hours", [])) == sorted(want_h))
            any_ok[fragment] = any_ok.get(fragment, False) or bool(ok)
            any_ok.setdefault(fragment, False)
            parts.append(f"{fragment}#{j['jobId']}:{'OK' if ok else 'BAD'} en={d.get('enabled')} "
                         f"h={sch.get('hours')} m={sch.get('minutes')}")
    bad = sum(1 for v in any_ok.values() if not v)  # a stray extra job is fine if one correct job exists
    print("::notice::VERIFY " + " ; ".join(parts))
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # surface the reason as a run annotation (logs are not readable from the API)
        import traceback
        print("::error::" + traceback.format_exc().replace("\n", " | ")[-900:])
        sys.exit(1)
