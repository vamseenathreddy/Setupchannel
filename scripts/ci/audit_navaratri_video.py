#!/usr/bin/env python3
"""
audit_navaratri_video.py: one-off read-only audit of the
"Swarnakavachadharini Kanakadurgamma" video's current live state --
privacy status, category, captions, playlist membership, made-for-kids
flag, and license -- so we can tell what's still missing for maximum
reach during Navaratri rather than guessing.

Usage (from CI, via the "Audit Navaratri Song" workflow):
    see .github/workflows/audit-navaratri-song.yml
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

TITLE_MATCH = "కనకదుర్గమ్మా"
NAVARATRI_PLAYLIST_ID = "PLR7mQSUcrHXM"


def main() -> int:
    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError

    try:
        channels_resp = youtube.channels().list(part="contentDetails,statistics", mine=True).execute()
        uploads_playlist_id = channels_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        sub_count = channels_resp["items"][0]["statistics"].get("subscriberCount", "hidden")
        print(f"Channel subscriber count: {sub_count}")

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

        videos_resp = youtube.videos().list(
            part="snippet,status,contentDetails,statistics", id=",".join(video_ids)
        ).execute()
        matches = [item for item in videos_resp.get("items", []) if TITLE_MATCH in item["snippet"]["title"]]
        if not matches:
            print(f"FAILED: no uploaded video found with '{TITLE_MATCH}' in its title.", file=sys.stderr)
            return 1
        matches.sort(key=lambda item: item["snippet"]["publishedAt"], reverse=True)

        for item in matches:
            vid = item["id"]
            snippet = item["snippet"]
            status = item["status"]
            content = item["contentDetails"]
            stats = item.get("statistics", {})
            print("=" * 60)
            print(f"Video: {vid}  -- \"{snippet['title']}\"")
            print(f"  Published: {snippet['publishedAt']}")
            print(f"  privacyStatus: {status.get('privacyStatus')}")
            print(f"  madeForKids: {status.get('madeForKids')}")
            print(f"  license: {status.get('license')}")
            print(f"  embeddable: {status.get('embeddable')}")
            print(f"  publicStatsViewable: {status.get('publicStatsViewable')}")
            print(f"  categoryId: {snippet.get('categoryId')}")
            print(f"  caption (flag): {content.get('caption')}")
            print(f"  defaultAudioLanguage: {snippet.get('defaultAudioLanguage')}")
            print(f"  defaultLanguage: {snippet.get('defaultLanguage')}")
            print(f"  views: {stats.get('viewCount')}  likes: {stats.get('likeCount')}  comments: {stats.get('commentCount')}")

            # Captions list (requires separate call)
            try:
                caps_resp = youtube.captions().list(part="snippet", videoId=vid).execute()
                caps = caps_resp.get("items", [])
                if caps:
                    for c in caps:
                        cs = c["snippet"]
                        print(f"  caption track: lang={cs.get('language')} name={cs.get('name')!r} status={cs.get('status')}")
                else:
                    print("  caption track: NONE")
            except HttpError as exc:
                print(f"  caption list error: {exc}")

        # Playlist membership check for the most recent match
        target_id = matches[0]["id"]
        pl_resp = youtube.playlistItems().list(
            part="contentDetails", playlistId=NAVARATRI_PLAYLIST_ID, maxResults=50
        ).execute()
        pl_video_ids = [i["contentDetails"]["videoId"] for i in pl_resp.get("items", [])]
        in_playlist = target_id in pl_video_ids
        print("=" * 60)
        print(f"Navaratri playlist ({NAVARATRI_PLAYLIST_ID}) contains target video {target_id}: {in_playlist}")
        print(f"Navaratri playlist current item count: {len(pl_video_ids)}")

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
