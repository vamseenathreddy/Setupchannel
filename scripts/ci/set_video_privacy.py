"""
set_video_privacy.py: one-off utility to change a single YouTube
video's privacyStatus (e.g. "unlisted" -> "public") via the Data API
v3. Built 2026-10-03 to publish the Mesha Rashi Mantra test upload
without needing to touch YouTube Studio by hand, and reusable for any
future test video.

Usage (from CI, via the "Set Video Privacy" workflow -- the normal
path, since it needs the REAL saved token restored from Drive):
    see .github/workflows/set-video-privacy.yml

Usage (locally, after youtube_shorts_auth_setup.py has run once):
    python -m mahanavi.scripts.set_video_privacy VIDEO_ID public
(not wired as a package script -- invoked directly as below instead)
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

VALID_STATUSES = {"public", "unlisted", "private"}


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: set_video_privacy.py VIDEO_ID {public|unlisted|private}", file=sys.stderr)
        return 1

    video_id, status = sys.argv[1], sys.argv[2]
    if status not in VALID_STATUSES:
        print(f"Invalid status {status!r}, must be one of {VALID_STATUSES}", file=sys.stderr)
        return 1

    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a utility script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError

    try:
        current = youtube.videos().list(part="status", id=video_id).execute()
        items = current.get("items", [])
        if not items:
            print(f"No video found with id {video_id}", file=sys.stderr)
            return 1
        video_status = items[0]["status"]
        video_status["privacyStatus"] = status
        youtube.videos().update(
            part="status",
            body={"id": video_id, "status": video_status},
        ).execute()
        print(f"Video {video_id} privacyStatus set to {status}.")
    except HttpError as exc:
        print(f"FAILED to update {video_id}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
