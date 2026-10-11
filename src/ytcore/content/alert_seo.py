"""
Alert Short SEO content — titles, descriptions, and hashtags for the
Rahu Kalam / Shubha Ghadiyalu Shorts. Deliberately separate from
content/generator.py (the main daily post's SEO builder) because Shorts
have real, different platform conventions from Community Posts:

Applied here (researched 2026 YouTube Shorts best practices, not
guessed from stale training-data assumptions):
  - #Shorts is the FIRST hashtag — mandatory categorizer.
  - 3-5 hashtags total, placed in the DESCRIPTION — the first 3 hashtags
    in a description show ABOVE the title as clickable links, which is
    actually the highest-visibility placement (not the title itself).
  - Shorts titles perform best short (30-40 characters), unlike the
    long descriptive titles used for the main daily Community Post.
  - Hashtags are a SECONDARY signal — hook quality, thematic
    consistency, and watch-through retention matter more. This module
    doesn't oversell hashtags as a growth lever they aren't.
  - No fabricated "trending hashtag" claims: there is no free, honest
    way to track real-time trending hashtags (the tools that do this
    are paid). What's here is a curated, ROTATING set of established
    devotional/Telugu hashtags, plus room for a genuinely relevant
    festival tag when Panchang data indicates one — not a fake
    "always latest" promise.

TITLE ROTATION: a real, legitimate concern was raised about posting
IDENTICAL title text every single day, indefinitely. Worth being clear
about what YouTube's spam/duplicate detection actually targets:
re-uploading the same VIDEO repeatedly, or channels with no genuine
changing value -- NOT a recurring daily-content format where the
underlying data (today's actual times) genuinely changes, the same
pattern used by established daily horoscope/weather/Panchang channels
without penalty. Real day-to-day title variety is still worthwhile
regardless, so titles rotate through a pool deterministically by date
(same pattern as the hashtag rotation) rather than one fixed string.

BILINGUAL DESCRIPTION (per explicit request): Telugu content first,
then an English translation below it, so the description serves both
audiences and both languages' search terms. The English CTA/title-
reasoning pools are paired by INDEX with their Telugu counterparts
(same rotation pick) -- not independently rotated -- so a given day's
Telugu and English sections say the same thing, not two different
random combinations.

FEATURED VIDEO LINKS: two specific past videos, given directly rather
than discovered/guessed -- this module never fabricates a link to
content it hasn't been explicitly told exists.
"""

from __future__ import annotations
from ytcore.brandcfg import A_HANDLE, A_NAME, A_TE  # noqa: E402

from dataclasses import dataclass
from datetime import date

from ytcore.content.branding import brand_tagline

# Niche hashtags specific to each alert type. Kept small and specific
# per the "specific beats generic" guidance (#రాహుకాలం beats #పంచాంగం
# alone) -- these are the 2-3 "niche identifier" tags in the researched
# 3-5 total formula.
_RAHU_KALAM_HASHTAGS = ["#రాహుకాలం", "#RahuKalam", "#పంచాంగం"]
_SHUBHA_GHADIYALU_HASHTAGS = ["#శుభముహూర్తం", "#అభిజిత్ముహూర్తం", "#పంచాంగం"]
_DURMUHURTHAM_HASHTAGS = ["#దుర్ముహూర్తం", "#Durmuhurtham", "#పంచాంగం"]

# Rotating pool of established devotional/Telugu hashtags -- reviewed
# periodically (same pattern as the Telugu translation dictionaries),
# not a real-time trend feed. One is added as the optional 4th/5th tag.
_ROTATING_POOL = [
    "#TeluguPanchangam", "#Devotional", "#Bhakti", "#HinduDevotional",
    "#DailyPanchangam", "#Spirituality",
]

_TELUGU_WEEKDAYS: dict[int, str] = {
    0: "సోమవారం", 1: "మంగళవారం", 2: "బుధవారం", 3: "గురువారం",
    4: "శుక్రవారం", 5: "శనివారం", 6: "ఆదివారం",
}
_ENGLISH_WEEKDAYS: dict[int, str] = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday",
}

