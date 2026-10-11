"""
gita_sloka_quiz.py: builds the 4-option multiple-choice "which chapter
& verse was yesterday's Gita Sloka Short?" quiz data for the Gita Sloka
series' quiz day (every other day -- see post_gita_sloka_short.py's
module docstring for the full verse-day/quiz-day cadence).

Explicit request (2026-10-03): "i want to change plan to not every day
one sloka it should be like one day verse nextday quiz with 4 options
on before days verse ... so users will learn from yesterday also we
have to push them to know answer look yesterday verse post number" --
the correct answer is literally the PREVIOUS day's chapter/verse
reference (the number shown as that Short's on-screen badge), so
answering correctly requires having watched -- or going back to
rewatch -- that earlier Short. That's the explicit engagement
mechanic requested: it pulls a viewer back through the channel's own
back-catalog, rather than testing independent scriptural knowledge.

Distractor refs are 3 OTHER verses already in GITA_SLOKAS (never a
fabricated chapter/verse that doesn't exist in this channel's
content), so a curious viewer who checks can always find all 4 as
real, already-posted Shorts on the channel. Picked deterministically
(seeded by the date) so a given day's quiz is reproducible across
retries/re-renders on that same day, but the specific distractor set
still varies from one quiz day to the next.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from mahanavi.content.bhagavad_gita_slokas import GITA_SLOKAS, GitaSloka
from mahanavi.exceptions import MahanaviError

# Need target + 3 distinct distractors. Only possible to fall short of
# this very early in phase 1 before enough verses have been added --
# callers should fall back to posting another verse Short instead of a
# quiz in that case (see post_gita_sloka_short.py).
MIN_SLOKAS_FOR_QUIZ = 4

_OPTION_LETTERS = ["A", "B", "C", "D"]


@dataclass(frozen=True, slots=True)
class GitaQuizOptions:
    target: GitaSloka         # the verse being quizzed on (yesterday's post)
    options: list[GitaSloka]  # 4 slokas, in on-card display order (one is `target`)
    correct_letter: str       # "A"/"B"/"C"/"D" -- options[index] == target at that index


def build_quiz_options(target_index: int, for_date_ordinal: int) -> GitaQuizOptions:
    """4 options: `target` plus 3 other distinct verses from GITA_SLOKAS,
    in a date-seeded shuffled order.

    Raises Channel AError if GITA_SLOKAS doesn't yet have enough verses
    to build 4 distinct options -- see MIN_SLOKAS_FOR_QUIZ.
    """
    if len(GITA_SLOKAS) < MIN_SLOKAS_FOR_QUIZ:
        raise MahanaviError(
            f"Need at least {MIN_SLOKAS_FOR_QUIZ} verses in GITA_SLOKAS to build a 4-option quiz, "
            f"only have {len(GITA_SLOKAS)} -- post another verse instead of a quiz for now."
        )

    target = GITA_SLOKAS[target_index]
    other_indices = [i for i in range(len(GITA_SLOKAS)) if i != target_index]

    rng = random.Random(for_date_ordinal)
    distractor_indices = rng.sample(other_indices, 3)
    options = [target] + [GITA_SLOKAS[i] for i in distractor_indices]
    rng.shuffle(options)

    correct_index = options.index(target)
    return GitaQuizOptions(target=target, options=options, correct_letter=_OPTION_LETTERS[correct_index])
