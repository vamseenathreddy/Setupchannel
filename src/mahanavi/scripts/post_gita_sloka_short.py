"""
post_gita_sloka_short.py: posts ONE "Bhagavad Gita Sloka" Short per run,
cycling through content/bhagavad_gita_slokas.py's GITA_SLOKAS via a
persisted rotation index -- same one-per-run rotation design as the
other series on this channel.

Flow: read the rotation state (data/last_gita_sloka_index.txt, default 0
if missing/first run) -> pick that verse -> render it as one static card
(GitaSlokaCardRenderer.render() -- Sanskrit verse + Telugu meaning,
auto-fit, static Krishna-Arjuna chariot watermark, no rotation layers
needed for this series) -> assemble into a .mp4 via the plain
video/assembler.assemble_short() (loop-friendly, no fades) -> build SEO
(gita_sloka_seo.py) -> upload -> advance the rotation index (wraps back
to 0 after the last verse), UNLESS --sloka was used to force a specific
one.

CONTENT SCOPE: GITA_SLOKAS currently holds 11 well-known, verified
verses (phase 1 -- see that module's docstring). More verses get added
over time; this script doesn't need to change as the list grows.

POSTING TIME: 3-4 PM IST (scripts/ci/gita_sloka_gate.py).

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m mahanavi.scripts.post_gita_sloka_short
    python -m mahanavi.scripts.post_gita_sloka_short --public
    python -m mahanavi.scripts.post_gita_sloka_short --sloka 0       # force by index
    python -m mahanavi.scripts.post_gita_sloka_short --sloka 2.47    # force by "chapter.verse"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.bhagavad_gita_slokas import GITA_SLOKAS, GitaSloka
from mahanavi.content.gita_sloka_seo import build_gita_sloka_seo
from mahanavi.exceptions import MahanaviError
from mahanavi.images.gita_sloka_card_renderer import GitaSlokaCard, GitaSlokaCardRenderer
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import assemble_short

STATE_FILE = Path("data") / "last_gita_sloka_index.txt"


def _icon_paths(settings: Settings) -> list[Path]:
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
        return int(STATE_FILE.read_text().strip()) % len(GITA_SLOKAS)
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable content, starting rotation at sloka 0.")
        return 0


def _write_rotation_index(next_index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(next_index % len(GITA_SLOKAS)))


def _resolve_forced_sloka(spec: str) -> int:
    """--sloka accepts a plain index, or "chapter.verse" (e.g. "2.47")."""
    spec = spec.strip()
    if spec.isdigit():
        index = int(spec)
        if not (0 <= index < len(GITA_SLOKAS)):
            raise MahanaviError(f"--sloka index must be 0-{len(GITA_SLOKAS) - 1}, got {index}")
        return index
    if "." in spec:
        try:
            chapter_s, verse_s = spec.split(".", 1)
            chapter, verse = int(chapter_s), int(verse_s)
        except ValueError as exc:
            raise MahanaviError(f"--sloka '{spec}' is not a valid index or 'chapter.verse'") from exc
        matches = [i for i, s in enumerate(GITA_SLOKAS) if s.chapter == chapter and s.verse == verse]
        if matches:
            return matches[0]
        raise MahanaviError(
            f"--sloka '{spec}' did not match any verse currently in content/bhagavad_gita_slokas.py. "
            f"Available: {', '.join(f'{s.chapter}.{s.verse}' for s in GITA_SLOKAS)}"
        )
    raise MahanaviError(f"--sloka '{spec}' is not a valid index or 'chapter.verse'")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the result yourself.",
    )
    parser.add_argument(
        "--sloka", type=str, default=None,
        help="Force a specific verse instead of the next one in rotation (index, or 'chapter.verse' "
             "like '2.47'). A forced run does NOT advance the stored rotation state.",
    )
    args = parser.parse_args()

    settings = get_settings()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    forced = args.sloka is not None
    try:
        sloka_index = _resolve_forced_sloka(args.sloka) if forced else _read_rotation_index()
    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    sloka: GitaSloka = GITA_SLOKAS[sloka_index]
    print(f"Posting sloka {sloka_index} ({sloka.chapter}.{sloka.verse}){' [FORCED]' if forced else ''}")

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    try:
        card = GitaSlokaCard(sloka=sloka, icon_paths=_icon_paths(settings))
        renderer = GitaSlokaCardRenderer(settings)
        image_path = renderer.render(card)
        print(f"Rendered card: {image_path}")

        video_path = settings.output_dir / f"{today.isoformat()}_gita_{sloka.chapter}_{sloka.verse}_short.mp4"
        assemble_short(
            image_path=image_path,
            output_path=video_path,
            duration_seconds=settings.gita_sloka_short_duration_seconds,
            audio_path=settings.alert_short_music_path,
            fade_in_seconds=0.0,
            fade_out_seconds=0.0,
        )
        print(f"Assembled (loop-friendly, {settings.gita_sloka_short_duration_seconds}s, no fades): {video_path}")

        seo = build_gita_sloka_seo(sloka, sloka_index, today.toordinal())
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        if not forced:
            next_index = (sloka_index + 1) % len(GITA_SLOKAS)
            _write_rotation_index(next_index)
            next_sloka = GITA_SLOKAS[next_index]
            print(f"Rotation advanced: next run will post sloka {next_index} ({next_sloka.chapter}.{next_sloka.verse})")
        else:
            print("Forced run -- rotation state left unchanged.")

        return 0

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