# Each title pool has 35 real variations, rotated deterministically by
# date -- avoids literally identical text every day while keeping every
# variant on-brand and equally accurate. Kept to the researched 30-40
# char Shorts sweet spot (module docstring), and every single title
# mixes actual Telugu script with English (not just a bilingual pair of
# otherwise-monolingual entries) -- per explicit requirement.
_RAHU_KALAM_TITLES = [
    "ఈరోజు రాహు కాలం - Rahu Kalam Today",
    "రాహు కాలం Timing - ఈరోజు జాగ్రత్త!",
    "Rahu Kalam ఈరోజు ఎప్పుడు?",
    "Today's Rahu Kalam - ఈరోజు సమయం",
    "రాహు కాలం Alert - నేటి సమయం",
    "Avoid This Time - ఈరోజు రాహు కాలం",
    "ఈరోజు రాహు కాలం Time చూడండి",
    "Rahu Kalam Alert - ఈరోజు Timing",
    "జాగ్రత్త! Rahu Kalam ఈరోజు సమయం",
    "Rahu Kalam Today - ఈరోజు వేళ ఇదే",
    "నేటి రాహు కాలం - Don't Miss This",
    "Rahu Kalam Warning - ఈరోజు టైమింగ్",
    "ఈరోజు రాహు కాలం Ends ఎప్పుడు?",
    "Know Today's రాహు కాలం Time",
    "రాహు కాలం Alert - ఈ సమయం గుర్తుంచుకోండి",
    "Today's Inauspicious Time - రాహు కాలం",
    "రాహు కాలం Update - ఈరోజు సమయం ఇదే",
    "Check రాహు కాలం Before You Start",
    "రాహు కాలం ఈరోజు - Full Details",
    "Today's Rahu Kalam Time - ఈరోజు తేదీ",
    "రాహు కాలం Start ఎప్పుడు? ఈరోజు",
    "Rahu Kalam Ends At - ఈరోజు సమయం",
    "ఈరోజు రాహు కాలం - Plan Your Day",
    "Rahu Kalam Live Update - ఈరోజు",
    "రాహు కాలం Timing Miss అవ్వకండి",
    "Today's Rahu Kalam Duration - ఈరోజు వ్యవధి",
    "రాహు కాలం - Important పని వాయిదా వేయండి",
    "Rahu Kalam Schedule - ఈరోజు",
    "ఈరోజు Rahu Kalam ఎప్పుడు మొదలు?",
    "Rahu Kalam Precaution Time - ఈరోజు",
    "రాహు కాలం Timing తెలుసుకోండి",
    "Daily Rahu Kalam - ఈరోజు వివరాలు",
    "Rahu Kalam Countdown - ఈరోజు",
    "రాహు కాలం Warning - ఈరోజు సమయం",
    "Rahu Kalam Timing Alert - ఈరోజు",
]

