"""
Image selection: picks today's devotional image from the correct
weekday folder, without repeating an image until every image in that
folder has been used at least once.

Algorithm:
    1. Resolve today's folder (e.g. Monday -> Images/Monday_Shiva).
    2. List all valid image files in it.
    3. Ask ImageHistoryRepository which filenames have already been used
       from this folder.
    4. unused = all_files - used_files
    5. If unused is empty (every image has been used), reset the folder's
       history in the DB and treat all files as unused again — this starts
       a fresh non-repeating cycle rather than ever blocking the pipeline.
    6. Randomly choose one from `unused`.
    7. Record it as used (for today's date) so it's excluded next time.

This class deliberately knows nothing about *how* images get rendered,
what Panchang is, or how posts get published — it only answers
"which image, and where is it".
"""

from __future__ import annotations

import logging
import random
from datetime import date
from pathlib import Path

from ytcore.config import WEEKDAY_FOLDER_MAP, Settings
from ytcore.core.interfaces import ImageSelector
from ytcore.core.models import Deity, SelectedImage
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import ImageSelectionError

logger = logging.getLogger(__name__)

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def deity_from_folder_name(folder_name: str) -> Deity:
    """'Monday_Shiva' -> Deity.SHIVA. Raises ImageSelectionError if unmappable."""
    try:
        _, deity_part = folder_name.split("_", 1)
        return Deity(deity_part)
    except (ValueError, KeyError) as exc:
        raise ImageSelectionError(
            f"Cannot determine deity from folder name '{folder_name}'. "
            f"Expected format 'Weekday_DeityName' matching one of: "
            f"{[d.value for d in Deity]}"
        ) from exc


class RandomImageSelector(ImageSelector):
    """Selects a random, non-repeating image per weekday folder."""

    def __init__(
        self,
        settings: Settings,
        history_repo: ImageHistoryRepository,
        rng: random.Random | None = None,
    ) -> None:
        self._settings = settings
        self._history_repo = history_repo
        self._rng = rng or random.Random()

    def select_for_date(self, for_date: date) -> SelectedImage:
        folder_name = WEEKDAY_FOLDER_MAP[for_date.weekday()]
        return self.select_from_folder(folder_name, for_date)

    def select_from_folder(self, folder_name: str, for_date: date) -> SelectedImage:
        """Pick a non-repeating image from an EXPLICITLY given folder,
        not necessarily today's weekday folder -- used by other pipelines
        (e.g. a long-form video that rotates among a custom subset of
        deity folders, like Vishnu/Shiva/Ganesha only) that want the same
        "don't repeat until every image has been used" behavior without
        being tied to the actual weekday mapping."""
        folder_path = self._settings.images_root / folder_name

        all_files = self._list_valid_images(folder_path)
        if not all_files:
            raise ImageSelectionError(
                f"No valid images found in {folder_path}. "
                f"Add at least one image ({', '.join(sorted(VALID_IMAGE_EXTENSIONS))}) "
                "to this folder."
            )

        used_filenames = self._history_repo.get_used_filenames(folder_name)
        unused = [f for f in all_files if f.name not in used_filenames]

        if not unused:
            logger.info(
                "All %d images in %s have been used — starting a new cycle.",
                len(all_files),
                folder_name,
            )
            self._history_repo.reset_folder_history(folder_name)
            unused = all_files

        chosen = self._rng.choice(unused)
        self._history_repo.mark_used(folder_name, chosen.name, for_date)

        logger.info("Selected image '%s' from folder '%s' for %s.", chosen.name, folder_name, for_date)

        return SelectedImage(
            path=chosen,
            folder_name=folder_name,
            filename=chosen.name,
            deity=deity_from_folder_name(folder_name),
        )

    @staticmethod
    def _list_valid_images(folder_path: Path) -> list[Path]:
        if not folder_path.exists():
            raise ImageSelectionError(f"Folder does not exist: {folder_path}")
        return sorted(
            p for p in folder_path.iterdir()
            if p.is_file() and p.suffix.lower() in VALID_IMAGE_EXTENSIONS
        )
