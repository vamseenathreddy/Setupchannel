"""Viewer-request Shorts (content/request_shorts.py + images/request_card_renderer.py)."""
import shutil
from pathlib import Path

import pytest

from mahanavi.config import get_settings
from mahanavi.content.request_shorts import NARASIMHA, SPECS
from mahanavi.images.request_card_renderer import SAFE_BOTTOM, SAFE_L, SAFE_R, SAFE_TOP, RequestCardRenderer


def test_spec_seo_is_valid():
    s = NARASIMHA
    assert len(s.title) <= 100 and len(s.title_en) <= 100
    assert s.hashtags[0] == "#Shorts" and len(s.hashtags) <= 5
    assert len(s.description()) <= 5000
    assert len(", ".join(s.tags)) <= 500
    assert s.handle.startswith("@") and s.handle in s.description() and s.handle in s.first_comment()
    assert s.comment_id
    assert s.reply_text("https://www.youtube.com/watch?v=x").startswith(s.handle)


def test_spec_has_four_mantras_with_beeja_first():
    kinds = [x.kind for x in NARASIMHA.slides]
    assert kinds[0] == "intro" and kinds[-1] == "outro" and kinds.count("mantra") == 4
    first = next(x for x in NARASIMHA.slides if x.kind == "mantra")
    assert "బీజ" in first.label_te and "నృం" in first.text_te
    assert NARASIMHA.total_seconds <= 60
    assert SPECS[NARASIMHA.slug] is NARASIMHA


def test_background_differs_from_scheduled_shorts():
    # maroon/saffron (alerts) and green (weekly Rashi) are taken; a request Short is blue-dominant
    for rgb in (NARASIMHA.bg_top, NARASIMHA.bg_mid, NARASIMHA.bg_bottom):
        assert rgb[2] > rgb[0] and rgb[2] > rgb[1]


def test_all_text_inside_the_safe_zone(tmp_path: Path):
    renderer = RequestCardRenderer(get_settings())
    slides = renderer.render_all(NARASIMHA, tmp_path)
    assert len(slides) == len(NARASIMHA.slides)
    for s in slides:
        assert s.path.exists() and s.boxes
        for x0, y0, x1, y1 in s.boxes:
            assert x0 >= SAFE_L - 4 and x1 <= SAFE_R + 4, (s.path.name, x0, x1)
            assert y0 >= SAFE_TOP and y1 <= SAFE_BOTTOM, (s.path.name, y0, y1)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_assemble_matches_total_duration(tmp_path: Path):
    import subprocess

    from mahanavi.scripts.post_request_short import assemble

    settings = get_settings()
    slides = RequestCardRenderer(settings).render_all(NARASIMHA, tmp_path)
    music = settings.alert_short_music_path
    assert music is not None and music.exists()
    video = assemble(NARASIMHA, [s.path for s in slides], music, tmp_path / "v.mp4")
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True).stdout)
    assert abs(dur - NARASIMHA.total_seconds) < 0.3
