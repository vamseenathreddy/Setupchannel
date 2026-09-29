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
