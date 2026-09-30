"""
Tests for scripts/ci/scheduler_gate.py's decision logic (_decide).

This script lives outside the installed `mahanavi` package (it's a CI-only
helper, like drive_state_sync.py, never imported at runtime), so it's
loaded here directly by file path rather than via a normal import.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "scheduler_gate.py"
_spec = importlib.util.spec_from_file_location("scheduler_gate", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
scheduler_gate = importlib.util.module_from_spec(_spec)
sys.modules["scheduler_gate"] = scheduler_gate
_spec.loader.exec_module(scheduler_gate)

IST = ZoneInfo("Asia/Kolkata")


def _ist(y: int, m: int, d: int, hh: int, mm: int) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=IST)


@pytest.fixture
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(scheduler_gate, "DATA_DIR", tmp_path / "data")
    return tmp_path / "data"


def _mark(data_dir: Path, which: str, date_str: str) -> None:
    (data_dir / f"last_run_date_{which}.txt").write_text(date_str)


class TestWindowBoundaries:
    def test_before_midnight_never_fires(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 23, 45)  # 11:45 PM -- still "yesterday" in spirit
        assert scheduler_gate._decide(now, "") == "none"

    def test_at_exactly_midnight_can_fire(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 0, 0)
        assert scheduler_gate._decide(now, "") == "rahu_kalam"

    def test_at_one_fifty_nine_am_can_fire(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 1, 59)
        assert scheduler_gate._decide(now, "") == "rahu_kalam"

    def test_at_two_fifty_nine_am_can_fire(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 2, 59)
        assert scheduler_gate._decide(now, "") == "rahu_kalam"

    def test_at_exactly_three_am_stops_firing(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 3, 0)
        assert scheduler_gate._decide(now, "") == "none"

    def test_daytime_tick_never_fires(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 14, 30)
        assert scheduler_gate._decide(now, "") == "none"


class TestOrdering:
    def test_rahu_kalam_first_when_neither_posted(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 0, 15)
        assert scheduler_gate._decide(now, "") == "rahu_kalam"

    def test_shubha_ghadiyalu_once_rahu_kalam_done(self, isolated_data_dir: Path) -> None:
        _mark(isolated_data_dir, "rahu_kalam", "2026-09-30")
        now = _ist(2026, 9, 30, 1, 5)
        assert scheduler_gate._decide(now, "") == "shubha_ghadiyalu"

    def test_durmuhurtham_once_rahu_and_shubha_done(self, isolated_data_dir: Path) -> None:
        _mark(isolated_data_dir, "rahu_kalam", "2026-09-30")
        _mark(isolated_data_dir, "shubha_ghadiyalu", "2026-09-30")
        now = _ist(2026, 9, 30, 2, 5)
        assert scheduler_gate._decide(now, "") == "durmuhurtham"

    def test_none_once_all_three_done(self, isolated_data_dir: Path) -> None:
        _mark(isolated_data_dir, "rahu_kalam", "2026-09-30")
        _mark(isolated_data_dir, "shubha_ghadiyalu", "2026-09-30")
        _mark(isolated_data_dir, "durmuhurtham", "2026-09-30")
        now = _ist(2026, 9, 30, 2, 30)
        assert scheduler_gate._decide(now, "") == "none"

    def test_yesterdays_marker_does_not_count_as_done_today(self, isolated_data_dir: Path) -> None:
        _mark(isolated_data_dir, "rahu_kalam", "2026-09-29")
        now = _ist(2026, 9, 30, 0, 10)
        assert scheduler_gate._decide(now, "") == "rahu_kalam"


class TestForceOverride:
    def test_force_target_ignores_daytime_window(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 15, 0)
        assert scheduler_gate._decide(now, "rahu_kalam") == "rahu_kalam"

    def test_force_target_ignores_already_posted_marker(self, isolated_data_dir: Path) -> None:
        _mark(isolated_data_dir, "shubha_ghadiyalu", "2026-09-30")
        now = _ist(2026, 9, 30, 15, 0)
        assert scheduler_gate._decide(now, "shubha_ghadiyalu") == "shubha_ghadiyalu"

    def test_force_both(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 15, 0)
        assert scheduler_gate._decide(now, "both") == "both"

    def test_force_durmuhurtham(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 15, 0)
        assert scheduler_gate._decide(now, "durmuhurtham") == "durmuhurtham"

    def test_empty_force_target_falls_back_to_normal_rules(self, isolated_data_dir: Path) -> None:
        now = _ist(2026, 9, 30, 15, 0)
        assert scheduler_gate._decide(now, "") == "none"
