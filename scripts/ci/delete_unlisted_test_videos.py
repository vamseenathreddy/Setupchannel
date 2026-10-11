"""
delete_unlisted_test_videos.py: finds every video on the channel that
is NOT public (privacyStatus "private" or "unlisted" -- i.e. draft/test
artifacts left over from manual review dispatches) and, only when
explicitly confirmed, permanently deletes them from YouTube.

Built 2026-10-03 per explicit request: "remove all drafted shorts in
playlist and from my youtube". Deleting a video also automatically
removes it from every playlist it's in -- YouTube doesn't need a
separate playlist-removal step.

SAFETY: defaults to DRY RUN (lists candidates, deletes nothing). Pass
--confirm to actually delete. This is irreversible, so the two-step
dry-run-then-confirm flow is deliberate -- always review the candidate
list before confirming.

Usage (from CI, via the "Delete Unlisted Test Videos" workflow):
    see .github/workflows/delete-unlisted-videos.yml

Usage (locally):
    python scripts/ci/delete_unlisted_test_videos.py            # dry run
    python scripts/ci/delete_unlisted_test_videos.py --confirm  # actually delete
"""

from __future__ import annotations

import sys

from ytcore.config import get_settings
from ytcore.exceptions import YouTubeUploadError
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    confirm = "--confirm" in sys.argv

    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a utility script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError

    try:
        channels_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
        uploads_playlist_id = channels_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_ids: list[str] = []
        page_token = None
        while True:
            resp = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=page_token,
            ).execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        if not video_ids:
            print("No videos found on channel.")
            return 0

        candidates: list[tuple[str, str, str]] = []  # (id, title, privacyStatus)
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            videos_resp = youtube.videos().list(part="snippet,status", id=",".join(batch)).execute()
            for item in videos_resp.get("items", []):
                status = item["status"]["privacyStatus"]
                if status != "public":
                    candidates.append((item["id"], item["snippet"]["title"], status))

        if not candidates:
            print("No non-public (draft/unlisted/private) videos found -- nothing to delete.")
            return 0

        print(f"{'VIDEO ID':<13} {'PRIVACY':<10} TITLE")
        print("-" * 100)
        for vid, title, status in candidates:
            print(f"{vid:<13} {status:<10} {title}")
        print("-" * 100)
        print(f"{len(candidates)} candidate(s) found.")

        if not confirm:
            print("\nDRY RUN -- nothing deleted. Re-run with --confirm to actually delete these.")
            return 0

        print("\n--confirm passed -- deleting now...")
        deleted = 0
        for vid, title, status in candidates:
            try:
                youtube.videos().delete(id=vid).execute()
                print(f"Deleted {vid} ({status}): {title}")
                deleted += 1
            except HttpError as exc:
                print(f"FAILED to delete {vid}: {exc}", file=sys.stderr)
        print(f"\n{deleted}/{len(candidates)} video(s) deleted.")

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
