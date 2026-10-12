"""
post_motivation_word.py: the daily 9 PM "Purana motivation word" Short for Mahanavi (2 seconds).
content/motivation_words.py picks the word from the date. Runs after channels/motivation/gate.py.

Usage:
    python -m mahanavi.scripts.post_motivation_word --dry-run
    POST_SLOT=motivation STATE_FILE=data/beej_state.json python -m mahanavi.scripts.post_motivation_word --public
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from zoneinfo import ZoneInfo

from channels.engine import state as state_mod
from mahanavi.config import get_settings
from mahanavi.content import motivation_words
from mahanavi.exceptions import MahanaviError, YouTubeUploadError
from mahanavi.images.motivation_card_renderer import MotivationCardRenderer
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.scripts.post_beej_mantra import music_for
from mahanavi.scripts.post_request_short import assemble, upload

IST = ZoneInfo("Asia/Kolkata")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--public", action="store_true", help="Upload public (default unlisted).")
    ap.add_argument("--dry-run", action="store_true", help="Render slide + video only; no upload.")
    ap.add_argument("--date", default="", help="ISO date override (testing).")
    args = ap.parse_args(argv)

    settings = get_settings()
    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(IST).date()
    try:
        spec = motivation_words.build(today)
        print(f"{today} -> {spec.deity_te}")
        out_dir = settings.output_dir / "motivation" / spec.slug
        w = motivation_words.pick(today)
        png = MotivationCardRenderer(settings).render(
            photo_path=motivation_words.image_for(today, w), label="నేటి పురాణ ప్రేరణ", word=w.word, reason=w.reason,
            source=w.source, invocation=motivation_words.INVOCATION.get(w.deity, "ఓం నమో నారాయణాయ"),
            header=spec.header, footer=spec.tag_footer, watermark=spec.watermark, out=out_dir / "card.png")
        music = music_for("mahanavi", today, settings.alert_short_music_path)
        video = assemble(spec, [png], music, out_dir / f"{spec.slug}.mp4")
        print(f"Assembled: {video} ({spec.total_seconds:.1f}s)")
        if args.dry_run:
            return 0

        youtube = YouTubeShortsUploader(settings)._build_service()  # noqa: SLF001
        got = youtube.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
        if spec.expected_channel.lower() not in got.lower():
            raise MahanaviError(f"NOT posting: the token acts as channel '{got}', expected '{spec.expected_channel}'.")
        video_id = upload(youtube, spec, video, "public" if args.public else "unlisted")
        print(f"Channel: {got}\nUploaded: https://www.youtube.com/watch?v={video_id}")
        state = state_mod.load()
        state_mod.mark_posted(state, today.isoformat(), spec.slug, video_id, True, dt.datetime.now(IST).isoformat())
        state_mod.save(state)
        return 0
    except (MahanaviError, YouTubeUploadError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # googleapiclient HttpError etc.
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
