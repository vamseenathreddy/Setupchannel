from datetime import date

from channels.lifestyle import post, render, topics


def test_every_theme_has_twelve_sourced_points_in_both_languages():
    for th in topics.THEMES:
        for lang in ("te", "hi"):
            pts = th[lang]["points"]
            assert len(pts) == 12
            assert all(t.strip() and b.strip() and s.strip() for t, b, s in pts)


def test_theme_rotates_by_week():
    assert topics.theme_for(date(2026, 10, 18)) in topics.THEMES


def test_strip_has_one_top_per_point_and_chapters_are_spaced_for_youtube():
    th = topics.THEMES[0]
    for lang in ("te", "hi"):
        tops: list = []
        strip = render.build_strip(lang, th, tops)
        assert len(tops) == 12 and tops == sorted(tops)
        ch = render.chapter_seconds(tops, strip.height)
        assert all(b - a >= 10 for a, b in zip(ch, ch[1:]))
        duration, _speed = render.timing(strip.height)
        assert duration >= 300 and ch[-1] < duration


def test_metadata_title_fits_and_description_has_chapters_and_disclaimer():
    th = topics.THEMES[0]
    for key in ("te", "hi", "tb"):
        lang = post.CHANNELS[key]["lang"]
        tops: list = []
        strip = render.build_strip(lang, th, tops)
        meta = post.metadata(key, th, render.chapter_seconds(tops, strip.height))
        assert len(meta["title"]) <= 100
        assert "0:00" in meta["description"] and topics.DISCLAIMER[lang] in meta["description"]


def test_trance_beats_uses_its_own_backgrounds_and_music():
    ch = post.CHANNELS["tb"]
    assert sorted(ch["assets"].glob(ch["bg_glob"])) and sorted(ch["assets"].glob(ch["music_glob"]))
    assert ch["assets"] != post.CHANNELS["hi"]["assets"]
