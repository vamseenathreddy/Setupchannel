from __future__ import annotations

from pathlib import Path

import pytest

from mahanavi.database.db import DatabaseManager
from mahanavi.database.repositories import ImageHistoryRepository


@pytest.fixture
def tmp_db(tmp_path: Path) -> DatabaseManager:
    return DatabaseManager(tmp_path / "test.db")


@pytest.fixture
def image_history_repo(tmp_db: DatabaseManager) -> ImageHistoryRepository:
    return ImageHistoryRepository(tmp_db)


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_post_ledger(tmp_path, monkeypatch):
    """Tests must never read or write the real duplicate ledger under data/."""
    from mahanavi.publishers import post_ledger
    monkeypatch.setattr(post_ledger, "DATA_DIR", tmp_path / "ledger")
