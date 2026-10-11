#!/usr/bin/env python3
"""video_status.py: read-only. Prints upload status, processing state, rejection or failure reasons, duration and
view counts for the given video ids (token chooses the channel). Usage: python scripts/ci/video_status.py ID [ID ...]"""
from __future__ import annotations

import json
import sys

from ytcore.config import get_settings
from ytcore.exceptions import YouTubeUploadError
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    ids = [a for a in sys.argv[1:] if a]
    try:
        yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    r = yt.videos().list(part="status,processingDetails,contentDetails,snippet,statistics", id=",".join(ids)).execute()
    found = {v["id"] for v in r.get("items", [])}
    for v in r.get("items", []):
        print("=" * 60)
        print(v["id"], v["snippet"]["title"])
        print("status:", json.dumps(v.get("status", {}), ensure_ascii=False))
        print("processing:", json.dumps(v.get("processingDetails", {}), ensure_ascii=False))
        print("duration:", v.get("contentDetails", {}).get("duration"), "| views:", v.get("statistics", {}).get("viewCount"))
        print("publishedAt:", v["snippet"]["publishedAt"])
    for i in ids:
        if i not in found:
            print(f"{i}: NOT RETURNED by the API (deleted, or not visible to this token)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
