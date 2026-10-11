from __future__ import annotations

from pathlib import Path

import pytest

from ytcore.config import Settings
from ytcore.exceptions import ConfigError
from ytcore.panchang.api_provider import ApiPanchangProvider
from ytcore.panchang.dummy_provider import DummyPanchangProvider
from ytcore.panchang.factory import get_panchang_provider


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    images_root = tmp_path / "Images"
    images_root.mkdir(parents=True, exist_ok=True)
    base = dict(
        images_root=images_root,
        output_dir=tmp_path / "out",
        database_path=tmp_path / "db" / "test.db",
        log_dir=tmp_path / "logs",
    )
    base.update(overrides)
    return Settings(**base)


def test_dummy_provider_selected_by_default(tmp_path: Path) -> None:
    settings = _settings(tmp_path, panchang_provider="dummy")
    provider = get_panchang_provider(settings)
    assert isinstance(provider, DummyPanchangProvider)


def test_api_provider_selected_with_base_url(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path,
        panchang_provider="api",
        panchang_api_base_url="https://example.test/panchang",
    )
    provider = get_panchang_provider(settings)
    assert isinstance(provider, ApiPanchangProvider)


def test_api_provider_without_base_url_raises(tmp_path: Path) -> None:
    settings = _settings(tmp_path, panchang_provider="api")
    with pytest.raises(ConfigError):
        get_panchang_provider(settings)


def test_scraper_provider_without_selectors_raises(tmp_path: Path) -> None:
    settings = _settings(tmp_path, panchang_provider="scraper")
    with pytest.raises(ConfigError):
        get_panchang_provider(settings)


def test_unknown_provider_raises(tmp_path: Path) -> None:
    settings = _settings(tmp_path, panchang_provider="carrier_pigeon")
    with pytest.raises(ConfigError):
        get_panchang_provider(settings)
