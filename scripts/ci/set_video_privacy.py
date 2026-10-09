"""set_video_privacy.py: change one video's privacy (public/unlisted/private).
Usage: python scripts/ci/set_video_privacy.py VIDEO_ID public
Built 2026-10-06 to publish a reviewed unlisted Puranam Short on explicit request."""
from __future__ import annotations
import sys
from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    video_id, privacy = sys.argv[1], sys.argv[2]
    if privacy not in {"public", "unlisted", "private"}:
        print("FAILED: privacy must be public|unlisted|private", file=sys.stderr)
        return 1
    try:
        yt = YouTubeShortsUploader(get_settings())._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    item = yt.videos().list(part="status,snippet", id=video_id).execute().get("items", [])
    if not item:
        print(f"FAILED: video {video_id} not found", file=sys.stderr)
        return 1
    status = item[0]["status"]
    print(f"{video_id} '{item[0]['snippet']['title']}' was {status['privacyStatus']}")
    status["privacyStatus"] = privacy
    status.pop("publishAt", None)  # drop any scheduled release so the change is immediate
    yt.videos().update(part="status", body={"id": video_id, "status": status}).execute()
    print(f"{video_id} is now {privacy}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
