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


class UploadLogRepository:
    """
    One row per successful upload, keyed by video_id and tagged with
    its series -- added 2026-10-03 so weekly_performance_report.py can
    ask "which video_ids belong to the Gita Sloka series over the last
    7 days?" without parsing titles. Every posting script calls
    log_upload() right after a successful upload, non-fatal on failure
    (same spirit as post_comment()/add_to_playlist() -- a failed log
    write must never fail the pipeline that already succeeded).
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def log_upload(self, video_id: str, series: str, title: str, posted_on: date) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO uploads (video_id, series, title, posted_on)
                VALUES (?, ?, ?, ?)
                """,
                (video_id, series, title, posted_on.isoformat()),
            )

    def video_ids_for_series(self, series: str, since: date) -> list[str]:
        """All video_ids for `series` posted on or after `since` -- used
        by the weekly performance report to scope its Analytics query."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT video_id FROM uploads WHERE series = ? AND posted_on >= ? ORDER BY posted_on",
                (series, since.isoformat()),
            ).fetchall()
        return [row["video_id"] for row in rows]

    def all_video_ids_since(self, since: date) -> list[tuple[str, str]]:
        """(video_id, series) pairs for every upload on or after `since`,
        across all series -- used by the weekly report to do one batched
        Analytics query instead of one per series."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT video_id, series FROM uploads WHERE posted_on >= ? ORDER BY posted_on",
                (since.isoformat(),),
            ).fetchall()
        return [(row["video_id"], row["series"]) for row in rows]
