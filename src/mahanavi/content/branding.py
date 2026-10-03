"""
branding.py: the channel's brand name and one short "<series> by
Mahanavi Spirituals" tagline per series, prepended to every Short's
description (explicit request, 2026-10-03: "I want in every short
description like example 'puranakathalu by mahanavi spirituals' means
I want to increase brand value").

A single shared constant (rather than each SEO module inventing its
own wording) so every series' tagline follows the exact same format
and the brand name itself is spelled identically everywhere -- change
BRAND_NAME once here and every series picks it up.

This is deliberately a plain, short, English-script line (not
Telugu) -- a tagline is a visual/brand signature meant to be
instantly recognizable on repeat viewing across every series, which
works better as one fixed, simple string than as content competing
for the viewer's reading attention. It is placed as the very FIRST
line of the description, ahead of even the hook -- brand recall was
the explicit goal of this request, so the tagline gets the single
highest-visibility spot (the snippet shown before YouTube's mobile
"...more" cutoff), ahead of the hook line that held that spot before.
"""

from __future__ import annotations

BRAND_NAME = "Mahanavi Spirituals"

# One short, recognizable English name per series -- matches the
# user's own example wording ("puranakathalu") for the Purana Story
# series, extended to the same style for every other series.
SERIES_TAGLINE_NAME: dict[str, str] = {
    "rahu_kalam": "Rahu Kalam",
    "shubha_ghadiyalu": "Shubha Ghadiyalu",
    "durmuhurtham": "Durmuhurtham",
    "rashi_mantra": "Rashi Mantra",
    "purana_short": "Purana Kathalu",
    "purana_concept": "Purana Shorts",
    "gita_sloka": "Bhagavad Gita Sloka",
}


def brand_tagline(series_key: str) -> str:
    """e.g. brand_tagline("purana_short") -> "Purana Kathalu by Mahanavi Spirituals"."""
    name = SERIES_TAGLINE_NAME[series_key]
    return f"{name} by {BRAND_NAME}"
