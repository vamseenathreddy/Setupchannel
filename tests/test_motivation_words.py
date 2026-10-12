"""Daily Purana motivation word Short (content/motivation_words.py)."""
from datetime import date, timedelta

from mahanavi.content import motivation_words as mw


def test_bank_has_no_duplicate_words():
    words = [w.word for w in mw.WORDS]
    assert len(words) == len(set(words)) >= 30


def test_no_repeat_within_a_full_cycle():
    start = date(2026, 10, 13)
    seen = [mw.pick(start + timedelta(days=i)).word for i in range(len(mw.WORDS))]
    assert len(seen) == len(set(seen))


def test_spec_is_two_seconds_on_mahanavi():
    spec = mw.build(date(2026, 10, 13))
    assert spec.total_seconds == 2.0
    assert spec.expected_channel == "Mahanavi"
    assert len(spec.title) <= 100
