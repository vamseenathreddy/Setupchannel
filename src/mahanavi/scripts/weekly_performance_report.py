"""
weekly_performance_report.py: pulls the last 7 days' view/like/
retention stats for every video uploaded in that window (via the
database.uploads log -- see UploadLogRepository), aggregates them PER
SERIES (muhurtas / gita_sloka / puranas / rashi), and sends a short
Telegram summary -- added 2026-10-03 (pipeline health review
suggestion #3, "no performance feedback loop").

WHY THIS MATTERS: every rotation in this codebase (mantras, titles,
hooks, CTAs, which deity shows up) is currently picked by a date
formula, never by what's actually being watched. This script is the
first step toward closing that loop -- it doesn't change any content
decisions by itself, but it's what would let a human (or a future
automated step) notice "the Durmuhurtham videos are retaining way
better than Shubha Ghadiyalu" instead of only ever guessing.

ONE-TIME PREREQUISITE: requires the yt-analytics.readonly scope on the
saved token, which is NOT there until youtube_shorts_auth_setup.py is
re-run once (it now requests this scope too) and the refreshed token
is pushed to Drive. Until then, this script prints clear instructions
and exits non-zero rather than posting a broken/empty report.

Usage:
    python -m mahanavi.scripts.weekly_performance_report
    python -m mahanavi.scripts.weekly_performance_report --days 14
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from mahanavi.config import get_settings
from mahanavi.database.db import DatabaseManager
from mahanavi.database.repositories import UploadLogRepository
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.notifications.telegram_alert import send_telegram_alert
from mahanavi.publishers.youtube_analytics_client import fetch_video_stats

SERIES_DISPLAY_NAMES = {
    "muhurtas": "Muhurtams (Rahu/Shubha/Durmuhurtham)",
    "gita_sloka": "Bhagavad Gita Sloka & Quiz",
    "puranas": "Purana Stories & Concepts",
    "rashi": "Rashi Mantras",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="How many days back to report on (default 7).")
    args = parser.parse_args()

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()
    since = today - timedelta(days=args.days)

    db = DatabaseManager(settings.database_path)
    repo = UploadLogRepository(db)
    pairs = repo.all_video_ids_since(since)

    if not pairs:
        print(f"No uploads logged since {since.isoformat()} -- nothing to report.")
        return 0

    video_ids = [vid for vid, _series in pairs]
    series_by_video = dict(pairs)

    try:
        stats = fetch_video_stats(settings, video_ids, since.isoformat(), today.isoformat())
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # most commonly an HttpError over the missing scope
        print(
            f"FAILED to fetch YouTube Analytics data: {exc}\n\n"
            "This usually means the saved token doesn't have the yt-analytics.readonly "
            "scope yet. Re-run `python -m mahanavi.scripts.youtube_shorts_auth_setup` "
            "once (it now requests this scope too), then push the refreshed "
            "data/youtube_token.json to Drive.",
            file=sys.stderr,
        )
        return 1

    # Aggregate per series.
    totals: dict[str, dict[str, float]] = {}
    for video_id, series in series_by_video.items():
        row = stats.get(video_id)
        if row is None:
            continue
        agg = totals.setdefault(series, {"videos": 0.0, "views": 0.0, "likes": 0.0, "retention_sum": 0.0})
        agg["videos"] += 1
        agg["views"] += row["views"]
        agg["likes"] += row["likes"]
        agg["retention_sum"] += row["averageViewPercentage"]

    if not totals:
        print(f"No Analytics data returned for the {len(video_ids)} video(s) logged since {since.isoformat()}.")
        return 0

    lines = [f"\U0001f4ca Mahanavi Spirituals -- last {args.days} days ({since.isoformat()} to {today.isoformat()})\n"]
    for series, agg in sorted(totals.items(), key=lambda kv: -kv[1]["views"]):
        avg_retention = agg["retention_sum"] / agg["videos"] if agg["videos"] else 0.0
        display_name = SERIES_DISPLAY_NAMES.get(series, series)
        lines.append(
            f"{display_name}: {int(agg['videos'])} videos, "
            f"{int(agg['views'])} views, {int(agg['likes'])} likes, "
            f"{avg_retention:.0f}% avg retention"
        )
    message = "\n".join(lines)

    print(message)
    send_telegram_alert(message, settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
