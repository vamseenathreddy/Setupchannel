"""
post_purana_short.py: posts ONE "Purana Story" Short per run, cycling
through content/purana_short_stories.py's PURANA_SHORT_STORIES in order
via a persisted rotation index -- same one-per-run rotation design as
post_rashi_mantra_short.py, not all of them at once (would flood
subscribers' feeds and dilute each video's individual loop/replay
performance).

Flow: read the rotation state (data/last_purana_short_index.txt,
default 0 if missing/first run) -> pick that story -> render its static
card (PuranaShortCardRenderer -- a held STILL frame with auto-fit text,
never scrolling, never narrated, per explicit requirement) -> assemble
into a .mp4 with NO fade-in/fade-out (LOOP_FRIENDLY_FADE_*_SECONDS, both
0.0) at a duration shorter than a comfortable full read (settings.
purana_short_duration_seconds, 12s default) so viewers loop 2-3x to
finish reading -> build SEO (purana_short_seo.py) -> upload -> advance
the rotation index (wraps back to 0 after the last story), UNLESS
--story was used to force a specific one (a forced run is a deliberate
one-off re-post/test, so it does NOT disturb where the natural rotation
is).

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m mahanavi.scripts.post_purana_short
    python -m mahanavi.scripts.post_purana_short --public
    python -m mahanavi.scripts.post_purana_short --story 0            # force by index
    python -m mahanavi.scripts.post_purana_short --story Gajendra     # force by title_en substring
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.purana_short_seo import build_purana_short_seo
from mahanavi.content.purana_short_stories import PURANA_SHORT_STORIES, PuranaShortStory
from mahanavi.exceptions import MahanaviError
from mahanavi.images.purana_short_card_renderer import PuranaShortCard, PuranaShortCardRenderer
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import (
    LOOP_FRIENDLY_FADE_IN_SECONDS,
    LOOP_FRIENDLY_FADE_OUT_SECONDS,
    assemble_short,
)

STATE_FILE = Path("data") / "last_purana_short_index.txt"


def _icon_paths(settings: Settings) -> list[Path]:
    """Same three deity icons already used on the alert and rashi cards,
    reused here for a single consistent channel identity."""
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
        return int(STATE_FILE.read_text().strip()) % len(PURANA_SHORT_STORIES)
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable content, starting rotation at story 0.")
        return 0


def _write_rotation_index(next_index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(next_index % len(PURANA_SHORT_STORIES)))


def _resolve_forced_story(spec: str) -> int:
    """--story accepts either a plain index or a case-insensitive
    substring match against title_en (e.g. "gajendra" matches
    "Gajendra Moksham")."""
    if spec.strip().isdigit():
        index = int(spec.strip())
        if not (0 <= index < len(PURANA_SHORT_STORIES)):
            raise MahanaviError(f"--story index must be 0-{len(PURANA_SHORT_STORIES) - 1}, got {index}")
        return index
    needle = spec.strip().lower()
    matches = [i for i, s in enumerate(PURANA_SHORT_STORIES) if needle in s.title_en.lower()]
    if not matches:
        raise MahanaviError(
            f"--story '{spec}' did not match any story title_en. "
            f"Valid titles: {', '.join(s.title_en for s in PURANA_SHORT_STORIES)}"
        )
    if len(matches) > 1:
        raise MahanaviError(f"--story '{spec}' matched more than one story: {matches}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the result yourself.",
    )
    parser.add_argument(
        "--story", type=str, default=None,
        help="Force a specific story instead of the next one in rotation (index, or a title_en "
             "substring like 'Gajendra'). A forced run does NOT advance the stored rotation state.",
    )
    args = parser.parse_args()

    settings = get_settings()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    forced = args.story is not None
    try:
        story_index = _resolve_forced_story(args.story) if forced else _read_rotation_index()
    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    story: PuranaShortStory = PURANA_SHORT_STORIES[story_index]
    print(f"Posting story {story_index} ({story.title_en}){' [FORCED]' if forced else ''}")

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    try:
        card = PuranaShortCard(story=story, icon_paths=_icon_paths(settings))
        renderer = PuranaShortCardRenderer(settings)
        image_path = renderer.render(card)
        print(f"Rendered: {image_path}")

        slug = story.title_en.split(" ")[0].lower()
        video_path = settings.output_dir / f"{today.isoformat()}_purana_{slug}_short.mp4"
        assemble_short(
            image_path, video_path,
            duration_seconds=settings.purana_short_duration_seconds,
            audio_path=settings.alert_short_music_path,
            fade_in_seconds=LOOP_FRIENDLY_FADE_IN_SECONDS,
            fade_out_seconds=LOOP_FRIENDLY_FADE_OUT_SECONDS,
        )
        print(f"Assembled (loop-friendly, {settings.purana_short_duration_seconds}s, no fades): {video_path}")

        seo = build_purana_short_seo(story, story_index, today.toordinal())
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        if not forced:
            next_index = (story_index + 1) % len(PURANA_SHORT_STORIES)
            _write_rotation_index(next_index)
            print(f"Rotation advanced: next run will post story {next_index} ({PURANA_SHORT_STORIES[next_index].title_en})")
        else:
            print("Forced run -- rotation state left unchanged.")

        return 0

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
