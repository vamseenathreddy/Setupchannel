"""
find_comments.py: read-only utility that searches a channel's recent comments
(top-level comments and replies) for a text fragment and prints who wrote
them, on which video, and when. Built 2026-10-09 to find which channel a
viewer's mantra request ("Narsimha Swamy mantram send me") was left on.

Usage (from CI, via the "Tools | Find Comments" workflow):
    python scripts/ci/find_comments.py <text_filter> [max_threads]
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    needle = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    max_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    try:
        youtube = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError

    try:
        ch = youtube.channels().list(part="snippet", mine=True).execute()["items"][0]
        print(f"CHANNEL: {ch['snippet']['title']}  id={ch['id']}  handle={ch['snippet'].get('customUrl', '-')}")
        seen = 0
        hits = 0
        page = None
        while seen < max_threads:
            resp = youtube.commentThreads().list(
                part="snippet,replies", allThreadsRelatedToChannelId=ch["id"],
                maxResults=100, order="time", textFormat="plainText", pageToken=page,
            ).execute()
            for th in resp.get("items", []):
                seen += 1
                top = th["snippet"]["topLevelComment"]
                comments = [top] + th.get("replies", {}).get("comments", [])
                for c in comments:
                    sn = c["snippet"]
                    text = sn.get("textDisplay", "")
                    if needle and needle not in text.lower():
                        continue
                    hits += 1
                    print(f"- video={sn.get('videoId', th['snippet'].get('videoId'))} commentId={c['id']} "
                          f"author={sn.get('authorDisplayName')} channel={sn.get('authorChannelUrl')} "
                          f"at={sn.get('publishedAt')} likes={sn.get('likeCount')}")
                    print(f"    {text!r}")
            page = resp.get("nextPageToken")
            if not page:
                break
        print(f"{hits} match(es) in {seen} thread(s) for '{needle}'")
    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