_SHUBHA_GHADIYALU_TITLES = [
    "ఈరోజు శుభ ఘడియలు - Auspicious Time Today",
    "Shubha Muhurtam - నేటి శుభ సమయాలు",
    "Good Time Today - ఈరోజు మంచి సమయం",
    "Auspicious Time - శుభకార్యాలకు ఇదే సమయం",
    "అభిజిత్/అమృత కాలం - Abhijit/Amrit Kaal - ఈరోజు టైమింగ్స్",
    "Pooja Time Today - ఈరోజు పూజకు మంచి సమయం",
    "ఈరోజు శుభ ఘడియలు Time చూడండి",
    "Shubha Ghadiyalu Alert - నేటి Timing",
    "నేటి Shubha ముహూర్తాలు ఇవే",
    "Best Time Today - ఈరోజు శుభ ఘడియలు",
    "శుభకార్యాలకు Today మంచి సమయం",
    "Auspicious Timings - ఈరోజు కోసం",
    "ఈరోజు Pooja, శుభకార్యాలకు మంచి సమయం",
    "Today's Good Muhurtam - శుభ సమయం",
    "శుభ ఘడియలు Update - ఈరోజు సమయం ఇదే",
    "Perfect Time Today - శుభ ముహూర్తం",
    "ఈరోజు Abhijit ముహూర్తం సమయం",
    "Know Today's శుభ ఘడియలు Timings",
    "శుభ ఘడియలు ఈరోజు - Full Details",
    "Today's Auspicious Timings - ఈరోజు తేదీ",
    "శుభ సమయం Start ఎప్పుడు? ఈరోజు",
    "Shubha Time Ends At - ఈరోజు",
    "ఈరోజు శుభ ఘడియలు - Plan Your Day",
    "Muhurtam Live Update - ఈరోజు",
    "శుభ సమయం Miss అవ్వకండి",
    "Today's Shubha Muhurtam Duration - ఈరోజు",
    "శుభ ఘడియలు - Important పని ఇప్పుడే మొదలుపెట్టండి",
    "Shubha Ghadiyalu Schedule - ఈరోజు",
    "ఈరోజు Shubha సమయం ఎప్పుడు మొదలు?",
    "Auspicious Time Reminder - ఈరోజు",
    "శుభ ఘడియల Details తెలుసుకోండి",
    "Daily Shubha Muhurtam - ఈరోజు వివరాలు",
    "Muhurtam Countdown - ఈరోజు",
    "శుభ సమయం Alert - ఈరోజు",
    "Shubha Timing Alert - ఈరోజు",
]

# Title pool for the Durmuhurtham alert -- leads with the exact "Avoid
# This Time" framing that (per real channel analytics, 2026-09-30) was
# the channel's single best-performing title pattern alongside the
# Abhijit/Amrit Kaal combo, so this pool is built around that phrasing
# rather than inventing a new one from scratch.
_DURMUHURTHAM_TITLES = [
    "Avoid This Time - దుర్ముహూర్తం కాలం",
    "ఈరోజు దుర్ముహూర్తం - Avoid This Time",
    "Durmuhurtham Alert - ఈరోజు సమయం",
    "Durmuhurtham | జాగ్రత్త! దుర్ముహూర్తం ఈరోజు సమయం",
    "Today's Durmuhurtham - ఈరోజు వేళ ఇదే",
    "దుర్ముహూర్తం Timing - ఈరోజు జాగ్రత్త!",
    "Durmuhurtham Today - Don't Start Anything",
    "నేటి దుర్ముహూర్తం - Avoid Starting Work",
    "Durmuhurtham Warning - ఈరోజు టైమింగ్",
    "ఈరోజు దుర్ముహూర్తం Time చూడండి",
    "Know Today's దుర్ముహూర్తం Time",
    "దుర్ముహూర్తం Alert - ఈ సమయం గుర్తుంచుకోండి",
    "Today's Inauspicious Window - దుర్ముహూర్తం",
    "దుర్ముహూర్తం Update - ఈరోజు సమయం ఇదే",
    "Check దుర్ముహూర్తం Before You Start",
    "దుర్ముహూర్తం ఈరోజు - Full Details",
    "Today's Durmuhurtham Time - ఈరోజు తేదీ",
    "దుర్ముహూర్తం Start ఎప్పుడు? ఈరోజు",
    "Durmuhurtham Ends At - ఈరోజు సమయం",
    "ఈరోజు దుర్ముహూర్తం - Plan Your Day",
]

