"""Pulse Boosting's own TrendingMetaConfig + fetch_row -- Pattern B (one real trending India
headline/day, see channels/engine/trending.py and channels/engine/trending_metadata.py). Query
is broad ("India") so there is always something fresh within the last 6 hours; language is
English since that's where the volume of indexed, well-attributed India-wide headlines is.
"""
from channels.engine import trending
from channels.engine.trending_metadata import TrendingMetaConfig, make_bundle_fn, make_captions_fn

QUERY = "India"
HL, GL, CEID = "en-IN", "IN", "IN:en"
HOURS = 6  # "popular content of last 6 hours" per the channel owner

META_CFG = TrendingMetaConfig(
    channel_name="Pulse Boosting",
    core_tags=["#PulseBoosting", "#Shorts", "#BreakingNews"],
    topic_tags=["#India", "#NewsUpdate", "#Trending", "#TopNews"],
    common_tags=["#NewsShorts", "#CurrentAffairs", "#IndiaNews", "#Viral"],
    keywords=["India news", "breaking news today", "trending news India", "top news today",
              "latest news", "news shorts", "current affairs India", "viral news"],
    intro="Pulse Boosting -- one real, trending India headline a day, in under a minute.",
    comment_text="What do you think about this? Share your views below. 👇",
)


def fetch_row(used_ids):
    """ChannelPipeline.fetch_row contract: (used_ids) -> row dict | None. row["id"] is set to
    the story's own link (see below), and state.mark_posted() appends row_id to used_ids on a
    successful post -- so used_ids here is naturally a set of already-posted article links,
    which we pass straight through as exclude_links to skip an exact repeat of a story that's
    still trending."""
    story = trending.fetch_top_story(QUERY, hl=HL, gl=GL, ceid=CEID, hours=HOURS,
                                      exclude_links=frozenset(used_ids))
    if story is None:
        return None
    return {
        "id": story.link,
        "category": "news",
        "text_primary": story.headline,
        "text_secondary": story.publisher,
        "source": story.link,
        "special": "",
        "used": "",
        "scheduled_for": "",
    }


bundle = make_bundle_fn(META_CFG)
captions = make_captions_fn()
