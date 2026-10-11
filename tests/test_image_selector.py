from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pytest

from ytcore.config import Settings
from ytcore.core.models import Deity
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import ImageSelectionError
from ytcore.images.selector import RandomImageSelector, deity_from_folder_name


def _make_settings(images_root: Path) -> Settings:
    # Bypass env/.env entirely and construct directly with required paths.
    # images_root itself must exist before Settings validation runs.
    images_root.mkdir(parents=True, exist_ok=True)
    return Settings(
        images_root=images_root,
        output_dir=images_root / "out",
        database_path=images_root / "db" / "test.db",
        log_dir=images_root / "logs",
    )


def _touch_images(folder: Path, names: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_bytes(b"fake-image-bytes")


@pytest.fixture
def images_root(tmp_path: Path) -> Path:
    return tmp_path / "Images"


def test_deity_from_folder_name() -> None:
    assert deity_from_folder_name("Monday_Shiva") == Deity.SHIVA
    assert deity_from_folder_name("Sunday_Surya") == Deity.SURYA


def test_deity_from_folder_name_invalid_raises() -> None:
    with pytest.raises(ImageSelectionError):
        deity_from_folder_name("NotAWeekday")
    with pytest.raises(ImageSelectionError):
        deity_from_folder_name("Monday_UnknownGod")


def test_missing_folder_raises(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    # Deliberately do NOT create Monday_Shiva.
    selector = RandomImageSelector(settings, image_history_repo)
    with pytest.raises(ImageSelectionError):
        selector.select_for_date(date(2026, 7, 20))  # a Monday


def test_empty_folder_raises(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    (images_root / "Monday_Shiva").mkdir(parents=True)
    selector = RandomImageSelector(settings, image_history_repo)
    with pytest.raises(ImageSelectionError):
        selector.select_for_date(date(2026, 7, 20))


def test_non_image_files_are_ignored(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    folder = images_root / "Monday_Shiva"
    _touch_images(folder, ["shiva1.jpg", "readme.txt", "notes.md"])
    selector = RandomImageSelector(settings, image_history_repo)
    result = selector.select_for_date(date(2026, 7, 20))
    assert result.filename == "shiva1.jpg"


def test_selection_returns_correct_deity_and_folder(
    images_root: Path, image_history_repo: ImageHistoryRepository
) -> None:
    settings = _make_settings(images_root)
    _touch_images(images_root / "Tuesday_Hanuman", ["h1.png"])
    selector = RandomImageSelector(settings, image_history_repo)
    result = selector.select_for_date(date(2026, 7, 21))  # a Tuesday
    assert result.folder_name == "Tuesday_Hanuman"
    assert result.deity == Deity.HANUMAN
    assert result.filename == "h1.png"


def test_no_repeat_until_all_used(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    names = [f"shiva_{i}.jpg" for i in range(5)]
    _touch_images(images_root / "Monday_Shiva", names)
    selector = RandomImageSelector(settings, image_history_repo, rng=random.Random(42))

    # Simulate 5 consecutive Mondays (7 days apart -> same weekday each time).
    monday = date(2026, 7, 6)
    chosen_in_first_cycle = []
    for i in range(5):
        result = selector.select_for_date(monday + timedelta(weeks=i))
        chosen_in_first_cycle.append(result.filename)

    # All 5 images must appear exactly once before any repeat.
    assert sorted(chosen_in_first_cycle) == sorted(names)
    assert len(set(chosen_in_first_cycle)) == 5


def test_cycle_resets_after_exhaustion(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    names = ["a.jpg", "b.jpg"]
    _touch_images(images_root / "Monday_Shiva", names)
    selector = RandomImageSelector(settings, image_history_repo, rng=random.Random(1))

    monday = date(2026, 7, 6)
    seen = [selector.select_for_date(monday + timedelta(weeks=i)).filename for i in range(2)]
    assert sorted(seen) == names  # first cycle: both used

    # Third pick (3rd Monday) should trigger reset and pick from full set again,
    # not raise ImageSelectionError.
    third = selector.select_for_date(monday + timedelta(weeks=2))
    assert third.filename in names


def test_marks_usage_in_repository(images_root: Path, image_history_repo: ImageHistoryRepository) -> None:
    settings = _make_settings(images_root)
    _touch_images(images_root / "Wednesday_Ganesha", ["g1.jpg"])
    selector = RandomImageSelector(settings, image_history_repo)
    selector.select_for_date(date(2026, 7, 22))  # a Wednesday

    used = image_history_repo.get_used_filenames("Wednesday_Ganesha")
    assert used == {"g1.jpg"}
