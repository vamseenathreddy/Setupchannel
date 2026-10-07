import datetime as dt

from channels.pulse_boosting import metadata_config as m


class _S:
    def __init__(self, link):
        self.link, self.headline, self.publisher = link, "H", "Pub"


def test_weekday_topic_and_fallback(monkeypatch):
    calls = []

    def fake(query, **kw):
        calls.append(query)
        return None if len(calls) < 3 else _S("https://x/1")

    monkeypatch.setattr(m.trending, "fetch_top_story", fake)
    row = m.fetch_row(set(), dt.date(2026, 10, 5))  # Monday: tech, then gadget, then science
    assert calls[0] == m.TOPICS[0][1] and row["category"] == m.TOPICS[2][0]


def test_none_when_nothing_fresh(monkeypatch):
    monkeypatch.setattr(m.trending, "fetch_top_story", lambda *a, **k: None)
    assert m.fetch_row(set(), dt.date(2026, 10, 7)) is None


def test_bare_title_rejected():
    from channels.engine.trending import Story, is_informative
    assert not is_informative(Story("NASA", "NASA (.gov)", "l", ""))
    assert not is_informative(Story("Apple", "Apple", "l", ""))
    assert is_informative(Story("NASA confirms water ice found near the Moon's south pole", "Reuters", "l", ""))
