#!/usr/bin/env python3
"""channel_report.py: read-only performance report for one channel's own uploads, from the YouTube
Data API (views, likes, comments, duration, privacy). Groups results by series/category and by IST
publish hour so the next batch of content can be aligned to what actually works.

The channel is chosen by the token file (MAHANAVI_YOUTUBE_TOKEN_FILE), same as read_video_details.py.

Usage: python scripts/ci/channel_report.py [days_back=120] [max_scan=800]
"""
from __future__ import annotations

import collections
import datetime as dt
import re
import statistics
import sys
from zoneinfo import ZoneInfo

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

IST = ZoneInfo("Asia/Kolkata")
# Order matters: first match wins. Titles carry the series keyword (see each channel's metadata.py).
SERIES = [
    ("ramana-qa", r"satsang"), ("ramana-life", r"ramana maharshi life"), ("ramana-quote", r"ramana maharshi teachings"),
    ("stotra", r"stotr|kamakhya|స్తోత్ర"), ("gita", r"gita|గీత"), ("rashi", r"rashi|రాశి|మేషం|కర్కాటకం|వారికి"),
    ("purana", r"purana|puranam|పురాణ"), ("navaratri", r"navaratri|నవరాత్రి"), ("alert", r"durmuhurt|rahu|yamagand|దుర్ముహూర్త|రాహు"),
    ("timings", r"muhurt|good time|auspicious|amrit|abhijit|pooja time|timings|శుభ|మంచి సమయం|అభిజిత్"),
    ("quiz", r"quiz|క్విజ్"), ("bhajan/mantra", r"mantra|bhajan|మంత్ర|భజన"), ("song", r"song|పాట"),
]


def series_of(title: str) -> str:
    t = title.lower()
    for name, pat in SERIES:
        if re.search(pat, t):
            return name
    return "other"


def iso_seconds(d: str) -> int:
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + s


def fetch_analytics(settings, days_back: int) -> dict:
    """Per-video retention from the YouTube Analytics API (needs the yt-analytics.readonly scope on the
    saved token). Returns {} with a clear note if the scope is missing, so the rest of the report still prints."""
    try:
        from mahanavi.publishers.youtube_analytics_client import build_analytics_service

        svc = build_analytics_service(settings)
        end = dt.date.today()
        resp = svc.reports().query(
            ids="channel==MINE", startDate=(end - dt.timedelta(days=days_back)).isoformat(), endDate=end.isoformat(),
            metrics="views,averageViewPercentage,averageViewDuration,subscribersGained",
            dimensions="video", sort="-views", maxResults=200,
        ).execute()
    except Exception as exc:  # noqa: BLE001
        print(f"NOTE: retention data unavailable ({type(exc).__name__}: {str(exc)[:160]}). "
              "If this says insufficient scope, re-run youtube_shorts_auth_setup for this channel and push the token to Drive.")
        return {}
    out = {}
    for vid, views, pct, sec, subs in resp.get("rows", []):
        out[vid] = {"views": views, "avgPct": round(pct, 1), "avgSec": round(sec, 1), "subs": int(subs)}
    print(f"RETENTION: analytics rows for {len(out)} videos (top 200 by views)")
    return out


def main() -> int:
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    max_scan = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    try:
        yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    ch = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()["items"][0]
    st = ch["statistics"]
    print(f"CHANNEL: {ch['snippet']['title']} | subs={st.get('subscriberCount')} views={st.get('viewCount')} videos={st.get('videoCount')}")
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < max_scan:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,contentDetails,status,statistics", id=",".join(ids[i:i + 50])).execute()
        for v in r.get("items", []):
            pub = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            age = (now - pub).total_seconds() / 86400
            if age > days_back:
                continue
            s = v.get("statistics", {})
            rows.append({
                "id": v["id"], "title": v["snippet"]["title"], "series": series_of(v["snippet"]["title"]),
                "privacy": v["status"]["privacyStatus"], "secs": iso_seconds(v["contentDetails"].get("duration")),
                "age_days": round(age, 1), "hour_ist": pub.astimezone(IST).hour,
                "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0)),
            })
    analytics = fetch_analytics(get_settings(), days_back)
    for r in rows:
        a = analytics.get(r["id"], {})
        r["avg_pct"], r["avg_sec"], r["subs"] = a.get("avgPct"), a.get("avgSec"), a.get("subs", 0)
    public = [r for r in rows if r["privacy"] == "public"]
    print(f"VIDEOS in last {days_back} days: {len(rows)} (public {len(public)})")
    print("\n== BY SERIES (public only; views per video, median and mean; likes per 100 views) ==")
    by = collections.defaultdict(list)
    for r in public:
        by[r["series"]].append(r)
    for name, vs in sorted(by.items(), key=lambda kv: -sum(x["views"] for x in kv[1]) / len(kv[1])):
        views = [x["views"] for x in vs]
        lk = 100 * sum(x["likes"] for x in vs) / max(1, sum(views))
        withp = [x for x in vs if x.get("avg_pct") is not None]
        tv = sum(x["views"] for x in withp)
        pct = sum(x["avg_pct"] * x["views"] for x in withp) / tv if tv else 0
        subs_k = 1000 * sum(x["subs"] for x in withp) / tv if tv else 0
        print(f"{name:14} n={len(vs):3} median={statistics.median(views):7.0f} mean={statistics.mean(views):8.0f} max={max(views):7} "
              f"likes/100v={lk:4.1f} avg_view%={pct:5.1f} subs/1kviews={subs_k:5.2f}")
    print("\n== BY IST PUBLISH HOUR (public, age>=2d; mean views) ==")
    hh = collections.defaultdict(list)
    for r in public:
        if r["age_days"] >= 2:
            hh[r["hour_ist"]].append(r["views"])
    for h in sorted(hh):
        print(f"{h:02d}:00  n={len(hh[h]):3} mean={statistics.mean(hh[h]):8.0f}")
    print("\n== TOP 15 ==")
    for r in sorted(public, key=lambda x: -x["views"])[:15]:
        print(f"{r['views']:7} v  {r['likes']:4} l  {r['age_days']:5}d  view%={r.get('avg_pct')} subs={r.get('subs')}  [{r['series']}] {r['id']} {r['title']}")
    print("\n== BOTTOM 15 (age>=3d) ==")
    for r in sorted([x for x in public if x["age_days"] >= 3], key=lambda x: x["views"])[:15]:
        print(f"{r['views']:7} v  {r['likes']:4} l  {r['age_days']:5}d  [{r['series']}] {r['id']} {r['title']}")
    print("\n== NON-PUBLIC (drafts waiting for review) ==")
    for r in rows:
        if r["privacy"] != "public":
            print(f"{r['privacy']:8} {r['age_days']:5}d [{r['series']}] {r['id']} {r['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
