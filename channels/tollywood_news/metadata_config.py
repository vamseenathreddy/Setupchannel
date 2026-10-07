"""Tollywood News's own TrendingMetaConfig + fetch_row -- Pattern B. Query targets Telugu film
industry releases/gossip specifically; hl stays English since that's where Google News indexes
the deepest, fastest-updating coverage of Tollywood (most entertainment-desk coverage of Telugu
cinema is published in English even for an Indian audience) -- the headline text itself is
whatever script the source publishes in, and NotoSansTelugu (see channel_config.py) renders
either cleanly.
"""
from channels.engine import trending
from channels.engine.trending_metadata import TrendingMetaConfig, make_bundle_fn, make_captions_fn

QUERY = "Tollywood"
HL, GL, CEID = "en-IN", "IN", "IN:en"
HOURS = 6

META_CFG = TrendingMetaConfig(
    channel_name="Tollywood News",
    core_tags=["#TollywoodNews", "#Shorts", "#Tollywood"],
    topic_tags=["#TeluguCinema", "#TollywoodUpdates", "#TeluguMovies", "#Trending"],
    common_tags=["#TeluguFilmIndustry", "#TollywoodGossip", "#CelebrityNews", "#Viral"],
    keywords=["Tollywood news", "Telugu cinema news", "Telugu movie updates", "Tollywood gossip",
              "Telugu film industry", "Tollywood latest", "Telugu actors news", "Tollywood shorts"],
    intro="Tollywood News -- one real, trending Telugu film industry headline a day, in under a minute.",
    comment_text="What's your take on this? Drop a comment! 👇",
)


def fetch_row(used_ids):
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
