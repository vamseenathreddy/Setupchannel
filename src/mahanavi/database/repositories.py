"""
Repositories: the only place that writes raw SQL. Everything else in the
codebase talks to these classes, never to sqlite3 directly.
"""

from __future__ import annotations

from datetime import date

from mahanavi.database.db import DatabaseManager


class ImageHistoryRepository:
    """
    Tracks which images have been used per weekday-folder, so the image
    selector can avoid repeats until every image in a folder is exhausted.
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_used_filenames(self, folder_name: str) -> set[str]:
        """All filenames already used from this folder (across all time)."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT filename FROM image_usage WHERE folder_name = ?",
                (folder_name,),
            ).fetchall()
        return {row["filename"] for row in rows}

    def mark_used(self, folder_name: str, filename: str, used_on: date) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO image_usage (folder_name, filename, used_on)
                VALUES (?, ?, ?)
                """,
                (folder_name, filename, used_on.isoformat()),
            )

    def reset_folder_history(self, folder_name: str) -> None:
        """Wipe usage history for a folder once every image has been used —
        called by the ImageSelector (Module 2) at the start of a new cycle."""
        with self._db.connection() as conn:
            conn.execute(
                "DELETE FROM image_usage WHERE folder_name = ?", (folder_name,)
            )


class PuranaHistoryRepository:
    """
    Tracks which of the 18 Puranas have already been used for a long-form
    video, so episode selection can jump randomly between them (per
    explicit request) while never repeating one until all 18 have been
    covered -- same non-repeating-cycle pattern as ImageHistoryRepository,
    just keyed by Purana name instead of image folder.
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_used_puranas(self) -> set[str]:
        """All Purana names already used (across all time)."""
        with self._db.connection() as conn:
            rows = conn.execute("SELECT DISTINCT purana_name FROM purana_usage").fetchall()
        return {row["purana_name"] for row in rows}

    def mark_used(self, purana_name: str, used_on: date) -> None:
        with self._db.connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO purana_usage (purana_name, used_on) VALUES (?, ?)",
                (purana_name, used_on.isoformat()),
            )

    def reset_history(self) -> None:
        """Wipe usage history once all 18 Puranas have been used, starting
        a fresh non-repeating cycle -- same idea as
        ImageHistoryRepository.reset_folder_history."""
        with self._db.connection() as conn:
            conn.execute("DELETE FROM purana_usage")