# Opening hook line, prepended to each description -- this is the part
# that shows in the high-visibility snippet before YouTube's "...more"
# cutoff on mobile, so it earns a real hook rather than starting cold
# on the raw time data. Rotates independently of the title/CTA pools;
# paired Telugu/English by index (see module docstring's pairing note).
_RAHU_KALAM_HOOKS_TE = [
    "ఈరోజు ఈ సమయంలో కొత్త పని మొదలుపెట్టకండి — Rahu Kalam Alert",
    "Rahu Kalam Alert: ఈరోజు ఈ సమయం జాగ్రత్తగా గమనించండి",
    "ముఖ్యమైన పనులు మొదలుపెట్టేముందు ఈ సమయం చూడండి",
    "Save This Time: ఈరోజు రాహు కాలం వివరాలు ఇక్కడ",
    "ప్రతిరోజు రాహు కాలం తెలుసుకోవడం ఎందుకు ముఖ్యమో మీకు తెలుసా?",
    "Rahu Kalam Reminder: ఈరోజు ఈ సమయం పాటించండి",
    "ఈరోజు శుభ కార్యాలు మొదలుపెట్టే ముందు ఇది చదవండి",
    "Quick Alert: ఈరోజు రాహు కాలం సమయం ఇదే",
]
_RAHU_KALAM_HOOKS_EN = [
    "Don't start anything new during this time today — Rahu Kalam Alert",
    "Rahu Kalam Alert: Please note this time carefully today",
    "Check this time before starting anything important",
    "Save This Time: Today's Rahu Kalam details here",
    "Do you know why checking Rahu Kalam every day matters?",
    "Rahu Kalam Reminder: Follow this time today",
    "Read this before starting any auspicious task today",
    "Quick Alert: Here's today's Rahu Kalam time",
]

_SHUBHA_GHADIYALU_HOOKS_TE = [
    "ఈరోజు ఈ సమయంలో శుభకార్యాలు మొదలుపెట్టండి — Shubha Muhurtam",
    "Good News: ఈరోజు ఈ సమయాలు అన్నీ శుభప్రదం",
    "కొత్త పని మొదలుపెట్టాలా? ఈ శుభ సమయం చూడండి",
    "Save This Time: ఈరోజు శుభ ఘడియల వివరాలు ఇక్కడ",
    "ప్రతిరోజు శుభ ముహూర్తం తెలుసుకోవడం ఎందుకు ముఖ్యమో మీకు తెలుసా?",
    "Shubha Muhurtam Reminder: ఈరోజు ఈ సమయాలు పాటించండి",
    "ఏదైనా మంచి పని మొదలుపెట్టేముందు ఇది చదవండి",
    "Quick Update: ఈరోజు శుభ ఘడియలు ఇవే",
]
_SHUBHA_GHADIYALU_HOOKS_EN = [
    "Start your auspicious tasks during this time today — Shubha Muhurtam",
    "Good News: All these timings today are auspicious",
    "Planning to start something new? Check this auspicious time",
    "Save This Time: Today's Shubha Ghadiyalu details here",
    "Do you know why checking Shubha Muhurtam every day matters?",
    "Shubha Muhurtam Reminder: Follow these timings today",
    "Read this before starting any good work today",
    "Quick Update: Here are today's Shubha Ghadiyalu timings",
]

_DURMUHURTHAM_HOOKS_TE = [
    "ఈరోజు ఈ సమయంలో కొత్త పని మొదలుపెట్టకండి — Durmuhurtham Alert",
    "Durmuhurtham Alert: ఈరోజు ఈ సమయం జాగ్రత్తగా గమనించండి",
    "ముఖ్యమైన పనులు మొదలుపెట్టేముందు ఈ సమయం చూడండి",
    "Save This Time: ఈరోజు దుర్ముహూర్తం వివరాలు ఇక్కడ",
    "ప్రతిరోజు దుర్ముహూర్తం తెలుసుకోవడం ఎందుకు ముఖ్యమో మీకు తెలుసా?",
    "Durmuhurtham Reminder: ఈరోజు ఈ సమయం పాటించండి",
    "ఈరోజు శుభ కార్యాలు మొదలుపెట్టే ముందు ఇది చదవండి",
    "Quick Alert: ఈరోజు దుర్ముహూర్తం సమయం ఇదే",
]
_DURMUHURTHAM_HOOKS_EN = [
    "Don't start anything new during this time today — Durmuhurtham Alert",
    "Durmuhurtham Alert: Please note this time carefully today",
    "Check this time before starting anything important",
    "Save This Time: Today's Durmuhurtham details here",
    "Do you know why checking Durmuhurtham every day matters?",
    "Durmuhurtham Reminder: Follow this time today",
    "Read this before starting any auspicious task today",
    "Quick Alert: Here's today's Durmuhurtham time",
]

