"""
post_beej_mantra.py: the daily 6 AM beej mantra Short for one channel (content/beej_mantras.py picks the
deity from festival / tithi / weekday). Runs after the gate; marks today's slot in STATE_FILE (beej_state.json).

Usage:
    python -m mahanavi.scripts.post_beej_mantra --channel mahanavi --dry-run
    POST_SLOT=mahanavi STATE_FILE=data/beej_state.json python -m mahanavi.scripts.post_beej_mantra --channel mahanavi --public
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from channels.engine import state as state_mod
from mahanavi.config import PROJECT_ROOT, get_settings
from mahanavi.content import beej_mantras
from mahanavi.exceptions import MahanaviError, YouTubeUploadError
from mahanavi.images.request_card_renderer import RequestCardRenderer
from mahanavi.panchang.local_provider import HYDERABAD, LocalPanchangProvider
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.scripts.post_request_short import assemble, upload

IST = ZoneInfo("Asia/Kolkata")
MUSIC_DIRS = {
    "mantra_sangam": (PROJECT_ROOT / "channels" / "mantra_sangam" / "assets" / "music", "om_*.mp3"),
    "trance_beats": (PROJECT_ROOT / "channels" / "trance_beats" / "assets" / "music" / "approved", "*.mp3"),
}


def music_for(channel: str, d: dt.date, default: Path | None) -> Path:
    if channel in MUSIC_DIRS:
        folder, pattern = MUSIC_DIRS[channel]
        files = sorted(folder.glob(pattern))
        if files:
            return files[d.toordinal() % len(files)]
    if default is None or not default.exists():
        raise MahanaviError(f"Music file missing: {default}")
    return default


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", required=True, choices=sorted(beej_mantras.CHANNELS))
    ap.add_argument("--public", action="store_true", help="Upload public (default unlisted).")
    ap.add_argument("--dry-run", action="store_true", help="Render slides + video only; no upload.")
    ap.add_argument("--date", default="", help="ISO date override (testing).")
    args = ap.parse_args(argv)

    settings = get_settings()
    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(IST).date()
    try:
        tithi = LocalPanchangProvider(*HYDERABAD).fetch(today).tithi
        spec = beej_mantras.build(args.channel, today, tithi)
        print(f"{today} tithi={tithi} -> {spec.deity_te}")
        out_dir = settings.output_dir / "beej" / spec.slug
        slides = RequestCardRenderer(settings).render_all(spec, out_dir)
        music = music_for(args.channel, today, settings.alert_short_music_path)
        video = assemble(spec, [s.path for s in slides], music, out_dir / f"{spec.slug}.mp4")
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
