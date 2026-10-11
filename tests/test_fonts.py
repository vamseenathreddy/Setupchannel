from __future__ import annotations

from pathlib import Path

import pytest
from PIL import ImageFont

from ytcore.config import PROJECT_ROOT
from ytcore.exceptions import ImageRenderError
from ytcore.images.fonts import FontManager

REAL_FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "NotoSansTelugu-Variable.ttf"


def test_missing_font_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ImageRenderError):
        FontManager(tmp_path / "does_not_exist.ttf")


def test_loads_real_font_and_returns_freetype_font() -> None:
    manager = FontManager(REAL_FONT_PATH)
    font = manager.get_font(size=40, weight="Regular")
    assert isinstance(font, ImageFont.FreeTypeFont)


def test_font_instances_are_cached() -> None:
    manager = FontManager(REAL_FONT_PATH)
    font1 = manager.get_font(size=40, weight="Bold")
    font2 = manager.get_font(size=40, weight="Bold")
    assert font1 is font2


def test_different_sizes_are_not_cached_together() -> None:
    manager = FontManager(REAL_FONT_PATH)
    font_small = manager.get_font(size=20, weight="Regular")
    font_large = manager.get_font(size=60, weight="Regular")
    assert font_small is not font_large


def test_unknown_weight_raises() -> None:
    manager = FontManager(REAL_FONT_PATH)
    with pytest.raises(ImageRenderError):
        manager.get_font(size=40, weight="UltraMegaBold")
