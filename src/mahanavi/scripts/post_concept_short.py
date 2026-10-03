"""
post_concept_short.py: posts ONE "Purana Concept" Short per run, cycling
through content/purana_concept_shorts.py's PURANA_CONCEPT_SHORTS (18
entries, interleaved across all 6 concept types) via a persisted
rotation index -- same one-per-run rotation design as
post_purana_short.py.

Flow: read the rotation state (data/last_purana_concept_index.txt,
default 0 if missing/first run) -> pick that entry -> render it as three
layers (PuranaConceptCardRenderer.render_layers() -- background, Sri
Chakra motif, auto-fit text) -> assemble into a .mp4 with the Sri Chakra
rotating behind the fixed text (assemble_purana_short_with_rotating_chakra
-- reused as-is, same seamless-loop rotation already validated for the
Purana Story series) -> build SEO (purana_concept_seo.py) -> upload ->
IF the card's text overflowed even at the legibility floor (layers.
truncated), post the FULL, un-truncated body text as a YouTube comment
on the just-uploaded video (per explicit request, 2026-10-02: "if its
still more and occupying copay same text and put it in comment section
while posting") -> advance the rotation index (wraps back to 0 after the
last entry), UNLESS --concept was used to force a specific one.

POSTING TIME: 11 AM-1 PM IST (scripts/ci/purana_concept_gate.py) --
distinct from both the 12-1 AM alert Shorts and the 5-6 PM Purana Story
Shorts, per explicit request.

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m mahanavi.scripts.post_concept_short
    python -m mahanavi.scripts.post_concept_short --public
    python -m mahanavi.scripts.post_concept_short --concept 0          # force by index
    python -m mahanavi.scripts.post_concept_short --concept Hanuman    # force by title_en substring
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.category_comments import build_category_comment
from mahanavi.content.purana_concept_seo import build_purana_concept_seo
from mahanavi.content.purana_concept_shorts import PURANA_CONCEPT_SHORTS, PuranaConceptShort
from mahanavi.exceptions import MahanaviError
from mahanavi.images.purana_concept_card_renderer import PuranaConceptCard, PuranaConceptCardRenderer
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import assemble_purana_short_with_rotating_chakra

STATE_FILE = Path("data") / "last_purana_concept_index.txt"


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
        return int(STATE_FILE.read_text().strip()) % len(PURANA_CONCEPT_SHORTS)
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable content, starting rotation at concept 0.")
        return 0


def _write_rotation_index(next_index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(str(next_index % len(PURANA_CONCEPT_SHORTS)))


def _resolve_forced_concept(spec: str) -> int:
    """--concept accepts either a plain index or a case-insensitive
    substring match against title_en."""
    if spec.strip().isdigit():
        index = int(spec.strip())
        if not (0 <= index < len(PURANA_CONCEPT_SHORTS)):
            raise MahanaviError(f"--concept index must be 0-{len(PURANA_CONCEPT_SHORTS) - 1}, got {index}")
        return index
    needle = spec.strip().lower()
    matches = [i for i, c in enumerate(PURANA_CONCEPT_SHORTS) if needle in c.title_en.lower()]
    if not matches:
        raise MahanaviError(
            f"--concept '{spec}' did not match any entry's title_en. "
            f"Valid titles: {', '.join(c.title_en for c in PURANA_CONCEPT_SHORTS)}"
        )
    if len(matches) > 1:
        raise MahanaviError(f"--concept '{spec}' matched more than one entry: {matches}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the result yourself.",
    )
    parser.add_argument(
        "--concept", type=str, default=None,
        help="Force a specific entry instead of the next one in rotation (index, or a title_en "
             "substring like 'Hanuman'). A forced run does NOT advance the stored rotation state.",
    )
    args = parser.parse_args()

    settings = get_settings()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    forced = args.concept is not None
    try:
        concept_index = _resolve_forced_concept(args.concept) if forced else _read_rotation_index()
    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    concept: PuranaConceptShort = PURANA_CONCEPT_SHORTS[concept_index]
    print(f"Posting concept {concept_index} ({concept.title_en}, {concept.concept_type.value}){' [FORCED]' if forced else ''}")

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    try:
        card = PuranaConceptCard(concept=concept, icon_paths=_icon_paths(settings))
        renderer = PuranaConceptCardRenderer(settings)
        layers = renderer.render_layers(card)
        print(f"Rendered layers: {layers.background_path}, {layers.chakra_path}, {layers.text_path}")
        if layers.truncated:
            print("Note: card text overflowed at the legibility floor -- full text will be posted as a comment.")

        slug = concept.title_en.split(" ")[0].lower()
        video_path = settings.output_dir / f"{today.isoformat()}_concept_{slug}_short.mp4"
        chakra_x = layers.chakra_center_x - layers.chakra_width // 2
        chakra_y = layers.chakra_center_y - layers.chakra_height // 2
        assemble_purana_short_with_rotating_chakra(
            background_path=layers.background_path,
            chakra_path=layers.chakra_path,
            text_path=layers.text_path,
            output_path=video_path,
            duration_seconds=settings.purana_concept_short_duration_seconds,
            chakra_x=chakra_x,
            chakra_y=chakra_y,
            audio_path=settings.alert_short_music_path,
        )
        print(f"Assembled (rotating Sri Chakra, loop-friendly, {settings.purana_concept_short_duration_seconds}s, no fades): {video_path}")

        seo = build_purana_concept_seo(concept, concept_index, today.toordinal())
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        # Category tag is folded into the SAME comment as the full-text
        # overflow (when there is one), rather than posting two separate
        # comments on one video -- keeps to the "one comment per video"
        # design (category_comments.py) even on this series' special case.
        category_tag = build_category_comment("puranas", today.toordinal())
        if layers.truncated and result.video_id:
            comment_text = f"{concept.title_te}\n\n{layers.full_body_te}\n\n— {concept.purana_name_te}\n\n{category_tag}"
            posted = uploader.post_comment(result.video_id, comment_text)
            if posted:
                print("Posted full text as a comment (card text was truncated).")
            else:
                print(
                    "Note: could not post full text as a comment (likely needs a re-run of "
                    "youtube_shorts_auth_setup.py for the broadened scope -- see that script's docstring).",
                )
        elif result.video_id:
            if uploader.post_comment(result.video_id, category_tag):
                print(f"Posted category comment: {category_tag}")
            else:
                print("Note: could not post category comment (non-fatal).")

        if not forced:
            next_index = (concept_index + 1) % len(PURANA_CONCEPT_SHORTS)
            _write_rotation_index(next_index)
            print(f"Rotation advanced: next run will post concept {next_index} ({PURANA_CONCEPT_SHORTS[next_index].title_en})")
        else:
            print("Forced run -- rotation state left unchanged.")

        return 0

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
