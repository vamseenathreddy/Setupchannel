#!/usr/bin/env python3
"""
set_navaratri_thumbnail.py: one-off utility that sets a custom
thumbnail on the most recent "Swarnakavachadharini Kanakadurgamma"
upload. Built 2026-10-03 -- the channel owner approved the final
render and supplied a custom thumbnail graphic for it.

Finds the video by title match (not a hardcoded video id, since this
script may need to re-target a newer draft after a prior fix/re-run --
exactly what happened here: there were two private drafts of this song
on the channel, an earlier one with visual bugs and the corrected one,
and this always picks the most recently published match) rather than
hardcoding a video id that would go stale.

PREREQUISITE: the channel must be phone-verified for custom
thumbnails via the API to work at all -- YouTube rejects
thumbnails.set() with a 403 "youtubeSignupRequired" (or similar) error
on an unverified channel, which this script surfaces plainly rather
than silently failing.

Usage (from CI, via the "Set Navaratri Song Thumbnail" workflow):
    see .github/workflows/set-navaratri-thumbnail.yml

Usage (locally):
    python scripts/ci/set_navaratri_thumbnail.py <path-to-thumbnail.jpg> [title-substring]
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

DEFAULT_TITLE_SUBSTRING = "కనకదుర్గమ్మా"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: set_navaratri_thumbnail.py <path-to-thumbnail.jpg> [title-substring]", file=sys.stderr)
        return 1
    thumbnail_path = sys.argv[1]
    title_substring = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TITLE_SUBSTRING

    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a utility script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    try:
        channels_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
        uploads_playlist_id = channels_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_ids: list[str] = []
        page_token = None
        while len(video_ids) < 50:
            resp = youtube.playlistItems().list(
                part="contentDetails", playlistId=uploads_playlist_id,
                maxResults=50, pageToken=page_token,
            ).execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        if not video_ids:
            print("FAILED: no uploads found on this channel at all.", file=sys.stderr)
            return 1

        videos_resp = youtube.videos().list(part="snippet", id=",".join(video_ids)).execute()
        matches = [
            item for item in videos_resp.get("items", [])
            if title_substring in item["snippet"]["title"]
        ]
        if not matches:
            print(f"FAILED: no uploaded video found with '{title_substring}' in its title.", file=sys.stderr)
            return 1
        matches.sort(key=lambda item: item["snippet"]["publishedAt"], reverse=True)
        target = matches[0]
        video_id = target["id"]
        print(f"Target video: {video_id} -- \"{target['snippet']['title']}\" (published {target['snippet']['publishedAt']})")
        if len(matches) > 1:
            print(f"Note: {len(matches)} videos matched '{title_substring}'; picked the most recently published one.")

        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        print(f"SUCCESS: thumbnail set on video {video_id}")

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
