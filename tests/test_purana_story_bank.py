from ytcore.content.purana_short_stories import PURANA_SHORT_STORIES
from ytcore.scripts.post_purana_short import _next_postable_index, _story_pinned_to


def test_bank_loaded_and_unique():
    assert len(PURANA_SHORT_STORIES) >= 70
    titles = [s.title_en for s in PURANA_SHORT_STORIES]
    assert len(titles) == len(set(titles))
    topics = [s.topic for s in PURANA_SHORT_STORIES if s.topic]
    assert len(topics) == len(set(topics)) == 60


def test_bank_fields_complete():
    for s in PURANA_SHORT_STORIES:
        for f in ("title_te", "title_en", "invocation_te", "story_te", "search_keyword_te",
                  "moral_te", "moral_en", "purana_name_te", "purana_name_en"):
            assert getattr(s, f).strip(), (s.title_en, f)


def test_dated_stories_skipped_in_rotation_and_pinned_by_date():
    i = _story_pinned_to("2026-11-08")
    assert i is not None and PURANA_SHORT_STORIES[i].date == "2026-11-08"
    idx = 0
    while (idx := _next_postable_index(idx)) < len(PURANA_SHORT_STORIES):
        assert PURANA_SHORT_STORIES[idx].date is None
        idx += 1
