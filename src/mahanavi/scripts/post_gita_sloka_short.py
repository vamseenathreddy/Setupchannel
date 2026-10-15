"""
post_gita_sloka_short.py: posts ONE "Bhagavad Gita Sloka" Short per run,
alternating VERSE days and QUIZ days -- not one verse every single day.

CADENCE (explicit request, 2026-10-03: "i want to change plan to not
every day one sloka it should be like one day verse nextday quiz with
4 options on before days verse so total 1400 days this pipeline will
work. so users will learn from yesterday also we have to push them to
know answer look yesterday verse post number"):

  Day 1 (VERSE): post the next verse in GITA_SLOKAS (Sanskrit + Telugu
    meaning + its chapter/verse badge, same card as before).
  Day 2 (QUIZ):  post a 4-option "which chapter & verse was THAT verse?"
    quiz (gita_sloka_quiz.py / GitaQuizCardRenderer) -- shows the same
    Sanskrit verse again but WITHOUT the chapter/verse badge, so the
    only way to confirm the answer is to go find yesterday's Short on
    the channel again. That's the deliberate engagement mechanic: it
    pulls viewers back through the channel's own back-catalog instead
    of just testing scriptural memory in isolation.
  Day 3 (VERSE): the NEXT verse (rotation advances only after a quiz
    day, not after a verse day) -- and so on.

Once all 700 Bhagavad Gita verses are in GITA_SLOKAS, this pipeline
runs for 700 * 2 = 1400 days before it needs to loop back to verse 1.

STATE: a single rotation state (data/last_gita_sloka_index.txt) now
stores "MODE:INDEX" (e.g. "verse:3" or "quiz:3") instead of a bare
index -- MODE says what to post THIS run, INDEX says which verse it's
about. After a verse-day post, state becomes "quiz:<same index>" (the
quiz is about what was JUST posted). After a quiz-day post, state
becomes "verse:<index + 1>" (advance to the next verse, wrapping back
to 0 after the last one). A legacy bare-integer state file (from
before this cadence existed) is still read correctly, treated as
"verse:<that index>".

CONTENT SCOPE: GITA_SLOKAS currently holds a phase-1 subset of verses
(see that module's docstring) -- more get added over time; this script
doesn't need to change as the list grows. If GITA_SLOKAS doesn't yet
have enough verses for a 4-option quiz (gita_sloka_quiz.MIN_SLOKAS_FOR_QUIZ),
a quiz-day run falls back to posting another verse instead, so the
pipeline never breaks while the verse list is still small.

POSTING TIME: 3-4 PM IST (scripts/ci/gita_sloka_gate.py) -- same single
daily window for both verse days and quiz days.

SAFETY: uploads as "unlisted" by default, same as every other posting
script in this repo -- pass --public once you've reviewed it.

Usage:
    python -m mahanavi.scripts.post_gita_sloka_short
    python -m mahanavi.scripts.post_gita_sloka_short --public
    python -m mahanavi.scripts.post_gita_sloka_short --sloka 0            # force verse by index
    python -m mahanavi.scripts.post_gita_sloka_short --sloka 2.47         # force verse by "chapter.verse"
    python -m mahanavi.scripts.post_gita_sloka_short --mode quiz          # force a quiz on the current rotation verse
    python -m mahanavi.scripts.post_gita_sloka_short --sloka 2.47 --mode quiz   # force a quiz on a specific verse
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.bhagavad_gita_slokas import GITA_SLOKAS, GitaSloka
from mahanavi.content.category_comments import build_category_comment
from mahanavi.content.gita_sloka_quiz import MIN_SLOKAS_FOR_QUIZ, build_quiz_options
from mahanavi.content.gita_sloka_seo import build_gita_sloka_quiz_seo, build_gita_sloka_seo
from mahanavi.database.db import DatabaseManager
from mahanavi.database.repositories import UploadLogRepository
from mahanavi.exceptions import MahanaviError
from mahanavi.images.gita_quiz_card_renderer import GitaQuizCard, GitaQuizCardRenderer
from mahanavi.images.gita_sloka_card_renderer import GitaSlokaCard, GitaSlokaCardRenderer, pick_invocation
from mahanavi.publishers.blogger_publisher import post_to_blogger
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import assemble_short
from mahanavi.video.watermark import GITA_POSITIONS_Y

QUIZ_ENABLED = False  # owner request 2026-10-15: no Gita Quiz Shorts for now (set True to resume)
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


def _read_state() -> tuple[str, int]:
    """Returns (mode, index). Missing file -> ("verse", 0) -- the very
    first run ever has no previous verse to quiz on, so it must be a
    verse day. Also accepts a legacy bare-integer file (pre-dates the
    verse/quiz cadence), read as ("verse", that index)."""
    if not STATE_FILE.exists():
        return "verse", 0
    raw = STATE_FILE.read_text().strip()
    if ":" not in raw:
        try:
            return "verse", int(raw) % len(GITA_SLOKAS)
        except ValueError:
            print(f"Note: {STATE_FILE} had unreadable content, starting at verse 0.")
            return "verse", 0
    mode, _, idx_s = raw.partition(":")
    if mode not in ("verse", "quiz"):
        print(f"Note: {STATE_FILE} had unrecognized mode '{mode}', starting at verse 0.")
        return "verse", 0
    try:
        return mode, int(idx_s) % len(GITA_SLOKAS)
    except ValueError:
        print(f"Note: {STATE_FILE} had unreadable index, starting at verse 0.")
        return "verse", 0


def _write_state(mode: str, index: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(f"{mode}:{index % len(GITA_SLOKAS)}")


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
    parser.add_argument(
        "--mode", choices=["verse", "quiz"], default=None,
        help="Force verse or quiz mode instead of the persisted rotation state. Combine with --sloka "
             "to target a specific verse; without --sloka, targets whatever verse is currently in "
             "rotation. A forced run does NOT advance the stored rotation state.",
    )
    args = parser.parse_args()

    settings = get_settings()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    forced = args.sloka is not None or args.mode is not None
    # Snapshot BEFORE _read_state() -- the only reliable way to tell "the
    # very first run ever" (no previous quiz exists to reveal) apart from
    # a legitimate "verse:0" written after the rotation wrapped around.
    had_prior_state = STATE_FILE.exists()
    try:
        state_mode, state_index = _read_state()
        target_index = _resolve_forced_sloka(args.sloka) if args.sloka is not None else state_index
    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    # --sloka alone (no --mode) means "force this verse", matching the
    # series' pre-existing CLI convention. --mode alone targets whatever
    # verse rotation is currently on.
    mode = args.mode or ("verse" if args.sloka is not None else state_mode)

    if mode == "quiz" and len(GITA_SLOKAS) < MIN_SLOKAS_FOR_QUIZ:
        print(
            f"Note: only {len(GITA_SLOKAS)} verse(s) in GITA_SLOKAS, need {MIN_SLOKAS_FOR_QUIZ} "
            "for a 4-option quiz -- posting a verse instead today."
        )
        mode = "verse"

    if mode == "quiz" and not QUIZ_ENABLED and args.mode is None:
        # Owner request 2026-10-15: stop the Gita Quiz Short (verses continue on their own days).
        # The quiz turn is skipped and the rotation moves on to the next verse.
        next_index = (target_index + 1) % len(GITA_SLOKAS)
        _write_state("verse", next_index)
        print(f"Gita quiz is switched off (QUIZ_ENABLED=False): nothing posted, next run posts VERSE {next_index}.")
        return 0

    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()

    try:
        if mode == "verse":
            sloka: GitaSloka = GITA_SLOKAS[target_index]
            print(f"Posting VERSE {target_index} ({sloka.chapter}.{sloka.verse}){' [FORCED]' if forced else ''}")

            # Reveal yesterday's quiz answer on every verse-day card
            # except the very first run ever (no previous quiz exists).
            previous_quiz_sloka: GitaSloka | None = None
            if QUIZ_ENABLED and len(GITA_SLOKAS) > 1 and (had_prior_state or forced):
                previous_quiz_sloka = GITA_SLOKAS[(target_index - 1) % len(GITA_SLOKAS)]

            verse_card = GitaSlokaCard(
                sloka=sloka, icon_paths=_icon_paths(settings), previous_quiz_sloka=previous_quiz_sloka,
                invocation_text=pick_invocation(today.toordinal()),
            )
            image_path = GitaSlokaCardRenderer(settings).render(verse_card)
            print(f"Rendered card: {image_path}")

            video_path = settings.output_dir / f"{today.isoformat()}_gita_{sloka.chapter}_{sloka.verse}_short.mp4"
            assemble_short(
                image_path=image_path,
                output_path=video_path,
                duration_seconds=settings.gita_sloka_short_duration_seconds,
                audio_path=settings.alert_short_music_path,
                fade_in_seconds=0.0,
                fade_out_seconds=0.0,
                watermark_positions_y=GITA_POSITIONS_Y,
            )
            print(f"Assembled (loop-friendly, {settings.gita_sloka_short_duration_seconds}s, no fades): {video_path}")

            seo = build_gita_sloka_seo(sloka, target_index, today.toordinal(), previous_quiz_sloka=previous_quiz_sloka)

        else:  # mode == "quiz"
            quiz = build_quiz_options(target_index, today.toordinal())
            print(
                f"Posting QUIZ on verse {target_index} ({quiz.target.chapter}.{quiz.target.verse})"
                f"{' [FORCED]' if forced else ''} -- correct answer is option {quiz.correct_letter}"
            )

            # Tomorrow's verse is deterministic (next_index below) even
            # though it isn't persisted as state until after a
            # successful upload -- safe to tease it here.
            next_index = (target_index + 1) % len(GITA_SLOKAS)
            next_verse_hint: GitaSloka | None = GITA_SLOKAS[next_index] if len(GITA_SLOKAS) > 1 else None

            quiz_card = GitaQuizCard(
                quiz=quiz, icon_paths=_icon_paths(settings), next_verse_hint=next_verse_hint,
                invocation_text=pick_invocation(today.toordinal()),
            )
            image_path = GitaQuizCardRenderer(settings).render(quiz_card)
            print(f"Rendered card: {image_path}")

            video_path = (
                settings.output_dir
                / f"{today.isoformat()}_gita_quiz_{quiz.target.chapter}_{quiz.target.verse}_short.mp4"
            )
            assemble_short(
                image_path=image_path,
                output_path=video_path,
                duration_seconds=settings.gita_sloka_short_duration_seconds,
                audio_path=settings.alert_short_music_path,
                fade_in_seconds=0.0,
                fade_out_seconds=0.0,
                watermark_positions_y=GITA_POSITIONS_Y,
            )
            print(f"Assembled (loop-friendly, {settings.gita_sloka_short_duration_seconds}s, no fades): {video_path}")

            seo = build_gita_sloka_quiz_seo(quiz, today.toordinal(), next_verse_hint=next_verse_hint)

        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if not result.success:
            print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
            return 1

        print(f"Uploaded ({privacy_status}): {result.post_url}")

        if result.video_id:
            comment_category = "slokas" if mode == "verse" else "quiz"
            comment_text = build_category_comment(comment_category, today.toordinal())
            if uploader.post_comment(result.video_id, comment_text):
                print(f"Posted category comment: {comment_text}")
            else:
                print("Note: could not post category comment (non-fatal).")

            db = DatabaseManager(settings.database_path)
            # One playlist for the whole series (verse AND quiz days) --
            # they're one alternating series, not two separate ones.
            UploadLogRepository(db).log_upload(result.video_id, "gita_sloka", seo.title, today)

            if settings.playlist_id_gita_sloka:
                if uploader.add_to_playlist(result.video_id, settings.playlist_id_gita_sloka):
                    print("Added to playlist.")
                else:
                    print("Note: could not add to playlist (non-fatal).")

            if post_to_blogger(settings, result.video_id, seo.title, seo.full_caption()):
                print("Posted to Blogger.")
            else:
                print("Note: could not post to Blogger (non-fatal).")

        if not forced:
            if mode == "verse" and not QUIZ_ENABLED:
                _write_state("quiz", target_index)  # next turn is a quiz turn, which is skipped (see above)
            elif mode == "verse":
                _write_state("quiz", target_index)
                print(f"State advanced: next run will QUIZ on verse {target_index} ({sloka.chapter}.{sloka.verse})")
            else:
                next_index = (target_index + 1) % len(GITA_SLOKAS)
                _write_state("verse", next_index)
                next_sloka = GITA_SLOKAS[next_index]
                print(f"State advanced: next run will post VERSE {next_index} ({next_sloka.chapter}.{next_sloka.verse})")
        else:
            print("Forced run -- rotation state left unchanged.")

        return 0

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
