"""Every one of the 12 Rashi cards must render without its content overrunning the footer/icon area."""
import logging

import pytest

from mahanavi.config import get_settings
from mahanavi.content.rashi_mantra_content import RASHI_MANTRAS
from mahanavi.images.rashi_card_renderer import RashiCard, RashiCardRenderer
from mahanavi.scripts import post_rashi_mantra_short as m


@pytest.mark.parametrize("idx", range(12))
def test_rashi_card_no_overflow(idx, tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("MAHANAVI_OUTPUT_DIR", str(tmp_path))
    st = get_settings()
    card = RashiCard(content=RASHI_MANTRAS[idx], rashi_index=idx, comment_prompt_text=m.COMMENT_PROMPT_TEXT,
                     icon_paths=m._icon_paths(st))
    with caplog.at_level(logging.WARNING):
        RashiCardRenderer(st).render(card)
    assert not [r for r in caplog.records if "past its budget" in r.getMessage()]
