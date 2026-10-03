"""
token_health_check.py: confirms the saved YouTube API token still
works, and sends a Telegram alert immediately if it doesn't -- added
2026-10-03 (pipeline health review suggestion #4, "token-expiry risk
is a single point of failure").

WHY THIS MATTERS: every single posting script (all 5 series) shares
ONE saved OAuth token (data/youtube_token.json). If it expires or gets
revoked, every series stops posting AT ONCE, silently -- the failure
mode is identical everywhere ("YouTube API call failed"), so nothing
distinguishes it from, say, a one-off network blip unless someone is
actively watching. Combined with no alerting (suggestion #1, now
fixed separately), this was the single most likely way for the whole
channel to go quiet for days without the owner noticing.

Runs on its OWN daily schedule (see .github/workflows/
token-health-check.yml), BEFORE the first posting window of the day
(the night alert Shorts start at 12:00 AM IST), so a dead token is
caught and can be fixed before it actually costs a missed post --
rather than discovering it only when tonight's post fails.

Usage:
    python -m mahanavi.scripts.token_health_check
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.notifications.telegram_alert import send_telegram_alert
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader


def main() -> int:
    settings = get_settings()
    uploader = YouTubeShortsUploader(settings)

    ok, reason = uploader.check_token_health()
    if ok:
        print("YouTube token is healthy.")
        return 0

    print(f"YouTube token check FAILED: {reason}", file=sys.stderr)
    message = (
        "\U0001f6a8 Mahanavi Spirituals: YouTube token needs attention\n\n"
        f"Reason: {reason}\n\n"
        "Every series shares this one token, so ALL posting will stop until "
        "it's fixed. Re-run youtube_shorts_auth_setup.py locally, then push "
        "the refreshed data/youtube_token.json to Drive "
        "(python scripts/ci/drive_state_sync.py push)."
    )
    send_telegram_alert(message, settings)
    return 1


if __name__ == "__main__":
    sys.exit(main())
