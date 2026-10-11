from __future__ import annotations

from datetime import date

from ytcore.content.data import (
    DEITY_CONTENT,
    GENERAL_ENGLISH_KEYWORDS,
    GENERAL_TELUGU_HASHTAGS,
    TRENDING_DEVOTIONAL_HASHTAGS,
    WEEKDAY_DEITY_MAP,
    pick_beeja_mantram,
)
from ytcore.core.models import Deity


def test_every_deity_has_content() -> None:
    for deity in Deity:
        assert deity in DEITY_CONTENT
        content = DEITY_CONTENT[deity]
        assert content.telugu_name
        assert content.blessing_phrase
        assert content.mantra
        assert content.telugu_hashtags
        assert content.english_keywords


def test_every_deity_has_at_least_one_beeja_mantram() -> None:
    for deity in Deity:
        assert DEITY_CONTENT[deity].beeja_mantrams


def test_thursday_is_dattatreya_not_sai() -> None:
    # Explicit request: Thursday used to always be Sai with no variety --
    # it's now Dattatreya (the classical Guruvaram deity). Sai's content
    # is kept in DEITY_CONTENT for a possible future Sai-specific post,
    # but it must not be in the daily weekday rotation anymore.
    assert WEEKDAY_DEITY_MAP[3] == Deity.DATTATREYA
    assert Deity.SAI not in WEEKDAY_DEITY_MAP.values()


def test_pick_beeja_mantram_is_deterministic_per_date() -> None:
    content = DEITY_CONTENT[Deity.SHIVA]
    d = date(2026, 9, 26)
    assert pick_beeja_mantram(content, d) == pick_beeja_mantram(content, d)
    assert pick_beeja_mantram(content, d) in content.beeja_mantrams


def test_pick_beeja_mantram_varies_across_dates_for_a_multi_variant_deity() -> None:
    content = DEITY_CONTENT[Deity.SHIVA]
    assert len(content.beeja_mantrams) > 1
    picks = {pick_beeja_mantram(content, date(2026, 9, day)) for day in range(1, 29)}
    # With >1 variant and 28 distinct dates, rotation must produce more
    # than a single value -- guards against the rotation silently
    # collapsing to a constant.
    assert len(picks) > 1


def test_general_lists_are_non_empty() -> None:
    assert GENERAL_TELUGU_HASHTAGS
    assert TRENDING_DEVOTIONAL_HASHTAGS
    assert GENERAL_ENGLISH_KEYWORDS


def test_hashtags_are_well_formed() -> None:
    for tag in TRENDING_DEVOTIONAL_HASHTAGS:
        assert tag.startswith("#")
        assert " " not in tag
    for tag in GENERAL_TELUGU_HASHTAGS:
        assert tag.startswith("#")
        assert " " not in tag
