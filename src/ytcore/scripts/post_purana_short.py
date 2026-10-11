"""
post_purana_short.py: posts ONE "Purana Story" Short per run, cycling
through content/purana_short_stories.py's PURANA_SHORT_STORIES in order
via a persisted rotation index -- same one-per-run rotation design as
post_rashi_mantra_short.py, not all of them at once (would flood
subscribers' feeds and dilute each video's individual loop/replay
performance).

Flow: read the rotation state (data/last_purana_short_index.txt,
default 0 if missing/first run) -> pick that story -> render it as three
layers (PuranaShortCardRenderer.render_layers() -- background, a Sri
Chakra motif, and the text, auto-fit per story, never scrolling, never
narrated, per explicit requirement) -> assemble into a .mp4 with the Sri
Chakra slowly swaying/rotating behind the fixed text
(assemble_purana_short_with_rotating_chakra -- see that function's
docstring for why a sway instead of a continuous spin) and NO fade-in/
fade-out at a duration shorter than a comfortable full read (settings.
purana_short_duration_seconds, 5s) so viewers loop 2-3x to finish
reading -> build SEO (purana_short_seo.py) -> upload -> advance the
rotation index (never wraps -- see SKIP_TITLES_EN), UNLESS --story
was used to force a specific one (a forced run is a deliberate one-off
re-post/test, so it does NOT disturb where the natural rotation is).

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m ytcore.scripts.post_purana_short
    python -m ytcore.scripts.post_purana_short --public
    python -m ytcore.scripts.post_purana_short --story 0            # force by index
    python -m ytcore.scripts.post_purana_short --story Gajendra     # force by title_en substring
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ytcore.config import Settings, get_settings
from ytcore.content.category_comments import build_category_comment
from ytcore.content.purana_short_seo import build_purana_short_seo
from ytcore.content.purana_short_stories import PURANA_SHORT_STORIES, PuranaShortStory
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import UploadLogRepository
from ytcore.exceptions import AppError
from ytcore.images.purana_short_card_renderer import PuranaShortCard, PuranaShortCardRenderer
from ytcore.publishers.blogger_publisher import post_to_blogger
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.assembler import assemble_purana_short_with_rotating_chakra

STATE_FILE = Path("data") / "last_purana_short_index.txt"

# Ever-incrementing posting count shown on the card ("పురాణ కథ - N"),
# tracked separately from STATE_FILE's bounded 0-9 content rotation --
# see PuranaShortCard.episode_number's docstring for why. Never reset,
# never wraps, so a forced/test run still advances it (unlike the
# content rotation, which a forced run deliberately leaves alone).
EPISODE_COUNT_FILE = Path("data") / "purana_short_episode_count.txt"


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


# NO REPEATS (explicit request, 2026-10-06: "don't repeat uploaded stories"). The rotation no longer
# wraps back to story 0 -- once every story has been posted the run fails loudly until more stories are
# added to content/purana_short_stories.py. These titles are also skipped because the SAME story is
# already on the channel from another series (the Puranam Shorts / long videos): Markandeya was posted
# 2026-09-27 as a Puranam Short, and Kurma / the churning of the ocean is covered by the Mahalakshmi
# Avirbhavam video (2026-09-26).
SKIP_TITLES_EN = {"Markandeya's Boon", "Kurma Avatara and the Churning of the Ocean"}


def _next_postable_index(index: int) -> int:
    # Skip already-posted titles AND date-pinned stories (those post only on their date).
    while index < len(PURANA_SHORT_STORIES) and (
        PURANA_SHORT_STORIES[index].title_en in SKIP_TITLES_EN or PURANA_SHORT_STORIES[index].date
    ):
        index += 1
    return index


def _story_pinned_to(day: str) -> int | None:
    """Index of the story pinned to this IST date (festival/tithi story), if any."""
    for i, s in enumerate(PURANA_SHORT_STORIES):
        if s.date == day:
            return i
    return None


def _read_rotation_index() -> int:
    if not STATE_FILE.exists():
        return 0
    try:
        return int(STATE_FILE.read_text().strip())
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable content, starting rotation at story 0.")
        return 0


def _write_rotation_index(next_index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(next_index))


def _read_episode_count() -> int:
    if not EPISODE_COUNT_FILE.exists():
        return 0
    try:
        return int(EPISODE_COUNT_FILE.read_text().strip())
    except ValueError:
        print(f"Note: {EPISODE_COUNT_FILE} had unreadable content, starting episode count at 0.")
        return 0


def _write_episode_count(count: int) -> None:
    EPISODE_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    EPISODE_COUNT_FILE.write_text(str(count))


def _resolve_forced_story(spec: str) -> int:
    """--story accepts either a plain index or a case-insensitive
    substring match against title_en (e.g. "gajendra" matches
    "Gajendra Moksham")."""
    if spec.strip().isdigit():
        index = int(spec.strip())
        if not (0 <= index < len(PURANA_SHORT_STORIES)):
            raise AppError(f"--story index must be 0-{len(PURANA_SHORT_STORIES) - 1}, got {index}")
        return index
    needle = spec.strip().lower()
    matches = [i for i, s in enumerate(PURANA_SHORT_STORIES) if needle in s.title_en.lower()]
    if not matches:
        raise AppError(
            f"--story '{spec}' did not match any story title_en. "
            f"Valid titles: {', '.join(s.title_en for s in PURANA_SHORT_STORIES)}"
        )
    if len(matches) > 1:
        raise AppError(f"--story '{spec}' matched more than one story: {matches}")
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
    pinned_index = None if forced else _story_pinned_to(datetime.now(ZoneInfo(settings.timezone)).date().isoformat())
    try:
        if forced:
            story_index = _resolve_forced_story(args.story)
        elif pinned_index is not None:
            story_index = pinned_index
            print(f"Date-pinned festival story for today: {PURANA_SHORT_STORIES[pinned_index].title_en}")
        else:
            story_index = _next_postable_index(_read_rotation_index())
    except AppError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    if story_index >= len(PURANA_SHORT_STORIES):
        print("FAILED: every Purana Story has been posted already -- add new stories to "
              "content/purana_short_stories.py (nothing is re-posted automatically).", file=sys.stderr)
        return 1

    story: PuranaShortStory = PURANA_SHORT_STORIES[story_index]
    print(f"Posting story {story_index} ({story.title_en}){' [FORCED]' if forced else ''}")

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    episode_count = _read_episode_count()
    episode_number = episode_count + 1

    try:
        card = PuranaShortCard(story=story, episode_number=episode_number, icon_paths=_icon_paths(settings))
        renderer = PuranaShortCardRenderer(settings)
        layers = renderer.render_layers(card)
        print(f"Rendered layers: {layers.background_path}, {layers.chakra_path}, {layers.text_path}")

        slug = story.title_en.split(" ")[0].lower()
        video_path = settings.output_dir / f"{today.isoformat()}_purana_{slug}_short.mp4"
        # chakra_x/y: top-left placement for the (fixed-size, rotating)
        # chakra image so its own center -- its bindu, where ffmpeg's
        # rotate filter actually pivots -- lands at the intended spot on
        # the full card. See PuranaShortCardLayers' docstring.
        chakra_x = layers.chakra_center_x - layers.chakra_width // 2
        chakra_y = layers.chakra_center_y - layers.chakra_height // 2
        assemble_purana_short_with_rotating_chakra(
            background_path=layers.background_path,
            chakra_path=layers.chakra_path,
            text_path=layers.text_path,
            output_path=video_path,
            duration_seconds=settings.purana_short_duration_seconds,
            chakra_x=chakra_x,
            chakra_y=chakra_y,
            audio_path=settings.alert_short_music_path,
        )
        print(f"Assembled (rotating Sri Chakra, loop-friendly, {settings.purana_short_duration_seconds}s, no fades): {video_path}")

        seo = build_purana_short_seo(story, story_index, today.toordinal())
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        if result.video_id:
            comment_text = build_category_comment("puranas", today.toordinal(), topic_te=story.search_keyword_te)
            if uploader.post_comment(result.video_id, comment_text):
                print(f"Posted category comment: {comment_text}")
            else:
                print("Note: could not post category comment (non-fatal).")

            db = DatabaseManager(settings.database_path)
            UploadLogRepository(db).log_upload(result.video_id, "puranas", seo.title, today)

            if settings.playlist_id_puranas:
                if uploader.add_to_playlist(result.video_id, settings.playlist_id_puranas):
                    print("Added to playlist.")
                else:
                    print("Note: could not add to playlist (non-fatal).")

            if post_to_blogger(settings, result.video_id, seo.title, seo.full_caption()):
                print("Posted to Blogger.")
            else:
                print("Note: could not post to Blogger (non-fatal).")

        _write_episode_count(episode_number)
        print(f"Episode count advanced: next run will show 'పురాణ కథ - {episode_number + 1}'")

        if not forced and pinned_index is None:
            next_index = _next_postable_index(story_index + 1)
            _write_rotation_index(next_index)
            if next_index < len(PURANA_SHORT_STORIES):
                print(f"Rotation advanced: next run will post story {next_index} ({PURANA_SHORT_STORIES[next_index].title_en})")
            else:
                print("Rotation advanced: that was the last story -- add more before the next run.")
        else:
            print("Forced or date-pinned run -- rotation state left unchanged.")

        return 0

    except AppError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
