"""Gate: should THIS tick post today's Short, and is it past today's target minute?

An external pinger (cron-job.org) dispatches the workflow every 5 minutes through the window.
Only the first ping that is past the target minute and not yet done proceeds. Every other ping is a cheap no-op.

  python scripts/ci/ramana_gate.py            # reads state/ramana_state.json, writes outputs for GitHub Actions
  python scripts/ci/ramana_gate.py --now 2026-10-07T05:12:00   # test with a fixed IST time
"""
import argparse
import datetime as dt
import hashlib
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src import state as state_mod  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")
WINDOW_START = dt.time(5, 0)     # earliest possible post time
WINDOW_MINUTES = 40              # target minute is inside 05:00 to 05:40 IST
LATEST = dt.time(8, 0)           # a late backup run may still post until this time, after that the day is skipped


def target_time(date: dt.date) -> dt.datetime:
    """Day-seeded minute inside the window: the same date always gives the same minute, so every ping agrees."""
    offset = int(hashlib.sha256(f"ramana-gate-{date.isoformat()}".encode()).hexdigest(), 16) % (WINDOW_MINUTES + 1)
    return dt.datetime.combine(date, WINDOW_START, tzinfo=IST) + dt.timedelta(minutes=offset)


def decide(now: dt.datetime, state: dict, force: bool = False):
    """Return (post: bool, message: str, date_iso: str)."""
    now = now.astimezone(IST)
    date = now.date()
    iso = date.isoformat()
    tgt = target_time(date)
    if iso in state.get("posted", {}):
        return False, f"DECISION: skip, already done ({state['posted'][iso]['row']} -> {state['posted'][iso]['video_id']})", iso
    if force:
        return True, "DECISION: post ramana (forced)", iso
    if now < tgt:
        return False, f"DECISION: skip, before target {tgt:%H:%M} IST (now {now:%H:%M})", iso
    if now.time() > LATEST:
        return False, f"DECISION: skip, missed window (now {now:%H:%M}, latest {LATEST:%H:%M})", iso
    late = int((now - tgt).total_seconds() // 60)
    return True, f"DECISION: post ramana (target {tgt:%H:%M}, now {now:%H:%M}, {late} min after target)", iso


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", help="fixed IST time for testing, e.g. 2026-10-07T05:12:00")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.fromisoformat(args.now).replace(tzinfo=IST) if args.now else dt.datetime.now(IST)
    post, message, iso = decide(now, state_mod.load(), force=args.force or os.environ.get("FORCE_POST") == "true")
    print(message)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"post={'true' if post else 'false'}\ndate={iso}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