# English half of the comment-engagement line appended to every
# description, right after the CTA -- echoes the same on-screen
# comment prompt (passed in by the caller as `comment_prompt_te`,
# same rotation as the AlertCard render) rather than a third, separate
# ask, so viewers who don't watch to the end still see the request.
_COMMENT_ENGAGEMENT_EN = [
    "Share your thoughts in the comments below! 🙏",
    "Let us know in the comments! 🙏",
    "Drop a comment and share your thoughts! 🙏",
    "We'd love to hear from you in the comments! 🙏",
    "Comment below and join the conversation! 🙏",
    "Tell us in the comments below! 🙏",
]

# Closing CTA sentence in the description also rotates. English pools
# are paired by INDEX with the Telugu ones (see module docstring) --
# not independently rotated.
_RAHU_KALAM_CTAS = [
    "ఈ సమయంలో శుభకార్యాలు మొదలుపెట్టకండి.",
    "ఈ సమయంలో కొత్త పనులు ప్రారంభించడం మంచిది కాదు.",
    "ఈ సమయాన్ని గమనించి ముఖ్యమైన పనులు వాయిదా వేసుకోండి.",
]
_RAHU_KALAM_CTAS_EN = [
    "Avoid starting auspicious activities during this time.",
    "It's not advisable to start new tasks during this period.",
    "Please note this time and postpone important tasks accordingly.",
]
_SHUBHA_GHADIYALU_CTAS = [
    "ఈ సమయాల్లో శుభకార్యాలు చేయవచ్చు.",
    "ఈ సమయాల్లో ముఖ్యమైన పనులు ప్రారంభించడం శుభప్రదం.",
    "ఈ ఘడియల్లో పూజలు, శుభకార్యాలు చేయడం మంచిది.",
]
_SHUBHA_GHADIYALU_CTAS_EN = [
    "You can perform auspicious activities during these times.",
    "Starting important tasks during these times is considered auspicious.",
    "These are good times for poojas and other auspicious activities.",
]
_DURMUHURTHAM_CTAS = [
    "ఈ సమయంలో శుభకార్యాలు మొదలుపెట్టకండి.",
    "ఈ సమయంలో కొత్త పనులు ప్రారంభించడం మంచిది కాదు.",
    "ఈ సమయాన్ని గమనించి ముఖ్యమైన పనులు వాయిదా వేసుకోండి.",
]
_DURMUHURTHAM_CTAS_EN = [
    "Avoid starting auspicious activities during this time.",
    "It's not advisable to start new tasks during this period.",
    "Please note this time and postpone important tasks accordingly.",
]

# Two specific past videos, given directly -- see module docstring.
_FEATURED_VIDEO_LINKS = [
    "https://www.youtube.com/watch?v=at-SA1XoOL8",
    "https://youtu.be/c4AyFWMmhk8",
]

# Shared footer appended to every description -- real, stable channel
# links, the two featured videos above, a short about blurb, genuine
# keyword-rich sentences, and a subscription note. Telugu and English
# versions, Telugu shown first per explicit request. Uses the
# ~5000-character description budget that was otherwise sitting almost
# entirely unused.
_CHANNEL_FOOTER_TE = f"""
మా ఛానల్‌లో మరిన్ని భక్తి వీడియోలు చూడండి:
🎬 వీడియోలు: https://www.youtube.com/{A_HANDLE}/videos
📱 షార్ట్స్: https://www.youtube.com/{A_HANDLE}/shorts

మా ఇతర భక్తి వీడియోలు:
{{videos}}

{A_TE} - తెలుగు భక్తి ఛానల్. ప్రతిరోజు పంచాంగం, రాహు కాలం, శుభ ముహూర్తాలు, దేవుళ్ల మంత్రాలు మరియు భక్తి సమాచారం అందిస్తాము. మా లక్ష్యం సనాతన ధర్మం, వేద జ్ఞానాన్ని అందరికీ చేరువ చేయడం.

ప్రతిరోజు ఉదయం పంచాంగం అప్డేట్ కోసం సబ్‌స్క్రైబ్ చేయండి.""".strip().format(videos="\n".join(_FEATURED_VIDEO_LINKS))

