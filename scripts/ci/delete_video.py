"""delete_video.py: permanently delete ONE video by id (explicitly authorized
by the owner on 2026-10-06 to remove unlisted duplicate Puranam Shorts).
Usage: python scripts/ci/delete_video.py VIDEO_ID [EXPECTED_TITLE_SUBSTRING]
Refuses if the title substring is given and does not match."""
from __future__ import annotations
import sys
from ytcore.config import get_settings
from ytcore.exceptions import YouTubeUploadError
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def clear_from_playlists(yt, video_id: str) -> int:
    """Remove the video from every playlist of the channel (deleted Shorts must not linger)."""
    n, tok = 0, None
    while True:
        r = yt.playlists().list(part="id", mine=True, maxResults=50, pageToken=tok).execute()
        for p in r.get("items", []):
            ptok = None
            while True:
                q = yt.playlistItems().list(part="id", playlistId=p["id"], videoId=video_id,
                                            maxResults=50, pageToken=ptok).execute()
                for it in q.get("items", []):
                    yt.playlistItems().delete(id=it["id"]).execute()
                    n += 1
                ptok = q.get("nextPageToken")
                if not ptok:
                    break
        tok = r.get("nextPageToken")
        if not tok:
            return n


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
    removed = clear_from_playlists(yt, video_id)
    print(f"Removed from {removed} playlist item(s)")
    yt.videos().delete(id=video_id).execute()
    print(f"DELETED {video_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
