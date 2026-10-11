from __future__ import annotations

from pathlib import Path

from ytcore.database.db import DatabaseManager


def test_schema_created(tmp_path: Path) -> None:
    db = DatabaseManager(tmp_path / "test.db")
    with db.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {"image_usage", "purana_usage"}.issubset(tables)


def test_connection_is_idempotent_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    DatabaseManager(db_path)
    # Second instantiation against the same file should not raise.
    db2 = DatabaseManager(db_path)
    with db2.connection() as conn:
        conn.execute("SELECT 1")
