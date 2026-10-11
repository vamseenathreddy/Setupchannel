"""
SEO content (titles, descriptions, hashtags) for the "Rashi Mantra of the
Month" Shorts series. Mirrors the structure of alert_seo.py -- same
ShortSeoContent shape, same bilingual Telugu-first/English-second
description layout, same rotating-by-date title pools, same #Shorts-first
hashtag convention -- but built separately because this series' content
unit is a RASHI (12 of them, cycled one per post), not a CALENDAR DATE, so
titles rotate by (date, rashi) together rather than by date alone.

RESEARCHED TITLE/DESCRIPTION PATTERNS (2026-10-01), from screenshots the
user sent of real competitor channels that YouTube's own "audience also
watches" panel surfaced for this channel (Kenisha Channel, Bhakti Kripa,
ManaDevuduTelugu, Telugu Inspiration Hub):
  - Their highest-performing zodiac/temple-fact Shorts use a QUESTION-hook
    title ("... తెలుసా?" / "...తో ఏం జరుగుతుంది?") far more than a flat
    statement -- curiosity outperforms description. Example: a zodiac
    Short titled as a question about sons/daughters' abilities per rashi
    hit 71k views on a 20k-subscriber channel.
  - Titles stay short, name the rashi explicitly (so it reads clearly in
    the Shorts feed's small title area), and do not bury the hook.
  - Descriptions on these channels are thin (little more than the title
    restated); this channel's own convention (alert_seo.py) already beats
    that with a real bilingual, keyword-rich description plus a channel
    footer, which is kept here rather than copying competitors' thinner
    approach -- their thin descriptions are not what's driving their
    views (the hook/title and static-card format are), so there is
    nothing to lose and real SEO surface area to gain by keeping ours
    fuller.

POSTING TIME (researched 2026-10-01, see sources in the function this
reply's text cites): religious/devotional content on YouTube Shorts peaks
in a ~2-5 PM UTC window, i.e. roughly 7:30-10:30 PM IST, with Monday the
single most active day for religious content specifically. That is a
DIFFERENT window from the existing alert Shorts (posted ~12-3 AM IST,
because Rahu Kalam/Shubha Ghadiyalu are only useful if seen before the
day's events they describe). This series carries no such deadline -- it's
evergreen -- so it should run in that evening engagement window instead,
not the same early-morning slot. See build_rashi_mantra_seo's docstring
for the concrete recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ytcore.content.alert_seo import ShortSeoContent  # reuse the same shape
from ytcore.content.branding import brand_tagline
from ytcore.content.rashi_current_transits import ShaniTransitStatus
from ytcore.content.rashi_mantra_content import RashiMantraContent

# Niche hashtags for this series specifically (distinct from the alert
# Shorts' Panchang-focused tags).
_RASHI_HASHTAGS = ["#రాశిఫలాలు", "#RashiMantra", "#జాతకం"]

# Same rotating devotional pool used by alert_seo.py, reused here for
# consistency rather than duplicated with a different list.
_ROTATING_POOL = [
    "#TeluguPanchangam", "#Devotional", "#Bhakti", "#HinduDevotional",
    "#DailyPanchangam", "#Spirituality",
]

# Title templates take {rashi} (the Telugu rashi name). Every entry mixes
# Telugu+English in the SAME string (same requirement as alert_seo.py),
# and is phrased as a question/hook per the competitor pattern above,
# rather than a flat "X's mantra is Y" statement.
_TITLE_TEMPLATES = [
    "Rashi Mantra | {rashi} వారికి ఈ మంత్రం తెలుసా?",
    "{rashi} Rashi Mantra - మీకు తెలుసా?",
    "Rashi Mantra | {rashi} వారు ఈ మంత్రం వినాలి!",
    "{rashi} Rashi - ఈ మంత్రం Try చేయండి",
    "{rashi} వారికి Special మంత్రం ఇదే",
    "{rashi} Zodiac Mantra - ఈ నెల",
    "Rashi Mantra | {rashi} రాశివారి అదృష్ట మంత్రం",
    "{rashi} Rashi - ఈ మంత్రం జపించండి",
    "Rashi Mantra | {rashi} వారి సమస్యలకు ఈ మంత్రం పరిష్కారం",
    "{rashi} Mantra For Luck - తెలుసుకోండి",
    "Rashi Mantra | {rashi} రాశివారు మిస్ అవ్వకండి!",
    "{rashi} Rashi Mantra Of The Month",
    "Rashi Mantra | {rashi} వారికి ఈ శ్లోకం ఎందుకు ముఖ్యం?",
    "{rashi} Rashi - ఈ మంత్రం ఫలితం ఏంటి?",
    "Rashi Mantra | {rashi} వారి గ్రహ దోష నివారణ మంత్రం",
    "{rashi} Rashi Mantra - Watch Till End",
    "Rashi Mantra | {rashi} వారికి ఈ మంత్రం ఎందుకు చెప్పాలి?",
    "{rashi} Zodiac - ఈ మంత్రం రోజూ చదవండి",
    "Rashi Mantra | {rashi} రాశివారి జీవితం మారే మంత్రం",
    "{rashi} Rashi - ఈ చిన్న మంత్రం పెద్ద ఫలితం",
]

# Hook lines paired by index (Telugu/English), same pattern as alert_seo.py.
_HOOKS_TE = [
    "ప్రతి రాశికి ఒక ప్రత్యేక మంత్రం ఉంటుంది, మీదీ చూడండి.",
    "జ్యోతిష్యం ప్రకారం ప్రతి రాశికి ఒక అధిపతి గ్రహం ఉంటుంది.",
    "ఈ మంత్రం రోజూ జపిస్తే మంచి ఫలితాలు కలుగుతాయని నమ్మకం.",
    "మీ రాశి అధిపతి గ్రహాన్ని శాంతింపజేసే మంత్రం ఇదే.",
    "పెద్దలు చెప్పే ప్రకారం ఈ మంత్రం ప్రతి రాశివారికి ప్రత్యేకం.",
]
_HOOKS_EN = [
    "Every rashi has its own special mantra -- here's yours.",
    "According to Jyotisha, every rashi has a ruling planet.",
    "Chanting this daily is traditionally said to bring good results.",
    "This is the mantra that is said to pacify your rashi's ruling planet.",
    "As per tradition, this mantra is special to your rashi.",
]

_CTAS_TE = [
    "ప్రతి నెలా మీ రాశి మంత్రం కోసం ఫాలో అవ్వండి.",
    "మీ రాశి తెలుసుకుని ఈ మంత్రం జపించండి.",
    "ఈ మంత్రం మీకు నచ్చితే షేర్ చేయండి.",
]
_CTAS_EN = [
    "Follow for your rashi's mantra every month.",
    "Find your rashi and chant this mantra regularly.",
    "Share this if it resonated with you.",
]

_COMMENT_PROMPTS_EN = [
    "Comment your rashi below and tag someone who needs this!",
    "Which rashi are you? Let us know in the comments.",
    "Tag a friend from this rashi in the comments!",
]


def _pick_rotating(pool: list[str], index: int) -> str:
    return pool[index % len(pool)]


def _pick_rotating_pair(pool_te: list[str], pool_en: list[str], index: int) -> tuple[str, str]:
    i = index % len(pool_te)
    return pool_te[i], pool_en[i]


def build_rashi_mantra_seo(
    content: RashiMantraContent,
    rashi_index: int,
    for_date_ordinal: int,
    transit: ShaniTransitStatus | None = None,
) -> ShortSeoContent:
    """Build title/description/hashtags for one Rashi Mantra Short.

    POSTING TIME RECOMMENDATION (the user's other explicit ask in this
    request): post in the EVENING window, roughly 7:30-9:00 PM IST, not
    the early-morning window used for the Rahu Kalam/Shubha Ghadiyalu
    alert Shorts. Reasoning: those alerts are time-sensitive (useless
    once the day's muhurtam has passed, so they must be up before the
    morning), while this series is evergreen -- nothing about chanting a
    rashi's ruling-planet mantra goes stale by being seen at 8 PM instead
    of 6 AM. Independent research into religious-content Shorts
    performance (opus.pro's dataset of 214k religious clips, 2026) found
    the actual peak engagement window across platforms is ~2-5 PM UTC,
    which is 7:30-10:30 PM IST, with Monday the single most active
    posting day for religious content specifically. Within that window,
    Saturday is also worth favoring specifically for any post where
    `transit` is set (the five Sade Sati/Ashtama/Kantaka Shani rashis),
    since Saturday is traditionally Shani's own day -- the card's own
    chant-count line already says so ("శనివారం ఉత్తమం"). So: run this
    series daily around 7:30-8:30 PM IST, and if posting only a few times
    a week to start, prioritize Mondays and Saturdays.
    """
    rashi_pick_index = for_date_ordinal + rashi_index
    title = _pick_rotating(_TITLE_TEMPLATES, rashi_pick_index).format(rashi=f"{content.name_te} {content.name_en}")

    hook_te, hook_en = _pick_rotating_pair(_HOOKS_TE, _HOOKS_EN, rashi_pick_index)
    cta_te, cta_en = _pick_rotating_pair(_CTAS_TE, _CTAS_EN, rashi_pick_index + 1)
    comment_en = _pick_rotating(_COMMENT_PROMPTS_EN, rashi_pick_index + 2)
    comment_te = "మీ సన్నిహితుల కోసం మీరే ఈ మంత్రం జపించవచ్చు, వారి పేరు గోత్రం కామెంట్‌లో చెప్పండి!"

    transit_line_te = f"\n\n{transit.status_label_te}: {transit.note_te}" if transit else ""
    transit_line_en = ""
    if transit:
        # Short, honest English gloss -- not a literal re-translation,
        # since the Telugu line names a specific Jyotisha term (Sade
        # Sati/Ashtama/Kantaka Shani) that a direct word-for-word
        # translation would obscure rather than clarify.
        transit_line_en = (
            f"\n\nCurrent Shani (Saturn) transit note for {content.name_en}: this mantra is "
            "traditionally used for relief during this period."
        )

    description_te = (
        f"{hook_te}\n\n"
        f"{content.name_te} ({content.symbol_te}) రాశి అధిపతి: {content.ruling_planet_te}\n"
        f"మంత్రం: {content.mantra_te}\n"
        f"({content.mantra_transliteration})\n"
        f"జప సంఖ్య: {content.chant_count_te}\n"
        f"ఈ మంత్రం వల్ల: {content.benefit_te}"
        f"{transit_line_te}\n\n"
        f"{cta_te}\n\n{comment_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"{content.name_en} -- Ruling planet: {content.ruling_planet_en}\n"
        f"Mantra: {content.mantra_te} ({content.mantra_transliteration})\n"
        f"Recommended chanting: {content.chant_count_te}\n"
        f"Traditionally chanted for: {content.benefit_te}"
        f"{transit_line_en}\n\n"
        f"{cta_en}\n\n{comment_en}"
    )

    # Reuse the exact same channel footer block as the alert Shorts for a
    # single consistent channel identity across both series.
    from ytcore.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # local import: these are intentionally "private" module constants, reused here rather than duplicated

    description = (
        f"{brand_tagline('rashi_mantra')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_RASHI_HASHTAGS, f"#{content.name_en.split(' ')[0]}"]
    hashtags.append(_pick_rotating(_ROTATING_POOL, rashi_pick_index))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
