"""
telegram_alert.py: sends a plain-text alert to the channel owner's
Telegram via the Bot API -- the whole point is a push notification that
reaches a phone within seconds, unlike an email that might sit unread
or a GitHub Actions run someone has to remember to check.

Added 2026-10-03 as suggestion #1 ("No failure alerting") from a
pipeline health review: previously nothing told the owner when a
workflow failed (expired token, Panchang API down, cron-job.org
dispatch not landing, etc.) -- the only way to notice was seeing a gap
on the channel days later. This module is the shared primitive used by:
  - scripts/ci/notify_failure.py (generic "this workflow run failed")
  - token_health_check.py (specific "your YouTube token needs re-auth")
  - weekly_performance_report.py (the weekly summary itself)

WHY TELEGRAM over email: no SMTP server/app-password setup, a free bot
takes ~2 minutes to create via @BotFather, and delivery is an instant
phone push -- the best fit for "I need to know THIS, right now" alerts.

SETUP (one-time, by the channel owner -- cannot be done from here):
  1. Open Telegram, message @BotFather, send /newbot, follow the
     prompts -- you get back a bot token (looks like
     123456789:AAtsomeLongRandomString).
  2. Message your new bot anything (e.g. "hi") so it's allowed to
     message you back.
  3. Visit https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates in a
     browser right after step 2 -- your numeric chat id is in the
     JSON response under result[0].message.chat.id.
  4. Add both as GitHub Actions repo secrets: TELEGRAM_BOT_TOKEN and
     TELEGRAM_CHAT_ID (Settings -> Secrets and variables -> Actions),
     and set MAHANAVI_TELEGRAM_BOT_TOKEN / MAHANAVI_TELEGRAM_CHAT_ID in
     your local .env for testing.

Fails silently (logs a warning, returns False) rather than raising --
an alert channel going down must never be what breaks the actual
posting pipeline it's there to protect.
"""

from __future__ import annotations

import logging

from mahanavi.config import Settings

logger = logging.getLogger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org"


def send_telegram_alert(message: str, settings: Settings) -> bool:
    """Sends `message` to settings.telegram_chat_id via the bot at
    settings.telegram_bot_token. Returns False (without raising) if
    either is unset, the `requests` package is missing, or the HTTP
    call itself fails -- callers should treat this as best-effort."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning(
            "Telegram alert skipped -- MAHANAVI_TELEGRAM_BOT_TOKEN / "
            "MAHANAVI_TELEGRAM_CHAT_ID not configured."
        )
        return False

    try:
        import requests
    except ImportError:
        logger.warning("Telegram alert skipped -- the 'requests' package is not installed.")
        return False

    url = f"{_TELEGRAM_API_BASE}/bot{settings.telegram_bot_token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        response.raise_for_status()
        return True
    except Exception as exc:  # genuinely any requests/network failure is non-fatal here
        logger.warning("Telegram alert failed to send: %s", exc)
        return False
