"""
post_rashi_weekly.py: posts ONE weekly Rashi Mantra Short on Sunday (Sunday to Saturday week): all 12 rashis
on a single table card (rashi | mantra), the week's dates at the top, mantras chosen from that week's
planet positions (content/rashi_weekly.py). Replaces the old daily one-rashi rotation (2026-10-09).

Usage:
    python -m ytcore.scripts.post_rashi_weekly --dry-run     # render the card + video only
    python -m ytcore.scripts.post_rashi_weekly --public
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from ytcore.config import get_settings
from ytcore.content import rashi_weekly
from ytcore.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE, ShortSeoContent
from ytcore.content.branding import brand_tagline
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import UploadLogRepository
from ytcore.exceptions import AppError
from ytcore.images.rashi_weekly_card_renderer import RashiWeeklyCardRenderer, WeeklyCard
from ytcore.publishers.blogger_publisher import post_to_blogger
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.assembler import (
    LOOP_FRIENDLY_FADE_IN_SECONDS,
    LOOP_FRIENDLY_FADE_OUT_SECONDS,
    assemble_short,
)

WEEKLY_SECONDS = 5.0  # owner request 2026-10-11: the weekly Rashi table Short must be only 5 seconds


def build_seo(date_text: str, rows: list[dict]) -> ShortSeoContent:
    lines_te = [f"{r['name']} ({r['name_en']}): {r['mantra']}" for r in rows]
    title = f"ఈ వారం రాశి మంత్రాలు ({date_text}) | Weekly Rashi Mantra"
    if len(title) > 100:
        title = f"ఈ వారం రాశి మంత్రాలు | Weekly Rashi Mantra All 12 Rashis ({date_text})"[:100]
    description = (
        f"{brand_tagline('rashi_mantra')}\n\n"
        f"ఈ వారం ({date_text}) మీ రాశికి సూచించిన మంత్రం:\n\n" + "\n".join(lines_te) +
        "\n\nప్రతి మంత్రం 108 సార్లు చదువుకోండి. గ్రహ స్థితిని బట్టి ప్రతి ఆదివారం కొత్త మంత్రాలు వస్తాయి."
        "\n\nఈ వీడియోపై మీ అభిప్రాయం కామెంట్ చేయండి, ప్రతి ఆదివారం కోసం సబ్‌స్క్రైబ్ చేయండి."
        f"\n\n{_CHANNEL_FOOTER_TE}\n\n---\n\n"
        f"Weekly Rashi (zodiac) mantras for {date_text}, chosen from this week's planetary positions "
        "(traditional Vedic gochara). Chant your rashi's mantra 108 times. New table every Sunday.\n\n"
        + "\n".join(f"{r['name_en']}: {r['mantra']} ({r['planet']})" for r in rows) + f"\n\n{_CHANNEL_FOOTER_EN}"
    )
    hashtags = ["#Shorts", "#రాశిఫలాలు", "#WeeklyRashi", "#RashiMantra", "#జాతకం", "#Devotional"]
    return ShortSeoContent(title=title, description=description, hashtags=hashtags)


def build_comment(date_text: str, rows: list[dict]) -> str:
    return f"{date_text} రాశి మంత్రాలు:\n" + "\n".join(f"{r['name']}: {r['mantra']}" for r in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Render card + video only; no upload.")
    parser.add_argument("--date", help="Use the week containing this ISO date (default: today IST).")
    args = parser.parse_args(argv)

    settings = get_settings()
    today = (datetime.fromisoformat(args.date).date() if args.date
             else datetime.now(ZoneInfo(settings.timezone)).date())
    start = rashi_weekly.week_start(today)
    date_text = rashi_weekly.date_range_text(start, "te")
    rows = rashi_weekly.weekly_rows(start, "te")
    print(f"Weekly Rashi table for {date_text}: " + ", ".join(f"{r['name_en']}={r['planet']}" for r in rows))

    try:
        image = RashiWeeklyCardRenderer(settings).render(WeeklyCard(date_text=date_text, rows=rows, lang="te"))
        video = settings.output_dir / f"{start.isoformat()}_rashi_weekly_short.mp4"
        assemble_short(
            image, video, duration_seconds=WEEKLY_SECONDS, audio_path=settings.alert_short_music_path,
            fade_in_seconds=LOOP_FRIENDLY_FADE_IN_SECONDS, fade_out_seconds=LOOP_FRIENDLY_FADE_OUT_SECONDS,
        )
        print(f"Assembled: {video}")
        if args.dry_run:
            return 0

        seo = build_seo(date_text, rows)
        uploader = YouTubeShortsUploader(settings)
        privacy = "public" if args.public else "unlisted"
        result = uploader.upload(video, seo, privacy_status=privacy)
        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1
        print(f"Uploaded ({privacy}): {result.post_url}")
        if result.video_id:
            if uploader.post_comment(result.video_id, build_comment(date_text, rows)):
                print("Posted the table as the first comment.")
            UploadLogRepository(DatabaseManager(settings.database_path)).log_upload(
                result.video_id, "rashi", seo.title, today)
            if settings.playlist_id_rashi and uploader.add_to_playlist(result.video_id, settings.playlist_id_rashi):
                print("Added to playlist.")
            if post_to_blogger(settings, result.video_id, seo.title, seo.full_caption()):
                print("Posted to Blogger.")
        return 0
    except AppError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
