"""
category_comments.py: builds the short, rotating category-tag comment
posted (via YouTubeShortsUploader.post_comment) on every Short across
every series on this channel, per explicit request (2026-10-03):
"also post for every short a comment with short text like muhurtas
slokas puranas quiz etc.."

SPAM-SAFETY DESIGN (the user explicitly asked whether this risks a
spam flag from YouTube over time -- this module's design is the
direct answer to that):
  - This is the CHANNEL OWNER commenting once on their OWN upload, not
    mass-commenting on other people's videos -- the pattern YouTube's
    abuse systems actually target. Volume is tiny: one comment per
    Short, matching the channel's own ~7 posts/day pace.
  - The real spam/low-quality signals this module deliberately avoids:
    no links, no engagement-bait ("follow for follow"), and no
    byte-identical text forever -- each category has a small ROTATING
    pool (same deterministic by-date rotation pattern used everywhere
    else in this codebase: titles, hooks, CTAs), so the exact wording
    varies day to day even though the category stays consistent.
  - One comment per video, posted once, right after upload -- never
    re-posted or edited.

Deliberately a plain module-level dict, not per-series content files,
since this is genuinely small and shared across all 7 series.
"""

from __future__ import annotations

_MUHURTAS_POOL = [
    "#ముహూర్తాలు 🙏 ప్రతిరోజు ఇలాంటి వీడియోల కోసం ఫాలో అవ్వండి",
    "ముహూర్తాలు & పంచాంగం సిరీస్ — రోజూ కొత్త అప్డేట్",
    "#పంచాంగం ప్రతిరోజు ఈ సమయంలో అప్డేట్ అవుతుంది",
]
_SLOKAS_POOL = [
    "#గీతాశ్లోకాలు 🙏 ప్రతిరోజు ఒక కొత్త శ్లోకం",
    "భగవద్గీత శ్లోకాల సిరీస్ — రోజూ ఒకటి నేర్చుకుందాం",
    "#శ్లోకాలు రోజూ ఈ సమయంలో కొత్తది వస్తుంది",
]
# Expanded (explicit request, 2026-10-04): "mention about bhagavadgeetha
# telugu knowledge. And telugu lo bhagavadgeetha quiz like that indicate
# bhagavadgeeta #tags add rotating big seo ... people are looking this
# kind of content" -- every entry now explicitly names Telugu Bhagavad
# Gita knowledge/quiz (the actual search phrase people use) and carries
# several single-word hashtags (no spaces, so none of YouTube's
# tag-quoting rules apply to a plain comment anyway, but kept consistent
# with the rest of this codebase's tag style). Grown from 3 to 5 entries
# so the rotation reads less repetitive over the ~every-other-day cadence.
_QUIZ_POOL = [
    "#క్విజ్ 🧠 తెలుగులో భగవద్గీత జ్ఞానాన్ని పరీక్షించుకోండి #TeluguBhagavadGita #GitaQuizTelugu",
    "భగవద్గీత క్విజ్ సిరీస్ — ప్రతి రెండో రోజు పాల్గొనండి #BhagavadGitaQuiz #SanatanaDharma",
    "#Quiz సమాధానం కామెంట్‌లో చెప్పండి! #GitaQuiz #TeluguSpiritualQuiz",
    "తెలుగులో భగవద్గీత పరిజ్ఞానం ఎంతుందో చూద్దాం 🙏 #GitaJnanam #HinduQuizTelugu",
    "మీ భగవద్గీత నాలెడ్జ్ టెస్ట్ చేయండి #భగవద్గీతక్విజ్ #TeluguBhagavadGitaQuiz",
]
_PURANAS_POOL = [
    "#పురాణకథలు 🙏 ప్రతిరోజు కొత్త కథ",
    "పురాణాల సిరీస్ — రోజూ ఈ సమయంలో కొత్తది",
    "#పురాణాలు మా ఛానల్‌లో ప్రతిరోజు",
]
_RASHI_POOL = [
    "#రాశిమంత్రాలు 🙏 మీ రాశి కామెంట్‌లో చెప్పండి",
    "రాశి మంత్రాల సిరీస్ — నెలవారీ అప్డేట్",
    "#రాశిమంత్రం ప్రతి పోస్ట్‌కి ఫాలో అవ్వండి",
]

_POOLS: dict[str, list[str]] = {
    "muhurtas": _MUHURTAS_POOL,
    "slokas": _SLOKAS_POOL,
    "quiz": _QUIZ_POOL,
    "puranas": _PURANAS_POOL,
    "rashi": _RASHI_POOL,
}


def build_category_comment(category: str, for_date_ordinal: int, topic_te: str | None = None) -> str:
    """category: one of "muhurtas", "slokas", "quiz", "puranas", "rashi".
    Deterministic by-date rotation through that category's pool --
    reproducible for a given date, varies day to day.

    topic_te (explicit request, 2026-10-04): "Today it posted about
    druva Nakshatram. In comment also it should mention about
    druvanakshatram like that" -- the generic category line alone
    ("#పురాణకథలు ప్రతిరోజు కొత్త కథ") didn't say what TODAY'S story was
    actually about. When given (post_purana_short.py passes the
    story's own search_keyword_te), it's appended as a second line
    naming today's specific topic/hashtag -- optional and unused by
    every other category's call site, which keeps their existing
    generic-only comment unchanged."""
    pool = _POOLS[category]
    base = pool[for_date_ordinal % len(pool)]
    if topic_te:
        keyword_tag = "#" + topic_te.replace(" ", "")
        return f"{base}\nనేటి కథ: {topic_te} {keyword_tag}"
    return base
