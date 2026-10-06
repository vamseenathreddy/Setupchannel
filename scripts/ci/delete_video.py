"""delete_video.py: permanently delete ONE video by id (explicitly authorized
by the owner on 2026-10-06 to remove unlisted duplicate Puranam Shorts).
Usage: python scripts/ci/delete_video.py VIDEO_ID [EXPECTED_TITLE_SUBSTRING]
Refuses if the title substring is given and does not match."""
from __future__ import annotations
import sys
from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    video_id = sys.argv[1]
    expect = sys.argv[2] if len(sys.argv) > 2 else ""
    try:
        yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    items = yt.videos().list(part="snippet,status", id=video_id).execute().get("items", [])
    if not items:
        print(f"FAILED: {video_id} not found (already deleted?)", file=sys.stderr)
        return 1
    title, privacy = items[0]["snippet"]["title"], items[0]["status"]["privacyStatus"]
    print(f"{video_id} [{privacy}] '{title}'")
    if expect and expect not in title:
        print("FAILED: title does not match expectation, not deleting", file=sys.stderr)
        return 1
    yt.videos().delete(id=video_id).execute()
    print(f"DELETED {video_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
