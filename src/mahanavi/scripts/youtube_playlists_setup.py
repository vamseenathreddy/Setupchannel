"""
youtube_playlists_setup.py: one-time script that creates the channel's
4 series playlists via the YouTube Data API v3 and prints their IDs --
added 2026-10-03 (pipeline health review suggestion #2, "no
playlists"). Grouping choice: ONE playlist covers both Gita Sloka modes
(verse days AND quiz days), since they're literally one alternating
series, not two -- matches post_gita_sloka_short.py's own framing.

IDEMPOTENT: if a playlist with the exact same title already exists on
the channel (checked via playlists().list(mine=True) first), it reuses
that playlist's ID instead of creating a duplicate, and re-syncs its
description to whatever's currently in PLAYLISTS_TO_CREATE below --
safe to re-run any time, including just to push an edited description
to an already-live playlist.

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

# (settings field name suffix, playlist title, playlist description).
# Descriptions rewritten 2026-10-03 for actual SEO value (bilingual,
# keyword-bearing, several sentences) -- the original one-liners were
# barely more than the title repeated. main() keeps these in sync on
# every run, even for a playlist that already exists (see the
# "Already exists" branch below), so editing this list and re-running
# is how you update a live playlist's description going forward.
PLAYLISTS_TO_CREATE = [
    (
        "muhurtas",
        "Daily Muhurtams (Rahu Kalam, Shubha Ghadiyalu, Durmuhurtham)",
        "ప్రతిరోజు రాహు కాలం, శుభ ఘడియలు, దుర్ముహూర్తం సమయాలను ఖచ్చితమైన "
        "పంచాంగం ఆధారంగా తెలుసుకోండి. ఏ సమయంలో ఏ పని ప్రారంభించాలో, "
        "ఏది మానుకోవాలో ఇక్కడ ప్రతి ఉదయం తెలుసుకోవచ్చు -- అదే సమయంలో ఆ "
        "రోజు దేవత మంత్రం కూడా జత చేయబడింది.\n\n"
        "Your daily guide to Rahu Kalam, Shubha Ghadiyalu and "
        "Durmuhurtham -- the auspicious and inauspicious time windows "
        "from authentic Telugu Panchangam, updated every single day. "
        "Know exactly when to start something important and when to "
        "avoid it, plus that day's ruling deity mantra. New video every "
        "night -- subscribe so you never miss today's timings.\n\n"
        "#TeluguPanchangam #RahuKalam #DailyMuhurtham #MahanaviSpirituals",
    ),
    (
        "gita_sloka",
        "Bhagavad Gita Sloka & Quiz",
        "ప్రతి రెండు రోజులకు ఒక కొత్త భగవద్గీత శ్లోకం దాని తెలుగు అర్థంతో "
        "నేర్చుకోండి, తర్వాతి రోజు అదే శ్లోకంపై క్విజ్‌లో పాల్గొని మీ "
        "జ్ఞాపకశక్తిని పరీక్షించుకోండి.\n\n"
        "Learn one Bhagavad Gita verse every other day -- Sanskrit "
        "chant, Telugu meaning, chapter and verse reference -- then "
        "test what you remember with a 4-option quiz the following "
        "day. A slow, steady way to work through Krishna's teachings "
        "to Arjuna on the field of Kurukshetra, one verse at a time. "
        "Subscribe to join the Bhagavad Gita quiz series.\n\n"
        "#BhagavadGita #GitaSloka #KrishnaTeachings #MahanaviSpirituals",
    ),
    (
        "puranas",
        "Purana Stories & Concepts",
        "పురాణాల నుండి స్ఫూర్తిదాయక కథలు మరియు ముఖ్యమైన భావనలు ఒక నిమిషం "
        "లోపే తెలుసుకోండి -- పదునెనిమిది పురాణాల్లోని నీతి కథలు, "
        "దేవతల లీలలు మరియు ధర్మసూక్ష్మాలు.\n\n"
        "Short, engaging stories and concepts drawn from the 18 Puranas "
        "of Hindu scripture -- divine leelas, moral tales and the ideas "
        "behind them, told simply enough to watch in under a minute. A "
        "new story or concept posted daily. Subscribe to keep exploring "
        "Puranic Hindu mythology with us.\n\n"
        "#PuranaStories #HinduMythology #TeluguDevotional #MahanaviSpirituals",
    ),
    (
        "rashi",
        "Rashi Mantras",
        "మీ రాశికి సంబంధించిన గ్రహ అధిపతి మంత్రాన్ని తెలుసుకోండి -- అన్ని "
        "12 రాశులకు వారి పాలక గ్రహం, మంత్రం మరియు పఠన విధానం ఇక్కడ "
        "ఉంటుంది.\n\n"
        "Ruling-planet mantras for all 12 rashis (zodiac signs) in the "
        "Vedic system -- find your rashi, learn its mantra, and chant "
        "along for its benefits. Rotates through all 12 signs one at a "
        "time. Comment your rashi below and subscribe for the next "
        "one.\n\n"
        "#RashiMantra #Astrology #VedicAstrology #MahanaviSpirituals",
    ),
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
            try:
                youtube.playlists().update(
                    part="snippet",
                    body={
                        "id": playlist_id,
                        "snippet": {"title": title, "description": description},
                    },
                ).execute()
                print(f"Already exists, description synced: \"{title}\" -> {playlist_id}")
            except HttpError as exc:
                print(f"Already exists but FAILED to sync description for \"{title}\": {exc}", file=sys.stderr)
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
