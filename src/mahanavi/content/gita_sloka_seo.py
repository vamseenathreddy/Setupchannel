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
from mahanavi.content.gita_sloka_quiz import GitaQuizOptions

_GITA_HASHTAGS = ["#భగవద్గీత", "#BhagavadGita", "#GitaWisdom"]

_ROTATING_POOL = [
    "#TeluguDevotional", "#Devotional", "#Bhakti", "#Krishna",
    "#SanatanaDharma", "#Spirituality",
]

# {title} = "చాప్టర్ {chapter}.{verse}" style reference the formatter
# below builds -- kept separate from the template so chapter/verse stay
# numerals (easier to scan in a title) rather than spelled out.
_TITLE_TEMPLATES = [
    "Bhagavad Gita | భగవద్గీత {ref} - అర్థం తెలుసా?",
    "గీతా శ్లోకం {ref} | Bhagavad Gita",
    "Bhagavad Gita | నేటి గీతా సందేశం - {ref}",
    "Bhagavad Gita | {ref} - ఈ శ్లోకం జీవితాన్ని మారుస్తుంది",
    "Bhagavad Gita | కృష్ణుడి మాట - {ref}",
    "Bhagavad Gita | భగవద్గీత {ref} - వినండి, అర్థం చేసుకోండి",
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


def build_gita_sloka_seo(
    sloka: GitaSloka, sloka_index: int, for_date_ordinal: int,
    previous_quiz_sloka: GitaSloka | None = None,
) -> ShortSeoContent:
    """Build title/description/hashtags for one Gita Sloka Short.

    previous_quiz_sloka (explicit request, 2026-10-03) -- when given,
    echoes yesterday's quiz question and its correct answer in the
    description too, matching the same reveal shown on the card itself
    (gita_sloka_card_renderer.py)."""
    pick_index = for_date_ordinal + sloka_index
    ref = f"{sloka.chapter}.{sloka.verse}"
    title = _pick_rotating(_TITLE_TEMPLATES, pick_index).format(ref=ref)

    hook_te, hook_en = _pick_rotating_pair(_HOOKS_TE, _HOOKS_EN, pick_index)
    cta_te, cta_en = _pick_rotating_pair(_CTAS_TE, _CTAS_EN, pick_index + 1)
    comment_en = _pick_rotating(_COMMENT_PROMPTS_EN, pick_index + 2)
    comment_te = "ఈ శ్లోకం మీకు ఎలా అనిపించిందో కామెంట్‌లో చెప్పండి!"

    yesterday_te = yesterday_en = ""
    if previous_quiz_sloka is not None:
        p = previous_quiz_sloka
        yesterday_te = f"\n\nనిన్నటి ప్రశ్న & జవాబు: ఏ అధ్యాయంలోనిది? — అధ్యాయం {p.chapter}, శ్లోకం {p.verse}"
        yesterday_en = f"\n\nYesterday's quiz answer: Chapter {p.chapter}, Verse {p.verse}"

    description_te = (
        f"{hook_te}\n\n"
        f"{sloka.sanskrit_deva}\n\n"
        f"అర్థం: {sloka.telugu_meaning}\n"
        f"అధ్యాయం {sloka.chapter}, శ్లోకం {sloka.verse} — {sloka.chapter_name_te}\n\n"
        f"{cta_te}\n\n{comment_te}{yesterday_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"Transliteration: {sloka.transliteration}\n"
        f"Bhagavad Gita, Chapter {sloka.chapter}, Verse {sloka.verse}\n\n"
        f"{cta_en}\n\n{comment_en}{yesterday_en}"
    )

    from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # reused, not duplicated

    description = (
        f"{brand_tagline('gita_sloka')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_GITA_HASHTAGS]
    hashtags.append(_pick_rotating(_ROTATING_POOL, pick_index))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)


# --- Quiz-day SEO (every other day -- see gita_sloka_quiz.py) ----------

_QUIZ_TITLE_TEMPLATES = [
    "నిన్నటి శ్లోకం గుర్తుందా? Quiz Time!",
    "Gita Quiz - నిన్నటి శ్లోకం ఏ అధ్యాయం?",
    "మీకు గుర్తుందా? భగవద్గీత Quiz",
    "Quiz: నిన్నటి శ్లోకం ఎక్కడిది?",
]

_QUIZ_HOOKS_TE = [
    "నిన్నటి గీతా శ్లోకం మీకు గుర్తుందా? ఒకసారి ట్రై చేయండి!",
    "చిన్న Quiz టైమ్ — నిన్నటి శ్లోకం ఏ అధ్యాయంలోనిదో గుర్తుందా?",
    "మీరు నిన్న చూసిన శ్లోకం ఇదే. ఏ అధ్యాయంలోనిదో చెప్పగలరా?",
]
_QUIZ_HOOKS_EN = [
    "Do you remember yesterday's Gita verse? Give this a try!",
    "Quick quiz time — do you remember yesterday's chapter and verse?",
    "This is the verse we posted yesterday. Can you name the chapter and verse?",
]

_QUIZ_CTAS_TE = [
    "మీ సమాధానం (A/B/C/D) కామెంట్‌లో రాయండి!",
    "మీ జవాబు కామెంట్‌లో చెప్పండి — సరైనదేనో చూద్దాం!",
]
_QUIZ_CTAS_EN = [
    "Write your answer (A/B/C/D) in the comments!",
    "Drop your answer in the comments — let's see if you got it right!",
]

_QUIZ_COMMENT_PROMPTS_EN = [
    "Not sure? Check yesterday's Short on our channel to confirm!",
    "Rewatch yesterday's video on our channel if you need a hint!",
    "Our Shorts tab has yesterday's verse if you want to double-check!",
]

# Quiz-specific SEO hashtag pool (explicit request, 2026-10-04: "telugu
# lo bhagavadgeetha quiz like that indicate bhagavadgeeta #tags add
# rotating big seo ... people are looking this kind of content, it
# should reach them") -- targets the actual search phrases people use
# ("telugu bhagavad gita quiz", "gita quiz telugu") rather than only the
# generic devotional tags in _ROTATING_POOL above. Two picks per video
# (different offsets below, spread across this 6-entry pool) widen reach
# without bloating the tag list -- still well under YouTube's 500-char
# tag limit (single words, no spaces, so none hit the tag-quoting rule
# discovered during the Navaratri Day 2 upload).
_QUIZ_ROTATING_POOL = [
    "#TeluguBhagavadGita", "#GitaQuizTelugu", "#BhagavadGitaQuiz",
    "#TeluguSpiritualQuiz", "#GitaJnanam", "#HinduQuizTelugu",
]


def build_gita_sloka_quiz_seo(
    quiz: GitaQuizOptions, for_date_ordinal: int, next_verse_hint: GitaSloka | None = None,
) -> ShortSeoContent:
    """Build title/description/hashtags for a Gita Sloka QUIZ-day Short.

    The correct answer is deliberately NOT stated anywhere in this
    description -- the entire point (explicit request, 2026-10-03) is
    to send viewers back to yesterday's Short on the channel to check,
    not to let them read the answer here.

    next_verse_hint (explicit request, 2026-10-03: "repati short lo yem
    nerchukobotunnamo hint or intro") -- when given, echoes the same
    one-line "tomorrow's chapter" teaser shown on the card itself."""
    pick_index = for_date_ordinal
    title = _pick_rotating(_QUIZ_TITLE_TEMPLATES, pick_index)

    hook_te, hook_en = _pick_rotating_pair(_QUIZ_HOOKS_TE, _QUIZ_HOOKS_EN, pick_index)
    cta_te, cta_en = _pick_rotating_pair(_QUIZ_CTAS_TE, _QUIZ_CTAS_EN, pick_index + 1)
    comment_en = _pick_rotating(_QUIZ_COMMENT_PROMPTS_EN, pick_index + 2)
    comment_te = "సమాధానం తెలియకపోతే నిన్నటి Short చూడండి!"

    option_lines_te = "\n".join(
        f"{letter}) అధ్యాయం {s.chapter}, శ్లోకం {s.verse}"
        for letter, s in zip(["A", "B", "C", "D"], quiz.options)
    )
    option_lines_en = "\n".join(
        f"{letter}) Chapter {s.chapter}, Verse {s.verse}"
        for letter, s in zip(["A", "B", "C", "D"], quiz.options)
    )

    hint_te = hint_en = ""
    if next_verse_hint is not None:
        hint_te = f"\n\nరేపు {next_verse_hint.chapter_name_te} నుండి ఒక కొత్త శ్లోకం — మిస్ అవ్వకండి!"
        hint_en = f"\n\nTomorrow: a new verse from {next_verse_hint.chapter_name_te} -- don't miss it!"

    description_te = (
        f"{hook_te}\n\n"
        f"{quiz.target.sanskrit_deva}\n\n"
        f"ఈ శ్లోకం ఏ అధ్యాయంలోనిది?\n{option_lines_te}\n\n"
        f"{cta_te}\n\n{comment_te}{hint_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"Which chapter & verse is this?\n{option_lines_en}\n\n"
        f"{cta_en}\n\n{comment_en}{hint_en}"
    )

    from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # reused, not duplicated

    description = (
        f"{brand_tagline('gita_sloka')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_GITA_HASHTAGS, "#Quiz"]
    hashtags.append(_pick_rotating(_ROTATING_POOL, pick_index))
    hashtags.append(_pick_rotating(_QUIZ_ROTATING_POOL, pick_index + 1))
    hashtags.append(_pick_rotating(_QUIZ_ROTATING_POOL, pick_index + 4))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
