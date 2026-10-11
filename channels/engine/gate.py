"""Generic gate: should THIS call post today, and is it past today's target minute?
Shared by every Pattern-A channel -- same day-seeded-target-minute design as
ramana/scripts/ci/ramana_gate.py (and scripts/ci/cronjob_reschedule.py mirrors each
channel's formula so the daily reschedule orchestrator can compute the same target).

Each channel's own tiny scripts/ci/gate.py just calls run(channel_key, window_start,
window_minutes, latest) with its own window -- see channels/jesus/scripts/ci/gate.py for
the thinnest possible example.
"""
import argparse
import datetime as dt
import hashlib
import os
import sys
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Fixed posting times (from 2026-10-11): every Short posts at its window start instead of a random minute,
# so a handful of exact cron-job.org pings is enough (saves GitHub Actions minutes). Flip to False to bring
# back the day-seeded random minute.
FIXED_TIMES = True


def target_time(channel_key: str, date: dt.date, window_start: dt.time, window_minutes: int) -> dt.datetime:
    """Day-seeded minute inside the window: the same date always gives the same minute, so every
    ping agrees. channel_key salts the hash so different channels don't all land on the same
    offset-from-window-start minute."""
    if FIXED_TIMES:
        return dt.datetime.combine(date, window_start, tzinfo=IST)
    offset = int(hashlib.sha256(f"{channel_key}-gate-{date.isoformat()}".encode()).hexdigest(), 16) % (window_minutes + 1)
    return dt.datetime.combine(date, window_start, tzinfo=IST) + dt.timedelta(minutes=offset)


def decide(channel_key, now, state, window_start, window_minutes, latest, force=False):
    """Return (post: bool, message: str, date_iso: str)."""
    now = now.astimezone(IST)
    date = now.date()
    iso = date.isoformat()
    tgt = target_time(channel_key, date, window_start, window_minutes)
    key = os.environ.get("POST_SLOT", "")
    key = f"{iso}#{key}" if key else iso
    if key in state.get("posted", {}) and not force:
        return False, f"DECISION: skip, already done ({state['posted'][key]['row']} -> {state['posted'][key]['video_id']})", iso
    if force:
        return True, f"DECISION: post {channel_key} (forced)", iso
    if now < tgt:
        return False, f"DECISION: skip, before target {tgt:%H:%M} IST (now {now:%H:%M})", iso
    if now.time() > latest:
        return False, f"DECISION: skip, missed window (now {now:%H:%M}, latest {latest:%H:%M})", iso
    late = int((now - tgt).total_seconds() // 60)
    return True, f"DECISION: post {channel_key} (target {tgt:%H:%M}, now {now:%H:%M}, {late} min after target)", iso


def run(channel_key: str, window_start: dt.time, window_minutes: int, latest: dt.time) -> int:
    """Called by each channel's own scripts/ci/gate.py. Reads state via STATE_FILE (engine.state's
    default), writes GitHub Actions outputs post=true/false and date=<iso>."""
    from . import state as state_mod

    ap = argparse.ArgumentParser()
    ap.add_argument("--now", help="fixed IST time for testing, e.g. 2026-10-07T05:12:00")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.fromisoformat(args.now).replace(tzinfo=IST) if args.now else dt.datetime.now(IST)
    post, message, iso = decide(
        channel_key, now, state_mod.load(), window_start, window_minutes, latest,
        force=args.force or os.environ.get("FORCE_POST") == "true",
    )
    print(message)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"post={'true' if post else 'false'}\ndate={iso}\n")
    return 0
