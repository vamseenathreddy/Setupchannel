"""
SEO content (titles, descriptions, hashtags) for the "Bhagavad Gita
Sloka" Shorts series -- same proven structure as purana_short_seo.py /
purana_concept_seo.py (rotating title templates, hooks, CTAs, comment
prompts, bilingual description with the shared channel footer).

POSTING TIME: 3-4 PM IST (gita_sloka_gate.py) -- distinct from the
12-1 AM alert Shorts, 11 AM-1 PM Purana Concept Shorts, and 5-6 PM
Purana Story Shorts.
"""

from __future__ import annotations

from mahanavi.content.alert_seo import ShortSeoContent  # reuse the same shape
from mahanavi.content.bhagavad_gita_slokas import GitaSloka
from mahanavi.content.branding import brand_tagline

_GITA_HASHTAGS = ["#భగవద్గీత", "#BhagavadGita", "#GitaWisdom"]

_ROTATING_POOL = [
    "#TeluguDevotional", "#Devotional", "#Bhakti", "#Krishna",
    "#SanatanaDharma", "#Spirituality",
]

# {title} = "చాప్టర్ {chapter}.{verse}" style reference the formatter
# below builds -- kept separate from the template so chapter/verse stay
# numerals (easier to scan in a title) rather than spelled out.
_TITLE_TEMPLATES = [
    "భగవద్గీత {ref} - అర్థం తెలుసా?",
    "గీతా శ్లోకం {ref} | Bhagavad Gita",
    "నేటి గీతా సందేశం - {ref}",
    "{ref} - ఈ శ్లోకం జీవితాన్ని మారుస్తుంది",
    "కృష్ణుడి మాట - {ref}",
    "భగవద్గీత {ref} - వినండి, అర్థం చేసుకోండి",
]

_HOOKS_TE = [
    "శ్రీకృష్ణుడు అర్జునుడికి చెప్పిన ఈ మాట ఇవాళ్టికీ ప్రతిఒక్కరికీ వర్తిస్తుంది.",
    "భగవద్గీతలో ఉన్న అత్యంత ప్రసిద్ధ శ్లోకాల్లో ఇది ఒకటి.",
    "జీవితంలో ఎదురయ్యే సందిగ్ధాలకు గీత ఇచ్చే సమాధానం ఇది.",
    "కురుక్షేత్రంలో కృష్ణుడు బోధించిన ఈ సత్యం ఇప్పటికీ ప్రాసంగికమే.",
]
_HOOKS_EN = [
    "This teaching Krishna gave Arjuna still applies to everyone today.",
    "One of the most quoted verses in the entire Bhagavad Gita.",
    "The Gita's answer to a dilemma everyone faces at some point.",
    "A truth Krishna taught on the battlefield of Kurukshetra, still relevant today.",
]

_CTAS_TE = [
    "ప్రతిరోజు ఇలాంటి గీతా శ్లోకాల కోసం ఫాలో అవ్వండి.",
    "ఈ శ్లోకం నచ్చితే షేర్ చేయండి.",
    "ఈ శ్లోకం మీ జీవితంలో ఎలా వర్తిస్తుందో కామెంట్‌లో చెప్పండి.",
]
_CTAS_EN = [
    "Follow for a new Gita verse every day.",
    "Share this if it spoke to you.",
    "Tell us how this verse applies to your life in the comments.",
]

_COMMENT_PROMPTS_EN = [
    "Which Gita chapter should we cover next? Comment below!",
    "Tag someone who needs to hear this today.",
    "What does this verse mean to you?",
]


def _pick_rotating(pool: list[str], index: int) -> str:
    return pool[index % len(pool)]


def _pick_rotating_pair(pool_te: list[str], pool_en: list[str], index: int) -> tuple[str, str]:
    i = index % len(pool_te)
    return pool_te[i], pool_en[i]


def build_gita_sloka_seo(sloka: GitaSloka, sloka_index: int, for_date_ordinal: int) -> ShortSeoContent:
    """Build title/description/hashtags for one Gita Sloka Short."""
    pick_index = for_date_ordinal + sloka_index
    ref = f"{sloka.chapter}.{sloka.verse}"
    title = _pick_rotating(_TITLE_TEMPLATES, pick_index).format(ref=ref)

    hook_te, hook_en = _pick_rotating_pair(_HOOKS_TE, _HOOKS_EN, pick_index)
    cta_te, cta_en = _pick_rotating_pair(_CTAS_TE, _CTAS_EN, pick_index + 1)
    comment_en = _pick_rotating(_COMMENT_PROMPTS_EN, pick_index + 2)
    comment_te = "ఈ శ్లోకం మీకు ఎలా అనిపించిందో కామెంట్‌లో చెప్పండి!"

    description_te = (
        f"{hook_te}\n\n"
        f"{sloka.sanskrit_deva}\n\n"
        f"అర్థం: {sloka.telugu_meaning}\n"
        f"అధ్యాయం {sloka.chapter}, శ్లోకం {sloka.verse} — {sloka.chapter_name_te}\n\n"
        f"{cta_te}\n\n{comment_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"Transliteration: {sloka.transliteration}\n"
        f"Bhagavad Gita, Chapter {sloka.chapter}, Verse {sloka.verse}\n\n"
        f"{cta_en}\n\n{comment_en}"
    )

    from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # reused, not duplicated

    description = (
        f"{brand_tagline('gita_sloka')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_GITA_HASHTAGS]
    hashtags.append(_pick_rotating(_ROTATING_POOL, pick_index))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
