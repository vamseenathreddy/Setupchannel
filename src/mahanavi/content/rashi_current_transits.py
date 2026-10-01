"""
Current Saturn (Shani) transit status per rashi -- makes the Rashi Mantra
series respond to "sani and other situation" (explicit user request,
2026-10-01), not just show a fixed evergreen ruling-planet mantra.

WHY THIS IS HARDCODED, NOT A LIVE API CALL: per explicit product decision
for this series (same conversation), it does NOT call the Prokerala API
-- that's reserved for the daily alert Shorts, whose Panchang values
(tithi/nakshatra/rahu kalam) genuinely change every day. A planet's
RASHI position does not change daily -- Saturn spends roughly 2.5 years
in each sign, Jupiter roughly 1 year -- so this is slow-moving, publicly
published astronomical data that can be researched periodically (web
search) and typed in here, exactly like the Puranas content elsewhere
in this codebase, rather than fetched live.

RESEARCHED 2026-10-01 (sources: grahai.com/transit/saturn-pisces-2026,
muhuratchoghadiya.com/en/shani-gochar): Saturn entered Meena (Pisces) in
March 2025 and remains there until roughly mid-2027. During this transit:

  - Sade Sati (7.5-year Saturn cycle, 3 phases of ~2.5 years each):
      Mesha    -- 1st phase (Saturn in the 12th house from Moon sign)
      Meena    -- 2nd/peak phase (Saturn directly on the Moon sign)
      Kumbha   -- 3rd/ending phase (Saturn in the 2nd house)
  - Ashtama Shani (Saturn in the 8th house, a distinct ~2.5-year period):
      Simha
  - Kantaka Shani (Saturn in the 4th house):
      Dhanussu

For these 5 rashis, the card shows the classic Shani beej (seed) mantra
-- "ఓం ప్రాం ప్రీం ప్రౌం సః శనయే నమః" -- instead of their usual
ruling-planet mantra, since that is the traditional remedy specifically
associated with Sade Sati / Ashtama / Kantaka Shani relief, not just
"Saturn is their ruling planet" (which is separately already true for
Makara and Kumbha year-round, unrelated to this transit). Also ancient,
public-domain liturgical Sanskrit -- same copyright basis as the rest of
this series.

MAINTENANCE: re-research and update this file when Saturn changes rashi
(next expected ~mid-2027) -- search "Shani Gochar <year>" or "Saturn
transit <year>" and update AFFECTED_RASHIS accordingly. Until then this
file does not need to change; the status is correct for all of 2026.
"""

from __future__ import annotations

from dataclasses import dataclass

SHANI_REMEDY_MANTRA_TE = "ఓం ప్రాం ప్రీం ప్రౌం సః శనయే నమః"
SHANI_REMEDY_MANTRA_TRANSLITERATION = "Om Pram Preem Proum Sah Shanaye Namah"
SHANI_REMEDY_CHANT_COUNT_TE = "108 సార్లు, శనివారం ఉత్తమం"  # "108 times, Saturday is best" -- plain text, NOT pre-wrapped in parens (the renderer wraps every chant count in one pair of parens; wrapping here too produced a visible "))" double-paren bug on a real render)


@dataclass(frozen=True, slots=True)
class ShaniTransitStatus:
    status_label_te: str  # e.g. "శని సాడే సాటి (2వ దశ)"
    note_te: str  # one short line explaining it, shown on the card in place of the usual benefit


# Keyed by RashiMantraContent.name_en (e.g. "Mesha (Aries)") for an
# unambiguous, typo-resistant lookup against rashi_mantra_content.py.
AFFECTED_RASHIS: dict[str, ShaniTransitStatus] = {
    "Mesha (Aries)": ShaniTransitStatus(
        status_label_te="శని సాడే సాటి ప్రారంభం",
        note_te="శని సాడే సాటి ప్రభావం నుండి ఉపశమనానికి ఈ మంత్రం స్పెషల్",
    ),
    "Simha (Leo)": ShaniTransitStatus(
        status_label_te="అష్టమ శని ప్రభావం",
        note_te="అష్టమ శని ప్రభావం నుండి ఉపశమనానికి ఈ మంత్రం స్పెషల్",
    ),
    "Dhanussu (Sagittarius)": ShaniTransitStatus(
        status_label_te="కంటక శని ప్రభావం",
        note_te="కంటక శని ప్రభావం నుండి ఉపశమనానికి ఈ మంత్రం స్పెషల్",
    ),
    "Kumbha (Aquarius)": ShaniTransitStatus(
        status_label_te="శని సాడే సాటి ముగింపు దశ",
        note_te="శని సాడే సాటి ప్రభావం నుండి ఉపశమనానికి ఈ మంత్రం స్పెషల్",
    ),
    "Meena (Pisces)": ShaniTransitStatus(
        status_label_te="శని సాడే సాటి పతాక దశ",
        note_te="శని సాడే సాటి ప్రభావం నుండి ఉపశమనానికి ఈ మంత్రం స్పెషల్",
    ),
}
