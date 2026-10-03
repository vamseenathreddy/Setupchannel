#!/usr/bin/env python3
"""
notify_failure.py: sends a Telegram alert when a GitHub Actions
workflow run fails -- added 2026-10-03 (pipeline health review
suggestion #1, "No failure alerting"). Added as a final
`if: failure()` step in every posting workflow (see
.github/workflows/*.yml), so a broken run (expired YouTube token,
Panchang API down, a bad deploy, anything) reaches the channel owner's
phone within seconds instead of only being noticed days later as a gap
on the channel.

Deliberately STDLIB-ONLY (urllib, not `requests`) and does NOT import
the `mahanavi` package or read .env -- this step can run even when an
earlier step in the SAME failing job never got as far as `pip
install`, so it can't depend on either. Reads its two secrets straight
from the environment (passed as `env:` in the workflow step, sourced
from GitHub Actions repo secrets TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
-- note the workflow-level env var names have no MAHANAVI_ prefix,
unlike the application's own Settings fields, since this script never
goes through pydantic Settings at all).

Usage (as wired into each workflow):
    python scripts/ci/notify_failure.py "Daily Shorts Post"

Silently no-ops (exit 0) if the secrets aren't configured yet, so
adding this step to every workflow today doesn't break anything before
the user has actually created a bot -- see
src/mahanavi/notifications/telegram_alert.py for the one-time setup.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    workflow_name = sys.argv[1] if len(sys.argv) > 1 else "A Mahanavi Spirituals workflow"

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not bot_token or not chat_id:
        print("notify_failure: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set -- skipping alert.")
        return 0

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else ""

    message = f"⚠️ {workflow_name} FAILED\n\n" + (f"Logs: {run_url}" if run_url else "")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": message, "disable_web_page_preview": True}).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read()
        print("notify_failure: Telegram alert sent.")
    except urllib.error.URLError as exc:
        # Never fail the workflow over a failed ALERT about a failure --
        # that would just mask the original error in a confusing way.
        print(f"notify_failure: could not send Telegram alert: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
