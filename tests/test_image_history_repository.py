from __future__ import annotations

from datetime import date

from ytcore.database.repositories import ImageHistoryRepository


def test_no_usage_initially(image_history_repo: ImageHistoryRepository) -> None:
    assert image_history_repo.get_used_filenames("Monday_Shiva") == set()


def test_mark_used_and_retrieve(image_history_repo: ImageHistoryRepository) -> None:
    image_history_repo.mark_used("Monday_Shiva", "shiva_01.jpg", date(2026, 7, 13))
    image_history_repo.mark_used("Monday_Shiva", "shiva_02.jpg", date(2026, 7, 20))

    used = image_history_repo.get_used_filenames("Monday_Shiva")
    assert used == {"shiva_01.jpg", "shiva_02.jpg"}


def test_usage_scoped_per_folder(image_history_repo: ImageHistoryRepository) -> None:
    image_history_repo.mark_used("Monday_Shiva", "shiva_01.jpg", date(2026, 7, 13))
    image_history_repo.mark_used("Tuesday_Hanuman", "hanuman_01.jpg", date(2026, 7, 14))

    assert image_history_repo.get_used_filenames("Monday_Shiva") == {"shiva_01.jpg"}
    assert image_history_repo.get_used_filenames("Tuesday_Hanuman") == {"hanuman_01.jpg"}


def test_reset_folder_history(image_history_repo: ImageHistoryRepository) -> None:
    image_history_repo.mark_used("Monday_Shiva", "shiva_01.jpg", date(2026, 7, 13))
    image_history_repo.reset_folder_history("Monday_Shiva")
    assert image_history_repo.get_used_filenames("Monday_Shiva") == set()


def test_duplicate_mark_is_idempotent(image_history_repo: ImageHistoryRepository) -> None:
    d = date(2026, 7, 13)
    image_history_repo.mark_used("Monday_Shiva", "shiva_01.jpg", d)
    image_history_repo.mark_used("Monday_Shiva", "shiva_01.jpg", d)  # same day, same file
    assert image_history_repo.get_used_filenames("Monday_Shiva") == {"shiva_01.jpg"}
