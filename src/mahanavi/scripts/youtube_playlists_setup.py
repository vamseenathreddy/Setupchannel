"""
youtube_playlists_setup.py: one-time script that creates the channel's
4 series playlists via the YouTube Data API v3 and prints their IDs --
added 2026-10-03 (pipeline health review suggestion #2, "no
playlists"). Grouping choice: ONE playlist covers both Gita Sloka modes
(verse days AND quiz days), since they're literally one alternating
series, not two -- matches post_gita_sloka_short.py's own framing.

IDEMPOTENT: if a playlist with the exact same title already exists on
the channel (checked via playlists().list(mine=True) first), it reuses
that playlist's ID instead of creating a duplicate -- safe to re-run.

Usage (locally, after youtube_shorts_auth_setup.py has run once):
    python -m mahanavi.scripts.youtube_playlists_setup

Usage (from CI, via the one-off "Set Up YouTube Playlists" workflow,
workflow_dispatch -- this is the normal path, since this script needs
the REAL saved token, which only exists where data/youtube_token.json
has been restored from Drive):
    see .github/workflows/setup-playlists.yml

After it runs, copy the 4 printed playlist IDs into these GitHub repo
secrets (Settings -> Secrets and variables -> Actions):
    MAHANAVI_PLAYLIST_ID_MUHURTAS
    MAHANAVI_PLAYLIST_ID_GITA_SLOKA
    MAHANAVI_PLAYLIST_ID_PURANAS
    MAHANAVI_PLAYLIST_ID_RASHI
Each posting workflow already passes these through as env vars (see
.github/workflows/*.yml) -- once the secrets exist, every future
upload gets added to its series playlist automatically, no further
action needed.
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

# (settings field name suffix, playlist title, playlist description)
PLAYLISTS_TO_CREATE = [
    ("muhurtas", "Daily Muhurtams (Rahu Kalam, Shubha Ghadiyalu, Durmuhurtham)",
     "Daily auspicious/inauspicious timings -- Mahanavi Spirituals."),
    ("gita_sloka", "Bhagavad Gita Sloka & Quiz",
     "A new Bhagavad Gita verse every other day, with a quiz on the "
     "alternating days -- Mahanavi Spirituals."),
    ("puranas", "Purana Stories & Concepts",
     "Short Purana stories and concepts from Hindu scripture -- Mahanavi Spirituals."),
    ("rashi", "Rashi Mantras",
     "Ruling-planet mantras for all 12 rashis -- Mahanavi Spirituals."),
]


def main() -> int:
    settings = get_settings()

    try:
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        print(f"Missing packages: {exc}. Run: pip install google-api-python-client", file=sys.stderr)
        return 1

    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a setup script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print("Fetching this channel's existing playlists...")
    existing_by_title: dict[str, str] = {}
    page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50, pageToken=page_token,
        )
        response = request.execute()
        for item in response.get("items", []):
            existing_by_title[item["snippet"]["title"]] = item["id"]
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    results: dict[str, str] = {}
    for key, title, description in PLAYLISTS_TO_CREATE:
        if title in existing_by_title:
            playlist_id = existing_by_title[title]
            print(f"Already exists: \"{title}\" -> {playlist_id}")
        else:
            try:
                response = youtube.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {"title": title, "description": description},
                        "status": {"privacyStatus": "public"},
                    },
                ).execute()
                playlist_id = response["id"]
                print(f"Created: \"{title}\" -> {playlist_id}")
            except HttpError as exc:
                print(f"FAILED to create \"{title}\": {exc}", file=sys.stderr)
                return 1
        results[key] = playlist_id

    print("\n=== Copy these into GitHub repo secrets (Settings -> Secrets and variables -> Actions) ===")
    for key, playlist_id in results.items():
        print(f"MAHANAVI_PLAYLIST_ID_{key.upper()}={playlist_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
