"""
SEO content (titles, descriptions, hashtags) for the "Purana Story"
Shorts series -- mirrors rashi_mantra_seo.py's structure (same
ShortSeoContent shape, bilingual description, rotating title pool by
(date, story) together since this series' content unit is a STORY, not
a calendar date).

POSTING TIME (per explicit request, 2026-10-02: "one cronjob at 6:30
pm"): evening slot, same reasoning as the Rashi Mantra series -- this
content is evergreen (a Puranic story doesn't go stale by time of day),
so it runs in the researched evening engagement window rather than the
early-morning slot used for the time-sensitive Panchang alert Shorts.
"""

from __future__ import annotations

from dataclasses import dataclass

from mahanavi.content.alert_seo import ShortSeoContent  # reuse the same shape
from mahanavi.content.branding import brand_tagline
from mahanavi.content.purana_short_stories import PuranaShortStory

_PURANA_HASHTAGS = ["#పురాణకథలు", "#PuranaStories", "#భక్తికథలు"]

_ROTATING_POOL = [
    "#TeluguDevotional", "#Devotional", "#Bhakti", "#HinduMythology",
    "#IndianMythology", "#Spirituality",
]

# {title} = the story's Telugu title. Phrased as a hook/question per the
# same researched pattern used for the Rashi Mantra titles -- curiosity
# outperforms a flat statement for this kind of Shorts content.
_TITLE_TEMPLATES = [
    "Purana Story | {title} కథ తెలుసా?",
    "Purana Story | {title} - ఈ కథ వినండి",
    "{title} | Purana Story",
    "Purana Story | {title} - పూర్తి కథ ఇదే",
    "Purana Story | ఈ {title} కథ మీకు తెలుసా?",
    "Purana Story | {title} - నీతి ఏంటో తెలుసా?",
    "{title} Story - Watch Till End",
    "Purana Story | {title} - పురాణాల్లో ఈ కథ",
    "Purana Story | {title} కథ వింటే గూస్‌బంప్స్!",
    "Purana Story | {title} - ఈ నీతి మర్చిపోకండి",
]

_HOOKS_TE = [
    "మన పురాణాల్లో ఉన్న ఒక అద్భుతమైన కథ ఇది.",
    "పెద్దలు చెప్పే పురాణ కథల్లో ఇది ఒకటి.",
    "ఈ కథలో దాగి ఉన్న నీతి ప్రతి ఒక్కరికీ ఉపయోగపడుతుంది.",
    "భక్తి, త్యాగం నేర్పే ఈ కథ చదవండి.",
    "మన సంస్కృతిలో చిరకాలంగా చెప్పుకునే కథ ఇది.",
]
_HOOKS_EN = [
    "A timeless story from our Puranas.",
    "One of the classic stories passed down by our elders.",
    "The moral in this story is relevant for everyone.",
    "A story that teaches devotion and sacrifice.",
    "A story told in our culture for generations.",
]

_CTAS_TE = [
    "ప్రతిరోజు ఇలాంటి పురాణ కథల కోసం ఫాలో అవ్వండి.",
    "ఈ కథ నచ్చితే షేర్ చేయండి.",
    "మీకు నచ్చిన పురాణ కథ కామెంట్‌లో చెప్పండి.",
]
_CTAS_EN = [
    "Follow for a new Purana story every day.",
    "Share this if it moved you.",
    "Tell us your favorite Puranic story in the comments.",
]

_COMMENT_PROMPTS_EN = [
    "Which Puranic story do you want next? Comment below!",
    "Tag someone who needs to hear this story.",
    "What's your favorite story from the Puranas?",
]


def _pick_rotating(pool: list[str], index: int) -> str:
    return pool[index % len(pool)]


def _pick_rotating_pair(pool_te: list[str], pool_en: list[str], index: int) -> tuple[str, str]:
    i = index % len(pool_te)
    return pool_te[i], pool_en[i]


def build_purana_short_seo(story: PuranaShortStory, story_index: int, for_date_ordinal: int) -> ShortSeoContent:
    """Build title/description/hashtags for one Purana Story Short."""
    pick_index = for_date_ordinal + story_index
    title = _pick_rotating(_TITLE_TEMPLATES, pick_index).format(title=story.title_te)

    hook_te, hook_en = _pick_rotating_pair(_HOOKS_TE, _HOOKS_EN, pick_index)
    cta_te, cta_en = _pick_rotating_pair(_CTAS_TE, _CTAS_EN, pick_index + 1)
    comment_en = _pick_rotating(_COMMENT_PROMPTS_EN, pick_index + 2)
    comment_te = "మీకు నచ్చిన పురాణ కథ కామెంట్‌లో చెప్పండి!"

    description_te = (
        f"{hook_te}\n\n"
        f"{story.story_te}\n\n"
        f"నీతి: {story.moral_te}\n"
        f"మూలం: {story.purana_name_te}\n\n"
        f"{cta_te}\n\n{comment_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"Moral: {story.moral_en}\n"
        f"Source: {story.purana_name_en}\n\n"
        f"{cta_en}\n\n{comment_en}"
    )

    from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # reused, not duplicated

    description = (
        f"{brand_tagline('purana_short')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_PURANA_HASHTAGS]
    hashtags.append(_pick_rotating(_ROTATING_POOL, pick_index))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
