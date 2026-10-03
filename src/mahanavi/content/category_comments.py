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
_QUIZ_POOL = [
    "#క్విజ్ 🧠 మీ జ్ఞానాన్ని పరీక్షించుకోండి",
    "భగవద్గీత క్విజ్ సిరీస్ — ప్రతి రెండో రోజు పాల్గొనండి",
    "#Quiz సమాధానం కామెంట్‌లో చెప్పండి!",
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


def build_category_comment(category: str, for_date_ordinal: int) -> str:
    """category: one of "muhurtas", "slokas", "quiz", "puranas", "rashi".
    Deterministic by-date rotation through that category's pool --
    reproducible for a given date, varies day to day."""
    pool = _POOLS[category]
    return pool[for_date_ordinal % len(pool)]
