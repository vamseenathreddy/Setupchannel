"""Trending news channel: sources, planning, metadata. No network."""
from datetime import datetime, timedelta, timezone

from channels.trending import config as cfg
from channels.trending import metadata, post
from channels.trending.sources import (Story, clean_title, fresh_enough, is_informative, matches_language,
                                       parse_rss, pick_story)

RSS = """<?xml version="1.0"?><rss><channel>
<item><title>భారత్ ఘన విజయం, కోహ్లీ సెంచరీ - Eenadu</title><link>https://n/1</link>
<pubDate>Fri, 16 Oct 2026 10:00:00 GMT</pubDate><source url="x">Eenadu</source></item>
<item><title>Eenadu</title><link>https://n/2</link><source url="x">Eenadu</source></item>
</channel></rss>"""


def test_parse_rss_strips_publisher_and_keeps_source():
    items = parse_rss(RSS)
    assert items[0].headline == "భారత్ ఘన విజయం, కోహ్లీ సెంచరీ"
    assert items[0].publisher == "Eenadu" and items[0].link == "https://n/1"
    assert items[0].published == datetime(2026, 10, 16, 10, 0, tzinfo=timezone.utc)
    assert [is_informative(s) for s in items] == [True, False]  # a bare publisher name is not a headline


def test_clean_title_removes_hashtags_and_emoji():
    assert clean_title("Big win 🔥 #Shorts #IPL now") == "Big win now"


def test_language_matching():
    assert matches_language("భారత్ ఘన విజయం", "te") and not matches_language("India wins", "te")
    assert matches_language("India wins big", "en") and not matches_language("भारत जीता", "en")
    assert matches_language("வெற்றி பெற்றது", "ta") and matches_language("ಭಾರತ ಗೆದ್ದಿತು", "kn")
    assert matches_language("ഇന്ത്യ ജയിച്ചു", "ml") and matches_language("भारत जीता", "hi")


def test_every_language_niche_pair_is_planned_once_in_42():
    seen = {cfg.plan(i) for i in range(42)}
    assert len(seen) == 42 and {l for l, _ in seen} == set(cfg.LANGS) and {n for _, n in seen} == set(cfg.NICHES)


def test_labels_cover_every_language_and_niche():
    for lang in cfg.LANGS:
        assert len(cfg.NICHE_NATIVE[lang]) == len(cfg.NICHES)
        assert lang in cfg.CTA and lang in cfg.INTRO and lang in cfg.LANG_TAG
        for n in cfg.NICHES:
            t, d = cfg.playlist_for(lang, n)
            assert len(t) <= 150 and len(d) <= 5000 and "<" not in t + d


def test_pick_story_skips_used_and_stale_and_prefers_short():
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    long_ = Story("A very long headline " * 6, "P", "l1", now - timedelta(hours=1))
    stale = Story("Stale but fine headline here", "P", "l2", now - timedelta(hours=40))
    used = Story("Already posted headline right here", "P", "l3", now - timedelta(hours=1))
    short = Story("Fresh short headline for today", "P", "l4", now - timedelta(hours=2))
    got = pick_story("sports", "en", {used.key}, None, now, fetch_news=lambda n, l: [long_, stale, used, short])
    assert got is short
    assert pick_story("sports", "en", {short.key, used.key, long_.key}, None, now,
                      fetch_news=lambda n, l: [stale, used, short, long_]) is None
    assert not fresh_enough(stale, now, 30) and fresh_enough(stale, now, 48)


def test_failing_source_does_not_stop_the_slot():
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    ok = Story("Trending video title worth showing", "Chan", "yt1", now - timedelta(hours=1), "yt")

    def boom(*_):
        raise RuntimeError("down")
    assert pick_story("cinema", "en", set(), object(), now, fetch_news=boom, fetch_yt=lambda y, n, l: [ok]) is ok


def test_choose_falls_through_to_other_niches():
    story = Story("Fallback story headline here", "P", "l", None)
    calls = []

    def fetch(n, lang, used, yt):
        calls.append(n)
        return story if n == "business" else None
    niche, got = post.choose("en", "sports", set(), None, fetch=fetch)
    assert got is story and niche == "business" and calls[0] == "sports"


def test_metadata_names_source_and_mixes_english():
    s = Story("ఆసియా కప్ ఫైనల్‌లో భారత్ ఘన విజయం", "Eenadu", "https://n/1", None)
    m = metadata.bundle(s, "te", "sports")
    assert len(m["title"]) <= 100 and "Sports" in m["title"] and "Pulse Boosting" in m["title"]
    assert "Source: Eenadu" in m["description"] and "https://n/1" in m["description"]
    assert "Link: https://n/1" in m["comment"] and m["language"] == "te"
    assert len(metadata.hashtags("te", "sports")) <= 15 and sum(len(t) + 1 for t in m["tags"]) <= 500
    yt = Story("Trending video", "Some Channel", "https://youtu.be/x", None, "yt")
    assert "YouTube trending, creator: Some Channel" in metadata.description(yt, "en", "viral")


def test_long_title_is_trimmed_to_100():
    s = Story("word " * 60, "P", "l", None)
    assert len(metadata.title(s, "en", "breaking")) <= 100
