import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ytcore.exceptions import VideoAssemblyError
from ytcore.video import stotra_video as sv


def _spec(pages=None):
    return sv.StotraSpec(
        slug="t", deity_te="శ్రీ కామాఖ్యా దేవి", deity_en="Sri Kamakhya Devi",
        title_te="శ్రీ కామాఖ్యా స్తోత్రం", title_en="Sri Kamakhya Stotram",
        pages=pages if pages is not None else [{"te": ["నమస్తే దేవి నమస్తే", "నమో నమః"], "en": "Salutations"}],
    )


def test_empty_pages_rejected():
    with pytest.raises(VideoAssemblyError):
        _spec(pages=[]).validate()


def test_plan_segments_covers_total():
    segs = sv.plan_segments(200.0, 4, 2)
    assert abs(sum(s[2] for s in segs) - 200.0) < 1e-6
    assert segs[0][0] == "title" and segs[-1][0] == "end"
    assert len(segs) == 2 + 8


def test_plan_segments_too_short():
    with pytest.raises(VideoAssemblyError):
        sv.plan_segments(20.0, 10, 1)


def test_seo_title_and_description():
    seo = sv.build_seo(_spec(), "https://example.com/pl")
    assert len(seo.title) <= 100 and "Telugu Lyrics" in seo.title
    assert "నమస్తే దేవి నమస్తే" in seo.full_caption()
    assert "#TeluguDevotional" in seo.hashtags


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg missing")
def test_build_video_smoke(tmp_path):
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=30", str(audio)],
                   check=True, capture_output=True)
    out = sv.build_video(_spec(), audio, None, tmp_path / "w", tmp_path / "o.mp4")
    assert out.exists() and out.stat().st_size > 1000
    assert abs(sv.audio_duration(out) - 30) < 1.0
