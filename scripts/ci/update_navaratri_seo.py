#!/usr/bin/env python3
"""
update_navaratri_seo.py: one-off utility that pushes the current
navaratri_song_seo.py content (title/description/tags) onto the most
recent "Swarnakavachadharini Kanakadurgamma" upload via
videos().update(). Built 2026-10-03 -- the SEO copy was improved
(Telugu-script tags, playlist link) AFTER the video had already been
uploaded, so the live video's metadata needed a separate push rather
than just being baked in at upload time.

Finds the video by title match and picks the most recently published
one, same approach and same reasoning as set_navaratri_thumbnail.py
(there are currently two private drafts of this song on the channel).

Usage (from CI, via the "Update Navaratri Song SEO" workflow):
    see .github/workflows/update-navaratri-seo.yml
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.content.navaratri_song_seo import build_navaratri_song_seo
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

TITLE_MATCH = "కనకదుర్గమ్మా"

# Fallback only -- the real categoryId is read from the live video's own
# snippet below. "10" is YouTube's Music category (matches
# MUSIC_CATEGORY_ID in post_navaratri_song.py), used only if the video's
# snippet is somehow missing categoryId entirely.
FALLBACK_CATEGORY_ID = "10"


def main() -> int:
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
        matches = [item for item in videos_resp.get("items", []) if TITLE_MATCH in item["snippet"]["title"]]
        if not matches:
            print(f"FAILED: no uploaded video found with '{TITLE_MATCH}' in its title.", file=sys.stderr)
            return 1
        matches.sort(key=lambda item: item["snippet"]["publishedAt"], reverse=True)
        target = matches[0]
        video_id = target["id"]
        print(f"Target video: {video_id} (published {target['snippet']['publishedAt']})")
        if len(matches) > 1:
            print(f"Note: {len(matches)} videos matched '{TITLE_MATCH}'; picked the most recently published one.")

        seo = build_navaratri_song_seo()
        category_id = target["snippet"].get("categoryId", FALLBACK_CATEGORY_ID)
        youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": seo.title,
                    "description": seo.full_caption(),
                    "defaultAudioLanguage": "te",
                    "tags": seo.hashtags,
                    "categoryId": category_id,
                },
            },
        ).execute()
        print(f"SUCCESS: SEO updated on video {video_id} ({len(seo.hashtags)} tags).")

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
