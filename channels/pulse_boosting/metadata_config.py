"""Pulse Boosting's own TrendingMetaConfig + fetch_row -- Pattern B (one real, fresh headline/day,
see channels/engine/trending.py and channels/engine/trending_metadata.py).

Channel focus (owner, 2026-10-07, from the channel's own YouTube keywords): technology updates,
gadget reviews, movies, inspiring stories, creativity, latest/trending. NOT general India news.
Each weekday has its own topic (rotation below); if that topic has nothing fresh in its time
window we fall back to the next topic in the rotation, so a day is rarely skipped.
"""
import datetime as dt

from channels.engine import trending
from channels.engine.trending_metadata import TrendingMetaConfig, make_bundle_fn, make_captions_fn

HL, GL, CEID = "en-IN", "IN", "IN:en"

# (label, Google News query, look-back hours). Inspiring/creative stories are rarer, so a wider window.
TOPICS = [
    ("Tech Update", "technology updates OR new technology OR AI", 12),            # Mon
    ("Gadget Review", "gadget review OR smartphone launch OR new gadget", 24),    # Tue
    ("Movies", "new movie OR movie trailer OR box office", 12),                   # Wed
    ("Inspiring Story", "inspiring story OR success story OR against all odds", 48),  # Thu
    ("Creativity", "creativity OR innovation OR invention OR design", 48),        # Fri
    ("Latest Gadgets", "latest gadgets OR tech launch OR new launch", 24),        # Sat
    ("Trending Now", "viral OR trending", 12),                                    # Sun
]

META_CFG = TrendingMetaConfig(
    channel_name="Pulse Boosting",
    core_tags=["#PulseBoosting", "#Shorts", "#Trending"],
    topic_tags=["#TechUpdates", "#GadgetReviews", "#Movies", "#InspiringStories"],
    common_tags=["#Creativity", "#Inspiring", "#Latest", "#Viral"],
    keywords=["technology updates", "movies", "inspiring stories", "gadget reviews", "creativity",
              "inspiring", "latest", "trending"],
    intro="Pulse Boosting -- tech updates, gadgets, movies, inspiring stories and what's trending, one a day.",
    comment_text="What do you think about this? Share your views below. 👇",
)


def fetch_row(used_ids, today=None):
    """ChannelPipeline.fetch_row contract: (used_ids) -> row dict | None. row["id"] is the story's own
    link (state.mark_posted appends it to used_ids), passed through as exclude_links so a story that is
    still trending is never posted twice."""
    today = today or dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
    start = today.weekday()
    for i in range(len(TOPICS)):
        label, query, hours = TOPICS[(start + i) % len(TOPICS)]
        story = trending.fetch_top_story(query, hl=HL, gl=GL, ceid=CEID, hours=hours,
                                          exclude_links=frozenset(used_ids))
        if story is not None:
            return {
                "id": story.link,
                "category": label,
                "text_primary": story.headline,
                "text_secondary": story.publisher,
                "source": story.link,
                "special": "",
                "used": "",
                "scheduled_for": "",
            }
    return None


bundle = make_bundle_fn(META_CFG)
captions = make_captions_fn()
