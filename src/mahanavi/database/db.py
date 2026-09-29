"""
SQLite connection & schema management.

Design notes:
- One `DatabaseManager` per process, holding the path to the .db file.
- `connection()` is a context manager yielding a sqlite3.Connection with
  row_factory set to sqlite3.Row (dict-like access) and foreign keys on.
- Schema is created idempotently (CREATE TABLE IF NOT EXISTS) on init,
  so first-run setup requires no separate migration step. If the schema
  needs to evolve later, add a `schema_version` table and migration
  functions here — the hook point is `_MIGRATIONS` at the bottom.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from mahanavi.exceptions import DatabaseError

_SCHEMA = """
CREATE TABLE IF NOT EXISTS image_usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name   TEXT NOT NULL,
    filename      TEXT NOT NULL,
    used_on       TEXT NOT NULL,          -- ISO date string
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(folder_name, filename, used_on)
);

CREATE INDEX IF NOT EXISTS idx_image_usage_folder ON image_usage(folder_name);

CREATE TABLE IF NOT EXISTS purana_usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    purana_name   TEXT NOT NULL,
    used_on       TEXT NOT NULL,          -- ISO date string
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(purana_name, used_on)
);
"""
# Note: post_log and upload_log tables (one row per Daily Community Post
# run, plus its per-platform upload results) were removed along with the
# Daily Community Post pipeline -- that feature got no engagement and was
# fully decommissioned. Alert Shorts and the Purana video scripts never
# used these tables (confirmed by grep before removal); they don't keep
# a post-log at all.


class DatabaseManager:
    """Owns the SQLite connection lifecycle and schema for the whole app."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            with self.connection() as conn:
                conn.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to initialize schema at {self.db_path}") from exc

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with sane defaults; commits on success, rolls back on error."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(str(exc)) from exc
        finally:
            conn.close()
