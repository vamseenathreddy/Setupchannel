"""
One-time OAuth2 setup for uploading Shorts via the official YouTube Data
API v3 -- separate from scripts/youtube_login_setup.py (which sets up
the Playwright browser session used for Community Posts; Community
Posts have no official API at all, which is why that one exists).

Run this ONCE. It prints a Google sign-in/permission-grant URL for you
to paste into a browser yourself (see open_browser=False note below),
then saves a reusable refresh token to disk -- every future run reuses
that token silently, no browser needed again unless the token is
revoked or deleted.

Usage:
    python -m ytcore.scripts.youtube_shorts_auth_setup
    python -m ytcore.scripts.youtube_shorts_auth_setup --token-file data/youtube_token_ramana.json

Prerequisite: client_secrets.json downloaded from Google Cloud Console
(APIs & Services -> Credentials -> OAuth client ID -> Desktop app),
placed at the path in MAHANAVI_YOUTUBE_CLIENT_SECRETS_FILE (defaults to
the project root).

--token-file: added 2026-10 for second (and later) YouTube channels in
this repo (e.g. Channel D) that reuse this SAME Google Cloud
OAuth project/client_secrets.json but need their OWN saved token,
since each channel is authorized separately. Omit it for the original
channel (Channel A) -- defaults to
settings.youtube_token_file exactly as before this change. At the
Google consent screen, choose the YouTube channel this new token
should act as (the "choose an account" / channel picker Google shows
when a Google account manages more than one channel).
"""

from __future__ import annotations

from ytcore.brandcfg import A_NAME

import argparse
import sys
from pathlib import Path

from ytcore.config import get_settings

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
# post to Blogger with this SAME token, REMOVED again 2026-10-07 after
# it broke Brand Account channel selection: every re-auth done while
# this scope was present (including a re-auth of the original
# data/youtube_token.json meant to FIX a wrong-channel upload) landed
# on the signed-in Gmail's own default/personal channel instead of the
# Channel A Brand Account, confirmed via YouTube Studio
# showing "Revathy Vsl" as the uploading channel. Mixing a
# non-YouTube, account-level scope (blogger has no Brand Account
# concept) into the same consent grant as the YouTube scopes appears
# to suppress Google's Brand Account channel picker for the whole
# grant. blogger_publisher.post_to_blogger() already treats a missing
# scope as a soft failure (HttpError caught, logged, returns False --
# see that module's docstring), so removing this scope here just
# turns automatic Blogger cross-posting back off; it does not need any
# other code change and does not affect YouTube uploads/comments/
# playlists/analytics, which only ever needed the two scopes below.
# If Blogger cross-posting is wanted again later, it needs its own,
# separate OAuth token/consent run (never mixed into this one), so a
# non-YouTube scope can never again interfere with picking the right
# YouTube channel.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
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

    print(
        "This will NOT open a browser automatically -- it will print a URL below. "
        "Copy it and paste it yourself into the exact browser window/tab you want "
        "to sign in with (e.g. a fresh Incognito window)."
    )
    print(
        "IMPORTANT: when Google shows the account/channel picker, pick the correct "
        "Brand Account channel for THIS token -- not your personal Gmail channel."
    )
    flow = InstalledAppFlow.from_client_secrets_file(str(settings.youtube_client_secrets_file), SCOPES)
    # prompt="consent select_account" -- force Google to always re-show the
    # account chooser (never silently reuse a cached browser session), so the
    # Brand Account picker above is never skipped. Added 2026-10-07 alongside
    # the blogger-scope removal above, as part of the same wrong-channel fix.
    #
    # open_browser=False -- added 2026-10-07 after google_auth_oauthlib's
    # automatic browser launch kept opening a NEW regular (non-Incognito)
    # browser window/tab for the auth URL, overriding whatever
    # Incognito/already-signed-in-as-the-right-account browser window the
    # user had deliberately prepared. With this off, the script only PRINTS
    # the URL and never launches anything itself -- the user pastes it into
    # the exact browser window/session they want.
    credentials = flow.run_local_server(port=0, prompt="consent select_account", open_browser=False)

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json(), encoding="utf-8")

    print(f"Success. Token saved to {token_file}")
    print("Future uploads will reuse this token silently -- no browser needed again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
