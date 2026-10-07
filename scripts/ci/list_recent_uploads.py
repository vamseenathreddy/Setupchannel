"""
list_recent_uploads.py: one-off utility that lists the channel's most
recent uploads (title, video id, privacyStatus, publishedAt), optionally
filtered by a substring in the title. Built 2026-10-03 to audit how many
Rashi Mantra test videos are sitting as unlisted/public after repeated
manual test dispatches, since this cloud session has no direct access
to the real channel -- only CI (with the real restored token) does.

Usage (from CI, via the "List Recent Uploads" workflow):
    see .github/workflows/list-recent-uploads.yml

Usage (locally):
    python scripts/ci/list_recent_uploads.py [max_results] [title_filter]
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    max_results = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    title_filter = sys.argv[2].lower() if len(sys.argv) > 2 else None

    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a utility script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError

    try:
        channels_resp = youtube.channels().list(part="snippet,contentDetails", mine=True).execute()
        ch = channels_resp["items"][0]
        # Which channel does this token actually act as? (Brand-account pick at consent decides it.)
        print(f"CHANNEL: {ch['snippet']['title']}  id={ch['id']}  handle={ch['snippet'].get('customUrl', '-')}")
        uploads_playlist_id = channels_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_ids: list[str] = []
        page_token = None
        while len(video_ids) < max_results:
            resp = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=page_token,
            ).execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        if not video_ids:
            print("No videos found.")
            return 0

        # videos().list accepts at most 50 ids per call -- batch it.
        items_all: list[dict] = []
        for i in range(0, len(video_ids), 50):
            chunk = youtube.videos().list(
                part="snippet,status", id=",".join(video_ids[i:i + 50])
            ).execute()
            items_all.extend(chunk.get("items", []))
        videos_resp = {"items": items_all}

        print(f"{'VIDEO ID':<13} {'PRIVACY':<10} {'PUBLISHED':<21} TITLE")
        print("-" * 100)
        shown = 0
        for item in videos_resp.get("items", []):
            title = item["snippet"]["title"]
            if title_filter and title_filter not in title.lower():
                continue
            print(
                f"{item['id']:<13} {item['status']['privacyStatus']:<10} "
                f"{item['snippet']['publishedAt']:<21} {title}"
            )
            shown += 1
        print("-" * 100)
        print(f"{shown} video(s) shown" + (f" (filtered by '{title_filter}')" if title_filter else ""))

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
