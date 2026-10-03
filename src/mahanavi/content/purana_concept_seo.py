"""
SEO content (titles, descriptions, hashtags) for the "Purana Concept"
Shorts series -- mirrors purana_short_seo.py's already-validated
structure (same ShortSeoContent shape, rotating title templates/hooks/
CTAs/comment-prompts, bilingual description with the shared channel
footer), adapted for this series' per-entry concept_type instead of a
single story shape.

Per explicit request (2026-10-02: "make the best seo for every thing
what we did till now like the 5 to 6 pm posting also and this also") --
this module is held to the same bar as purana_short_seo.py, not a
stripped-down version of it.

POSTING TIME: 11 AM-1 PM IST (purana_concept_gate.py) -- a daytime slot
distinct from both the 12-1 AM alert Shorts and the 5-6 PM Purana Story
Shorts, per explicit request.
"""

from __future__ import annotations

from mahanavi.content.alert_seo import ShortSeoContent  # reuse the same shape
from mahanavi.content.branding import brand_tagline
from mahanavi.content.purana_concept_shorts import ConceptType, PuranaConceptShort

_CONCEPT_HASHTAGS = ["#పురాణవిశేషాలు", "#PuranaFacts", "#భక్తి"]

_ROTATING_POOL = [
    "#TeluguDevotional", "#Devotional", "#Bhakti", "#HinduMythology",
    "#IndianMythology", "#Spirituality", "#SanatanaDharma",
]

# Per-concept-type title templates -- {title} = the entry's Telugu title.
# Phrased to fit each concept's own natural hook (a quiz teases a
# reveal, a trivia list teases a count, a sloka teases a meaning), same
# curiosity-first approach already validated for the other series.
_TITLE_TEMPLATES: dict[ConceptType, list[str]] = {
    ConceptType.SLOKA: [
        "{title} - ఈ శ్లోకం అర్థం తెలుసా?",
        "{title} | Puranic Sloka",
        "{title} - నేటి పురాణ వాక్యం",
    ],
    ConceptType.SACRED_PLACE: [
        "{title} - ఈ క్షేత్ర మహత్యం తెలుసా?",
        "{title} | Sacred Place Facts",
        "{title} - పురాణాల్లో ఈ క్షేత్రం",
    ],
    ConceptType.VRATHA: [
        "{title} - ఈ వ్రతం ఫలితం తెలుసా?",
        "{title} | Vratha Mahatyam",
        "{title} - ఈ వ్రత విధానం చూడండి",
    ],
    ConceptType.DHARMA_QA: [
        "{title} - సమాధానం తెలుసా?",
        "{title} | Dharma Q&A",
        "ధర్మ సందేహం: {title}",
    ],
    ConceptType.TRIVIA_LIST: [
        "{title} - పూర్తి లిస్ట్ తెలుసా?",
        "{title} | Puranic Trivia",
        "{title} - అన్నీ గుర్తుపెట్టుకోగలరా?",
    ],
    ConceptType.CHARACTER_QUIZ: [
        "{title} - ఈ పాత్ర ఎవరో చెప్పగలరా?",
        "{title} | Guess the Character",
        "{title} - చివరివరకు చూడండి",
    ],
}

_HOOKS_TE = [
    "మన పురాణాల్లో దాగి ఉన్న ఒక విశేషం ఇది.",
    "18 పురాణాల్లో నుండి ఎంచుకున్న ఒక ఆసక్తికరమైన విషయం.",
    "ఇది తెలుసుకుంటే మీ పురాణ జ్ఞానం పెరుగుతుంది.",
    "పెద్దలు చెప్పే పురాణ విశేషాల్లో ఇది ఒకటి.",
    "మన సంస్కృతిలో నిక్షిప్తమైన ఒక సత్యం ఇది.",
]
_HOOKS_EN = [
    "A fascinating detail hidden in our Puranas.",
    "A pick from across all 18 Puranas.",
    "Knowing this adds to your Puranic knowledge.",
    "One of the classic details passed down by our elders.",
    "A truth preserved in our culture for generations.",
]

_CTAS_TE = [
    "ప్రతిరోజు ఇలాంటి పురాణ విశేషాల కోసం ఫాలో అవ్వండి.",
    "ఇది నచ్చితే షేర్ చేయండి.",
    "మీకు తెలిసిన పురాణ విశేషం కామెంట్‌లో చెప్పండి.",
]
_CTAS_EN = [
    "Follow for a new Puranic concept every day.",
    "Share this if you found it interesting.",
    "Tell us a Puranic fact you know in the comments.",
]

_COMMENT_PROMPTS_EN = [
    "Which Purana should we cover next? Comment below!",
    "Tag someone who'd enjoy this.",
    "Did you know this already? Let us know!",
]


def _pick_rotating(pool: list[str], index: int) -> str:
    return pool[index % len(pool)]


def _pick_rotating_pair(pool_te: list[str], pool_en: list[str], index: int) -> tuple[str, str]:
    i = index % len(pool_te)
    return pool_te[i], pool_en[i]


def build_purana_concept_seo(
    concept: PuranaConceptShort, concept_index: int, for_date_ordinal: int,
) -> ShortSeoContent:
    """Build title/description/hashtags for one Purana Concept Short."""
    pick_index = for_date_ordinal + concept_index
    templates = _TITLE_TEMPLATES[concept.concept_type]
    title = templates[pick_index % len(templates)].format(title=concept.title_te)

    hook_te, hook_en = _pick_rotating_pair(_HOOKS_TE, _HOOKS_EN, pick_index)
    cta_te, cta_en = _pick_rotating_pair(_CTAS_TE, _CTAS_EN, pick_index + 1)
    comment_en = _pick_rotating(_COMMENT_PROMPTS_EN, pick_index + 2)
    comment_te = "మీకు తెలిసిన పురాణ విశేషం కామెంట్‌లో చెప్పండి!"

    description_te = (
        f"{hook_te}\n\n"
        f"{concept.body_te}\n\n"
        f"మూలం: {concept.purana_name_te}\n\n"
        f"{cta_te}\n\n{comment_te}"
    )
    description_en = (
        f"{hook_en}\n\n"
        f"Source: {concept.purana_name_en}\n\n"
        f"{cta_en}\n\n{comment_en}"
    )

    from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE  # reused, not duplicated

    description = (
        f"{brand_tagline('purana_concept')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_CONCEPT_HASHTAGS]
    hashtags.append(_pick_rotating(_ROTATING_POOL, pick_index))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
