#!/usr/bin/env python3
"""read_video_details.py: prints title, description, tags, duration and
thumbnail URLs of the channel's own uploads whose title contains a given
substring. Read-only. Used to reuse the lyrics and metadata of an
existing video (e.g. the Kamakhya stotram) for the weekly stotra series.

Usage: python scripts/ci/read_video_details.py <title_substring> [max_scan]
"""
from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    needle = sys.argv[1].lower()
    max_scan = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    try:
        yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    ch = yt.channels().list(part="snippet,contentDetails", mine=True).execute()["items"][0]
    print(f"CHANNEL: {ch['snippet']['title']}")
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < max_scan:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,contentDetails,status", id=",".join(ids[i:i + 50])).execute()
        for v in r.get("items", []):
            s = v["snippet"]
            if needle not in s["title"].lower():
                continue
            print("=" * 70)
            print(f"ID: {v['id']}  privacy={v['status']['privacyStatus']}  duration={v['contentDetails']['duration']}")
            print(f"TITLE: {s['title']}")
            print(f"PUBLISHED: {s['publishedAt']}  category={s.get('categoryId')}")
            print(f"TAGS: {s.get('tags')}")
            print(f"THUMBS: { {k: t['url'] for k, t in s.get('thumbnails', {}).items()} }")
            print("DESCRIPTION:")
            print(s["description"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