_CHANNEL_FOOTER_EN = f"""
Watch more devotional videos on our channel:
🎬 Videos: https://www.youtube.com/{A_HANDLE}/videos
📱 Shorts: https://www.youtube.com/{A_HANDLE}/shorts

Our other devotional videos:
{{videos}}

{A_NAME} is a Telugu devotional channel. We bring you daily Panchangam, Rahu Kalam, auspicious muhurtams, deity mantras, and devotional content. Our goal is to bring Sanatana Dharma and Vedic knowledge closer to everyone.

Subscribe for daily morning Panchangam updates.""".strip().format(videos="\n".join(_FEATURED_VIDEO_LINKS))


@dataclass(frozen=True, slots=True)
class ShortSeoContent:
    """SEO content for one alert Short."""
    title: str            # kept to the 30-40 char Shorts sweet spot
    description: str      # Telugu first, then English (see module docstring)
    hashtags: list[str]   # ordered, #Shorts always first

    def full_caption(self) -> str:
        """Description + hashtags, the way it goes into the upload form."""
        return f"{self.description}\n\n{' '.join(self.hashtags)}"


def _pick_rotating(pool: list[str], for_date_ordinal: int, offset: int = 0) -> str:
    """Deterministic rotation through a pool, so the same date always
    gets the same item (reproducible), but it varies day to day rather
    than being static forever. `offset` lets two different rotations
    (e.g. title vs CTA) use the same ordinal without landing in sync."""
    return pool[(for_date_ordinal + offset) % len(pool)]


def _pick_rotating_pair(pool_te: list[str], pool_en: list[str], for_date_ordinal: int, offset: int) -> tuple[str, str]:
    """Same rotation index for a Telugu/English pair, so both languages
    say the same thing on a given day rather than mismatched picks."""
    index = (for_date_ordinal + offset) % len(pool_te)
    return pool_te[index], pool_en[index]


def build_rahu_kalam_seo(
    rahu_kalam_range: str, for_date_ordinal: int, comment_prompt_te: str, festival: str | None = None,
) -> ShortSeoContent:
    title = _pick_rotating(_RAHU_KALAM_TITLES, for_date_ordinal)
    d = date.fromordinal(for_date_ordinal)
    weekday_te, weekday_en = _TELUGU_WEEKDAYS[d.weekday()], _ENGLISH_WEEKDAYS[d.weekday()]
    cta_te, cta_en = _pick_rotating_pair(_RAHU_KALAM_CTAS, _RAHU_KALAM_CTAS_EN, for_date_ordinal, offset=1)
    hook_te, hook_en = _pick_rotating_pair(_RAHU_KALAM_HOOKS_TE, _RAHU_KALAM_HOOKS_EN, for_date_ordinal, offset=2)
    comment_en = _pick_rotating(_COMMENT_ENGAGEMENT_EN, for_date_ordinal, offset=3)

    # comment_prompt_te is the SAME text/rotation already shown on-screen
    # (caller passes the exact string it built the AlertCard with) --
    # the description echoes it rather than posing a second, different
    # ask, so viewers who don't watch to the end still see the request.
    description_te = (
        f"{hook_te}\n\nఈరోజు {weekday_te} రాహు కాలం: {rahu_kalam_range} — {cta_te}\n\n{comment_prompt_te}"
    )
    description_en = f"{hook_en}\n\nToday's ({weekday_en}) Rahu Kalam: {rahu_kalam_range} — {cta_en}\n\n{comment_en}"
    description = (
        f"{brand_tagline('rahu_kalam')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_RAHU_KALAM_HASHTAGS]
    if festival:
        hashtags.append(f"#{festival.replace(' ', '')}")
    hashtags.append(_pick_rotating(_ROTATING_POOL, for_date_ordinal))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)


