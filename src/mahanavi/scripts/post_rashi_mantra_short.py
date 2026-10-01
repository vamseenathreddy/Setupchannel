"""
post_rashi_mantra_short.py: posts ONE Rashi Mantra Short per run, cycling
through all 12 rashis in order (Mesha first) via a persisted rotation
index -- NOT all 12 at once. Posting all 12 in a single run would flood
subscribers' feeds at once and dilute each video's individual loop/replay
performance; spacing them out (one per manual trigger) is the explicit
design (2026-10-01).

Flow: read the rotation state (data/last_rashi_index.txt, default 0 if
missing/first run) -> pick that rashi from RASHI_MANTRAS -> render its
static card (RashiCardRenderer -- a held STILL frame, never scrolling
text, per explicit requirement distinguishing this series from
post_kamakhya_short.py's animated scroll) -> assemble into a .mp4 with
NO fade-in/fade-out (LOOP_FRIENDLY_FADE_*_SECONDS, both 0.0) at a
duration shorter than a comfortable full read (settings.
rashi_mantra_short_duration_seconds, 8s default) so viewers loop 2-3x to
finish reading and the loop itself is invisible -> build SEO
(rashi_mantra_seo.py) -> upload -> advance the rotation index (wraps
back to 0/Mesha after rashi 11/Meena) and persist it, UNLESS --rashi
was used to force a specific one (a forced run is a deliberate one-off
re-post / test, so it does NOT disturb where the natural rotation is).

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m mahanavi.scripts.post_rashi_mantra_short
    python -m mahanavi.scripts.post_rashi_mantra_short --public
    python -m mahanavi.scripts.post_rashi_mantra_short --rashi 0        # force Mesha by index
    python -m mahanavi.scripts.post_rashi_mantra_short --rashi Simha    # force by name (English, case-insensitive substring)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.rashi_current_transits import AFFECTED_RASHIS
from mahanavi.content.rashi_mantra_content import RASHI_MANTRAS, RashiMantraContent
from mahanavi.content.rashi_mantra_seo import build_rashi_mantra_seo
from mahanavi.exceptions import MahanaviError
from mahanavi.images.rashi_card_renderer import RashiCard, RashiCardRenderer
from mahanavi.images.telugu_text import TELUGU_MONTHS
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import (
    LOOP_FRIENDLY_FADE_IN_SECONDS,
    LOOP_FRIENDLY_FADE_OUT_SECONDS,
    assemble_short,
)

STATE_FILE = Path("data") / "last_rashi_index.txt"

# Short, generic comment prompt shown on the card itself -- distinct from
# (but consistent with) the longer engagement text in the description
# built by rashi_mantra_seo.py.
COMMENT_PROMPT_TEXT = "మీ రాశి కామెంట్‌లో చెప్పండి!"


def _icon_paths(settings: Settings) -> list[Path]:
    """Lakshmi, Ganesha, Kubera -- same three deity icons already used on
    the alert cards (post_alert_shorts.py's _icon_paths), reused here per
    the explicit request to show them on the Rashi Mantra card too. Only
    the ones that actually exist on disk are included."""
    candidates = [
        ("Lakshmi", settings.alert_icon_lakshmi_path),
        ("Ganesha", settings.alert_icon_ganesha_path),
        ("Kubera", settings.alert_icon_kubera_path),
    ]
    paths: list[Path] = []
    for name, path in candidates:
        if path is not None and path.exists():
            paths.append(path)
        else:
            print(f"Note: {name} icon not found at {path} -- card will render without it.")
    return paths


def _read_rotation_index() -> int:
    if not STATE_FILE.exists():
        return 0
    try:
        return int(STATE_FILE.read_text().strip()) % len(RASHI_MANTRAS)
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable content, starting rotation at Mesha (0).")
        return 0


def _write_rotation_index(next_index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(next_index % len(RASHI_MANTRAS)))


def _resolve_forced_rashi(spec: str) -> int:
    """--rashi accepts either a plain index ("0"-"11") or a case-insensitive
    substring match against name_en (e.g. "simha" matches "Simha (Leo)")."""
    if spec.strip().isdigit():
        index = int(spec.strip())
        if not (0 <= index < len(RASHI_MANTRAS)):
            raise MahanaviError(f"--rashi index must be 0-{len(RASHI_MANTRAS) - 1}, got {index}")
        return index
    needle = spec.strip().lower()
    matches = [i for i, c in enumerate(RASHI_MANTRAS) if needle in c.name_en.lower()]
    if not matches:
        raise MahanaviError(
            f"--rashi '{spec}' did not match any rashi name_en. "
            f"Valid names: {', '.join(c.name_en for c in RASHI_MANTRAS)}"
        )
    if len(matches) > 1:
        raise MahanaviError(f"--rashi '{spec}' matched more than one rashi: {matches}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the result yourself.",
    )
    parser.add_argument(
        "--rashi", type=str, default=None,
        help="Force a specific rashi instead of the next one in rotation (index 0-11, or a name "
             "substring like 'Simha'). A forced run does NOT advance or disturb the stored rotation "
             "state -- it's a one-off re-post/test, not a change to where the natural cycle is.",
    )
    args = parser.parse_args()

    settings = get_settings()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    forced = args.rashi is not None
    try:
        rashi_index = _resolve_forced_rashi(args.rashi) if forced else _read_rotation_index()
    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    content: RashiMantraContent = RASHI_MANTRAS[rashi_index]
    transit = AFFECTED_RASHIS.get(content.name_en)
    print(f"Posting rashi {rashi_index} ({content.name_en}){' [FORCED]' if forced else ''}"
          f"{' -- Shani transit note active' if transit else ''}")

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()
    date_text = f"{TELUGU_MONTHS[today.month]} {today.year} మాసం"

    try:
        card = RashiCard(
            content=content,
            rashi_index=rashi_index,
            date_text=date_text,
            comment_prompt_text=COMMENT_PROMPT_TEXT,
            icon_paths=_icon_paths(settings),
        )
        renderer = RashiCardRenderer(settings)
        image_path = renderer.render(card)
        print(f"Rendered: {image_path}")

        video_path = settings.output_dir / f"{today.isoformat()}_rashi_{content.name_en.split(' ')[0].lower()}_short.mp4"
        assemble_short(
            image_path, video_path,
            duration_seconds=settings.rashi_mantra_short_duration_seconds,
            audio_path=settings.alert_short_music_path,
            fade_in_seconds=LOOP_FRIENDLY_FADE_IN_SECONDS,
            fade_out_seconds=LOOP_FRIENDLY_FADE_OUT_SECONDS,
        )
        print(f"Assembled (loop-friendly, {settings.rashi_mantra_short_duration_seconds}s, no fades): {video_path}")

        seo = build_rashi_mantra_seo(content, rashi_index, today.toordinal(), transit)
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        if not forced:
            next_index = (rashi_index + 1) % len(RASHI_MANTRAS)
            _write_rotation_index(next_index)
            print(f"Rotation advanced: next run will post rashi {next_index} ({RASHI_MANTRAS[next_index].name_en})")
        else:
            print("Forced run -- rotation state left unchanged.")

        return 0

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
