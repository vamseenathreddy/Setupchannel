#!/usr/bin/env python3
"""Disable every cron-job.org job whose URL contains the given workflow file name.
Usage: CRONJOB_ORG_API_KEY=... python3 scripts/ci/cronjob_disable.py post-divine-mantra-sangam.yml"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from cronjob_reschedule import _api_request  # noqa: E402

key = os.environ["CRONJOB_ORG_API_KEY"].strip()
frag = sys.argv[1]
n = 0
for j in _api_request("GET", "/jobs", key).get("jobs", []):
    if frag in j.get("url", ""):
        time.sleep(1.2)
        _api_request("PATCH", f"/jobs/{j['jobId']}", key, {"job": {"enabled": False}})
        print(f"disabled job {j['jobId']} {j.get('title')!r}")
        n += 1
print(f"{n} job(s) disabled")
