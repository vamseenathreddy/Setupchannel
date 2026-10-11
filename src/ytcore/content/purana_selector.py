"""
PuranaSelector: picks which of the 18 Puranas the next long-form video
episode should come from -- randomly, per explicit request ("jump
randomly from one purana to another"), but never repeating one until
all 18 have been used at least once (same non-repeating-cycle pattern
as images/selector.py's RandomImageSelector, just tracking Purana names
instead of image filenames).

This selects the PURANA, not the specific story/passage within it --
finding a good, verifiable, self-contained passage inside a huge
Purana still needs the same manual reading/verification process used
for the Manasadevi episode (this book's legacy font encoding makes
text extraction unusable, so passages are read visually and checked
before use). This selector answers "which of the 18 books should the
next episode's research start from", not "which exact paragraph".
"""

from __future__ import annotations

import logging
import random
from datetime import date

from ytcore.database.repositories import PuranaHistoryRepository

logger = logging.getLogger(__name__)

# The 18 Mahapuranas, per the source book's own front-matter list
# (Astadasa_Puranalu.pdf, page 10-11) -- confirmed via direct reading,
# not guessed from general knowledge.
ALL_PURANAS: list[str] = [
    "బ్రహ్మ పురాణం", "పద్మ పురాణం", "విష్ణు పురాణం", "వాయు పురాణం", "భాగవత పురాణం",
    "నారద పురాణం", "మార్కండేయ పురాణం", "అగ్ని పురాణం", "భవిష్య పురాణం", "బ్రహ్మవైవర్త పురాణం",
    "లింగ పురాణం", "వరాహ పురాణం", "స్కంద పురాణం", "వామన పురాణం", "కూర్మ పురాణం",
    "మత్స్య పురాణం", "గరుడ పురాణం", "బ్రహ్మాండ పురాణం",
]


class PuranaSelector:
    """Selects a random, non-repeating Purana name for the next episode."""

    def __init__(self, history_repo: PuranaHistoryRepository, rng: random.Random | None = None) -> None:
        self._history_repo = history_repo
        self._rng = rng or random.Random()

    def select_next(self, for_date: date) -> str:
        used = self._history_repo.get_used_puranas()
        unused = [p for p in ALL_PURANAS if p not in used]

        if not unused:
            logger.info("All 18 Puranas have been used — starting a new cycle.")
            self._history_repo.reset_history()
            unused = ALL_PURANAS

        chosen = self._rng.choice(unused)
        self._history_repo.mark_used(chosen, for_date)
        logger.info("Selected Purana '%s' for episode dated %s.", chosen, for_date)
        return chosen
