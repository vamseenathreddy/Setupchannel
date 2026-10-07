"""Live Hyderabad's own TrendingMetaConfig + fetch_row -- Pattern B. Query is scoped tightly
to the city so the "last 6 hours" window surfaces genuinely Hyderabad-specific news (traffic,
civic, weather, local events) rather than generic India news that happens to mention the city.
"""
from channels.engine import trending
from channels.engine.trending_metadata import TrendingMetaConfig, make_bundle_fn, make_captions_fn

QUERY = "Hyderabad"
HL, GL, CEID = "en-IN", "IN", "IN:en"
HOURS = 6

META_CFG = TrendingMetaConfig(
    channel_name="Live Hyderabad",
    core_tags=["#LiveHyderabad", "#Shorts", "#Hyderabad"],
    topic_tags=["#HyderabadNews", "#Telangana", "#HyderabadUpdates", "#Trending"],
    common_tags=["#HyderabadCity", "#CyberabadNews", "#LocalNews", "#Viral"],
    keywords=["Hyderabad news", "Hyderabad city news", "Telangana news", "Hyderabad today",
              "Hyderabad traffic", "Hyderabad weather", "Hyderabad local news", "Hyderabad shorts"],
    intro="Live Hyderabad -- one real, trending Hyderabad-city headline a day, in under a minute.",
    comment_text="What's happening in your part of the city? Tell us below! 👇",
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
