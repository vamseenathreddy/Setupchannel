"""
One-time OAuth2 setup for uploading Shorts via the official YouTube Data
API v3 -- separate from scripts/youtube_login_setup.py (which sets up
the Playwright browser session used for Community Posts; Community
Posts have no official API at all, which is why that one exists).

Run this ONCE. It opens a real browser window for you to log into your
Google account and grant upload permission, then saves a reusable
refresh token to disk -- every future run reuses that token silently,
no browser needed again unless the token is revoked or deleted.

Usage:
    python -m mahanavi.scripts.youtube_shorts_auth_setup
    python -m mahanavi.scripts.youtube_shorts_auth_setup --token-file data/youtube_token_ramana.json

Prerequisite: client_secrets.json downloaded from Google Cloud Console
(APIs & Services -> Credentials -> OAuth client ID -> Desktop app),
placed at the path in MAHANAVI_YOUTUBE_CLIENT_SECRETS_FILE (defaults to
the project root).

--token-file: added 2026-10 for second (and later) YouTube channels in
this repo (e.g. Ramana Maharshi TV) that reuse this SAME Google Cloud
OAuth project/client_secrets.json but need their OWN saved token,
since each channel is authorized separately. Omit it for the original
channel (mahanavi spirituals) -- defaults to
settings.youtube_token_file exactly as before this change. At the
Google consent screen, choose the YouTube channel this new token
should act as (the "choose an account" / channel picker Google shows
when a Google account manages more than one channel).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mahanavi.config import get_settings

# youtube.force-ssl (not just youtube.upload) -- the Purana Concept
# Shorts series (post_concept_short.py) needs commentThreads.insert as
# well as video upload, per explicit request (2026-10-02: "put it in
# comment section while posting"). youtube.force-ssl is the scope that
# covers both upload and comments (and playlists -- see
# YouTubeShortsUploader.add_to_playlist); a token saved under the
# narrower youtube.upload (from before this change) does NOT get
# upgraded by itself -- re-run this script once to get a fresh token
# with the broader scope, then push the refreshed
# data/youtube_token.json to Drive (python scripts/ci/drive_state_sync.py
# push) so CI picks it up.
#
# yt-analytics.readonly -- added 2026-10-03 for
# weekly_performance_report.py (pipeline health review suggestion #3).
# A token saved before this change doesn't have it either; same
# one-time re-run-this-script-then-push-to-Drive fix applies.
#
# blogger -- added 2026-10-06 to let publishers/blogger_publisher.py
# post to Blogger with this SAME token (same Google account owns both
# the YouTube channel and the blog), replacing a broken IFTTT applet
# that posted images as literal unresolved template text instead of a
# real thumbnail URL. Same one-time re-run-this-script-then-push-to-
# Drive fix applies to tokens saved before this change.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/blogger",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--token-file",
        default=None,
        help="Where to save the token (default: settings.youtube_token_file, i.e. the main channel).",
    )
    args = ap.parse_args()

    settings = get_settings()
    token_file = Path(args.token_file) if args.token_file else settings.youtube_token_file

    if not settings.youtube_client_secrets_file or not settings.youtube_client_secrets_file.exists():
        print(
            f"client_secrets.json not found at {settings.youtube_client_secrets_file}. "
            "Download it from Google Cloud Console (APIs & Services -> Credentials -> "
            "OAuth client ID -> Desktop app) and place it there, or set "
            "MAHANAVI_YOUTUBE_CLIENT_SECRETS_FILE to its actual path.",
            file=sys.stderr,
        )
        return 1

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "Missing packages. Run: pip install google-api-python-client google-auth-oauthlib google-auth",
            file=sys.stderr,
        )
        return 1

    print("Opening a browser window for Google sign-in and permission grant...")
    flow = InstalledAppFlow.from_client_secrets_file(str(settings.youtube_client_secrets_file), SCOPES)
    credentials = flow.run_local_server(port=0)

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json(), encoding="utf-8")

    print(f"Success. Token saved to {token_file}")
    print("Future uploads will reuse this token silently -- no browser needed again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
