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


def test_pick_story_skips_used_and_stale_and_prefers_short():  # equal coverage and rank order, short first
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    long_ = Story("A very long headline " * 6, "P", "l1", now - timedelta(hours=1))
    stale = Story("Stale but fine headline here", "P", "l2", now - timedelta(hours=40))
    used = Story("Already posted headline right here", "P", "l3", now - timedelta(hours=1))
    short = Story("Fresh short headline for today", "P", "l4", now - timedelta(hours=2))
    long_.rank, stale.rank, used.rank, short.rank = 1, 2, 3, 4
    got = pick_story("sports", "en", {used.key}, None, now, fetch_news=lambda n, l: [long_, stale, used, short])
    assert got is short
    assert pick_story("sports", "en", {short.key, used.key, long_.key}, None, now,
                      fetch_news=lambda n, l: [stale, used, short, long_]) is None
    assert not fresh_enough(stale, now, 30) and fresh_enough(stale, now, 48)


def test_only_top_10_and_widest_coverage_first():
    now = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)
    mk = lambda h, rank, rel=(): Story(h, "P", f"l{rank}", now - timedelta(hours=1), rank=rank, related=rel)  # noqa: E731
    low = mk("Rank twelve headline that is out of the top ten", 12, (("a", "x"),) * 5)
    plain = mk("Rank one headline with no other outlets", 1)
    wide = mk("Rank four headline carried by several outlets", 4, (("a", "x"), ("b", "y")))
    got = pick_story("sports", "en", set(), None, now, fetch_news=lambda n, l: [low, plain, wide])
    assert got is wide  # outranks rank 1 on coverage; rank 12 is outside the top 10
    assert pick_story("sports", "en", {plain.key, wide.key}, None, now, fetch_news=lambda n, l: [low, plain, wide]) is None


def test_rank_only_in_description_not_on_card():
    s = Story("Fresh short headline for today", "Eenadu", "l", None, rank=3)
    row = metadata.row_for(s, "en", "sports")
    assert "label" not in row and "TRENDING" not in "".join(str(v) for v in row.values())
    assert "Ranked #3 in today's top 10 trending sports stories" in metadata.description(s, "en", "sports")
    assert "Trending India" in metadata.title(s, "en", "sports")


def test_twelve_two_hourly_slots_from_midnight():
    assert [h for h, _ in cfg.SLOTS] == list(range(0, 24, 2)) and len({s for _, s in cfg.SLOTS}) == 12


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


def test_related_headlines_come_from_the_story_cluster():
    desc = ('&lt;ol&gt;&lt;li&gt;&lt;a href="x"&gt;ఇది రెండవ పత్రిక శీర్షిక ఇక్కడ&lt;/a&gt;&amp;nbsp;&amp;nbsp;'
            '&lt;font color="#6f6f6f"&gt;Sakshi&lt;/font&gt;&lt;/li&gt;&lt;/ol&gt;')
    rss = (f'<rss><channel><item><title>ప్రధాన శీర్షిక ఇక్కడ ఉంది - Eenadu</title><link>https://n/1</link>'
           f'<description>{desc}</description><source url="x">Eenadu</source></item></channel></rss>')
    got = parse_rss(rss)[0].related
    assert got == (("ఇది రెండవ పత్రిక శీర్షిక ఇక్కడ", "Sakshi"),)


def test_meta_description_and_trim():
    from channels.trending.sources import _meta_description, trim
    page = '<html><head><meta property="og:description" content="Gill &amp; co named for the tour."></head></html>'
    assert _meta_description(page) == "Gill & co named for the tour."
    assert _meta_description('<meta name="description" content="Plain one">') == "Plain one"
    assert len(trim("word " * 100, 50)) <= 51 and trim("short", 50) == "short"


def test_enrich_keeps_only_same_language_related_and_row_has_source_last():
    from channels.trending.sources import enrich
    s = Story("భారత్ ఘన విజయం, కోహ్లీ సెంచరీ", "Eenadu", "l", None, "news",
              related=(("భారత్ గెలుపు, అభిమానుల సంబరాలు", "Sakshi"), ("India win the final in style", "Hindu"),
                       ("మరో తెలుగు శీర్షిక ఇక్కడ ఉంది", "A"), ("ఇంకొక తెలుగు శీర్షిక ఇక్కడ ఉంది", "B")))
    import channels.trending.sources as src
    src.article_summary = lambda *a, **k: "ఇది ప్రచురణకర్త సారాంశం"
    enrich(s, "te")
    assert len(s.related) == 3 and all("India" not in h for h, _ in s.related)
    row = metadata.row_for(s, "te", "sports")
    assert row["text_summary"] and row["text_related"].startswith("• ") and row["text_secondary"] == "Source: Eenadu"
    assert "Also reported:" in metadata.description(s, "te", "sports")


def test_news_stories_drops_other_language_headlines(monkeypatch):
    import channels.trending.sources as src
    xml = ("<rss><channel>"
           "<item><title>ಭಾರತ ತಂಡ ನ್ಯೂಜಿಲೆಂಡ್ ಪ್ರವಾಸಕ್ಕೆ ಆಯ್ಕೆ ಘೋಷಣೆ - ಪ್ರಜಾವಾಣಿ</title><link>a</link><source>ಪ್ರಜಾವಾಣಿ</source></item>"
           "<item><title>टेस्ला ने उड़ने वाली कार दिखाई, हवा में पलटी - दैनिक भास्कर</title><link>b</link><source>दैनिक भास्कर</source></item>"
           "</channel></rss>")
    monkeypatch.setattr(src, "_get", lambda *a, **k: xml)
    got = src.news_stories("breaking", "kn")
    assert [s.link for s in got] == ["a"]


def test_playlist_add_waits_for_a_new_playlist_instead_of_failing(monkeypatch):
    import channels.trending.playlists as pl
    from googleapiclient.errors import HttpError

    class Resp:
        status = 404
        reason = "Not Found"

    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise HttpError(Resp(), b"playlistNotFound")
        return "ok"

    monkeypatch.setattr(pl.time, "sleep", lambda s: None)
    assert pl._settled(flaky) == "ok" and calls["n"] == 3
    always = lambda: (_ for _ in ()).throw(HttpError(Resp(), b"x"))  # noqa: E731
    assert pl._settled(always, empty={"items": []}) == {"items": []}


def test_summary_accepts_decoder_success_key(monkeypatch):
    import sys
    import types
    import channels.trending.sources as src
    mod = types.ModuleType("googlenewsdecoder")
    mod.gnewsdecoder = lambda link, interval=1: {"success": True, "decoded_url": "https://example.com/a"}
    monkeypatch.setitem(sys.modules, "googlenewsdecoder", mod)
    monkeypatch.setattr(src, "_get", lambda *a, **k: '<meta property="og:description" content="ఇది ప్రచురణకర్త సారాంశం మరియు మరిన్ని వివరాలు ఇక్కడ">')
    assert src.article_summary("l", "te", "వేరే శీర్షిక") != ""