def build_shubha_ghadiyalu_seo(
    good_muhurtams: list[tuple[str, str]],
    for_date_ordinal: int,
    comment_prompt_te: str,
    festival: str | None = None,
) -> ShortSeoContent:
    title = _pick_rotating(_SHUBHA_GHADIYALU_TITLES, for_date_ordinal)
    d = date.fromordinal(for_date_ordinal)
    weekday_te, weekday_en = _TELUGU_WEEKDAYS[d.weekday()], _ENGLISH_WEEKDAYS[d.weekday()]
    lines = ", ".join(f"{label} {value}" for label, value in good_muhurtams)
    cta_te, cta_en = _pick_rotating_pair(_SHUBHA_GHADIYALU_CTAS, _SHUBHA_GHADIYALU_CTAS_EN, for_date_ordinal, offset=1)
    hook_te, hook_en = _pick_rotating_pair(
        _SHUBHA_GHADIYALU_HOOKS_TE, _SHUBHA_GHADIYALU_HOOKS_EN, for_date_ordinal, offset=2,
    )
    comment_en = _pick_rotating(_COMMENT_ENGAGEMENT_EN, for_date_ordinal, offset=3)

    description_te = (
        f"{hook_te}\n\nఈరోజు {weekday_te} శుభ ఘడియలు: {lines} — {cta_te}\n\n{comment_prompt_te}"
    )
    description_en = (
        f"{hook_en}\n\nToday's ({weekday_en}) auspicious timings: {lines} — {cta_en}\n\n{comment_en}"
    )
    description = (
        f"{brand_tagline('shubha_ghadiyalu')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_SHUBHA_GHADIYALU_HASHTAGS]
    if festival:
        hashtags.append(f"#{festival.replace(' ', '')}")
    hashtags.append(_pick_rotating(_ROTATING_POOL, for_date_ordinal))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)


def build_durmuhurtham_seo(
    durmuhurtham_range: str, for_date_ordinal: int, comment_prompt_te: str, festival: str | None = None,
) -> ShortSeoContent:
    """SEO content for the Durmuhurtham alert Short -- same structure as
    build_rahu_kalam_seo (another "avoid this time" inauspicious-period
    alert), added because real channel analytics (2026-09-30) showed a
    standalone "Avoid This Time - దుర్ముహూర్తం" video as one of the
    channel's two best performers, while this pipeline had only ever
    shown Durmuhurtham as small secondary text on the Rahu Kalam card,
    never as its own titled Short."""
    title = _pick_rotating(_DURMUHURTHAM_TITLES, for_date_ordinal)
    d = date.fromordinal(for_date_ordinal)
    weekday_te, weekday_en = _TELUGU_WEEKDAYS[d.weekday()], _ENGLISH_WEEKDAYS[d.weekday()]
    cta_te, cta_en = _pick_rotating_pair(_DURMUHURTHAM_CTAS, _DURMUHURTHAM_CTAS_EN, for_date_ordinal, offset=1)
    hook_te, hook_en = _pick_rotating_pair(_DURMUHURTHAM_HOOKS_TE, _DURMUHURTHAM_HOOKS_EN, for_date_ordinal, offset=2)
    comment_en = _pick_rotating(_COMMENT_ENGAGEMENT_EN, for_date_ordinal, offset=3)

    description_te = (
        f"{hook_te}\n\nఈరోజు {weekday_te} దుర్ముహూర్తం: {durmuhurtham_range} — {cta_te}\n\n{comment_prompt_te}"
    )
    description_en = (
        f"{hook_en}\n\nToday's ({weekday_en}) Durmuhurtham: {durmuhurtham_range} — {cta_en}\n\n{comment_en}"
    )
    description = (
        f"{brand_tagline('durmuhurtham')}\n\n{description_te}\n\n{_CHANNEL_FOOTER_TE}"
        f"\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"
    )

    hashtags = ["#Shorts", *_DURMUHURTHAM_HASHTAGS]
    if festival:
        hashtags.append(f"#{festival.replace(' ', '')}")
    hashtags.append(_pick_rotating(_ROTATING_POOL, for_date_ordinal))

    return ShortSeoContent(title=title, description=description, hashtags=hashtags)
