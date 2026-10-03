"""
post_alert_shorts.py: the full pipeline for the Rahu Kalam (red) and
Shubha Ghadiyalu (green) Shorts. This is deliberately its OWN script
rather than a shared orchestrator class, since the shape is different enough
(no image selection, no multi-platform publisher list, no post-log
database entry) that forcing it into the same class would mean a lot
of "this doesn't apply here" conditionals.

Flow: fetch today's Panchang -> render both cards (AlertCardRenderer)
-> assemble both into .mp4 (video/assembler.py, with your configured
music) -> build SEO for both (content/alert_seo.py) -> upload both
(YouTubeShortsUploader).

SAFETY: uploads as "unlisted" by default -- per explicit instruction,
this does NOT go public until you decide it's ready and pass --public
yourself. Nothing here auto-publicizes anything.

Usage:
    python -m mahanavi.scripts.post_alert_shorts
    python -m mahanavi.scripts.post_alert_shorts --date 2026-09-16
    python -m mahanavi.scripts.post_alert_shorts --public   # only once you're ready
    python -m mahanavi.scripts.post_alert_shorts --only rahu_kalam   # just one Short

TIMING: the production workflow (.github/workflows/daily-shorts.yml) now
ticks hourly, all day, and a separate cheap gate step (scripts/ci/
scheduler_gate.py) decides -- based on the current IST time and each
Short's own "already posted today" marker -- whether THIS tick should
post Rahu Kalam, Shubha Ghadiyalu, or nothing. It only ever invokes
this script with --only when it decides to fire, so by the time this
script runs it trusts that the timing is already correct and does NOT
re-check or wait -- it posts the one requested Short immediately. This
replaced an earlier design where a single once-a-night cron fired and
this script itself slept until the right wall-clock moment; that design
silently lost the whole night whenever GitHub's schedule event failed
to fire even once (confirmed happening for real on several nights).
Running with no --only (the default) still does both Shorts back to
back with the old natural-timing wait, for local/manual testing only.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from datetime import date, datetime
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

from mahanavi.config import Settings, get_settings
from mahanavi.content.alert_seo import (
    ShortSeoContent,
    build_durmuhurtham_seo,
    build_rahu_kalam_seo,
    build_shubha_ghadiyalu_seo,
)
from mahanavi.content.category_comments import build_category_comment
from mahanavi.content.data import DEITY_CONTENT, WEEKDAY_DEITY_MAP, pick_beeja_mantram
from mahanavi.core.models import PanchangData
from mahanavi.database.db import DatabaseManager
from mahanavi.database.repositories import UploadLogRepository
from mahanavi.exceptions import MahanaviError
from mahanavi.images.alert_card_renderer import (
    COLOR_DURMUHURTHAM_BOTTOM,
    COLOR_DURMUHURTHAM_TOP,
    COLOR_RAHU_BOTTOM,
    COLOR_RAHU_TOP,
    COLOR_SHUBHA_BOTTOM,
    COLOR_SHUBHA_TOP,
    AlertCard,
    AlertCardRenderer,
)
from mahanavi.images.telugu_text import PANCHANG_LABELS, format_telugu_date
from mahanavi.panchang.factory import get_panchang_provider
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.assembler import LOOP_FRIENDLY_FADE_IN_SECONDS, LOOP_FRIENDLY_FADE_OUT_SECONDS, assemble_short


def _icon_paths(settings: Settings) -> list[Path]:
    """Lakshmi, Ganesha, Kubera in that order -- only the ones that
    actually exist on disk, so a missing icon degrades gracefully
    (AlertCardRenderer also handles this; this is a second layer so we
    can print clearly which ones are missing up front)."""
    candidates = [
        ("Lakshmi", settings.alert_icon_lakshmi_path),
        ("Ganesha", settings.alert_icon_ganesha_path),
        ("Kubera", settings.alert_icon_kubera_path),
    ]
    paths: list[Path] = []
    for name, path in candidates:
        if path is not None and path.exists():
            paths.append(path)
        else:
            print(f"Note: {name} icon not found at {path} -- that card will render without it.")
    return paths


def _shubha_lines(panchang: PanchangData) -> list[tuple[str, str]]:
    # Both fields can genuinely be absent on a real day (confirmed via a
    # real Prokerala response: Abhijit Muhurtham simply doesn't occur
    # every day) -- skip a missing one entirely rather than showing its
    # label with nothing after it.
    lines = []
    if panchang.abhijit_muhurtham:
        lines.append((PANCHANG_LABELS["abhijit_muhurtham"], panchang.abhijit_muhurtham))
    if panchang.amrit_kaal:
        lines.append((PANCHANG_LABELS["amrit_kaal"], panchang.amrit_kaal))
    return lines


def _other_inauspicious_periods(panchang: PanchangData) -> str:
    """Compact, small-font secondary info for the Rahu Kalam card --
    Yamagandam, Gulika Kalam, Durmuhurtham, Varjyam. Rendered as one
    compact wrapped block (not separate large label/value pairs like
    the main Rahu Kalam time) so it stays visually secondary, per
    explicit request."""
    parts = [
        f"{PANCHANG_LABELS['yamagandam']}: {panchang.yamagandam}",
        f"{PANCHANG_LABELS['gulika_kalam']}: {panchang.gulika_kalam}",
        f"{PANCHANG_LABELS['durmuhurtham']}: {panchang.durmuhurtham}",
        f"{PANCHANG_LABELS['varjyam']}: {panchang.varjyam}",
    ]
    return "   |   ".join(parts)


# Rotating on-screen subscribe lines -- 10 each, deterministic by date
# (same pattern as the YouTube title/CTA rotation in content/alert_seo.py),
# so the card doesn't show the same flat line every single day. Rahu
# Kalam's tone is serious/protective urgency, not manufactured panic --
# these are meant to convey the real cultural weight the timing carries
# for many viewers, not exploit fear as a growth tactic.
#
# UPDATED 2026-10-03 (explicit user request): every line now also tells
# viewers to press the notification bell, not just subscribe. Real
# reason, not just growth-hacking -- this channel's videos keep
# resurfacing in viewers' feeds for days/weeks after posting (normal
# YouTube behavior), so someone watching an older Short could easily
# mistake its timings for TODAY's unless they're actually subscribed
# with the bell on, which is the only way YouTube reliably notifies them
# the moment each day's real video goes up. Spelled out as "బెల్ ఐకాన్"
# (bell icon) in words, never a 🔔 emoji character -- see
# _COMMENT_PROMPT_LINES' comment below: Noto Sans Telugu (the on-screen
# render font) has no emoji glyphs, so an emoji renders as a broken
# tofu box.
_RAHU_KALAM_SUBSCRIBE_LINES = [
    "ప్రతిరోజు అశుభ సమయాలు తెలుసుకోండి - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "చెడు సమయాన్ని తప్పకుండా తెలుసుకోండి - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "ప్రతిరోజు రాహు కాల అప్‌డేట్ కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "చాలా జాగ్రత్తగా ఉండవలసిన సమయం - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ఈరోజు సరైన సమయం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ప్రతిరోజు రాహు కాల సమయం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "మీ పనులు వాయిదా వేయాల్సిన సమయం కోసం బెల్ ఐకాన్ నొక్కండి",
    "ఈ సమయాన్ని నిర్లక్ష్యం చేయకండి - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "రోజూ నష్టం నివారించడానికి సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "మీ కుటుంబ భద్రత కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
]

_SHUBHA_GHADIYALU_SUBSCRIBE_LINES = [
    "ప్రతిరోజు శుభ సమయాలు తెలుసుకోండి - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "మంచి సమయాలను మిస్ కాకుండా - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "ప్రతిరోజు శుభ ముహూర్తాల అప్‌డేట్ కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "ఈ శుభ సమయం మీ కోసమే - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ఈరోజు శుభ సమయం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ప్రతిరోజు అదృష్ట సమయాలు కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "మీ శుభకార్యాలకు సరైన సమయం కోసం బెల్ ఐకాన్ నొక్కండి",
    "ఈ మంచి క్షణాలను వదులుకోకండి - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "రోజూ శుభారంభం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "మీ విజయానికి తొలి అడుగు - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
]

# Durmuhurtham reuses the Rahu Kalam pool's tone (serious/protective,
# not manufactured panic) since it's the same category of "avoid this
# time" content -- added because real analytics showed a standalone
# Durmuhurtham Short outperforming most of the channel's other content,
# while this pipeline previously only showed it as small secondary text
# on the Rahu Kalam card (see _other_inauspicious_periods below).
_DURMUHURTHAM_SUBSCRIBE_LINES = [
    "ప్రతిరోజు దుర్ముహూర్తం తెలుసుకోండి - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "చెడు సమయాన్ని తప్పకుండా తెలుసుకోండి - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "ప్రతిరోజు దుర్ముహూర్త అప్‌డేట్ కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "చాలా జాగ్రత్తగా ఉండవలసిన సమయం - సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ఈరోజు సరైన సమయం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "ప్రతిరోజు దుర్ముహూర్త సమయం కోసం సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "మీ పనులు వాయిదా వేయాల్సిన సమయం కోసం బెల్ ఐకాన్ నొక్కండి",
    "ఈ సమయాన్ని నిర్లక్ష్యం చేయకండి - సబ్‌స్క్రైబ్ చేసి బెల్ నొక్కండి",
    "రోజూ నష్టం నివారించడానికి సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
    "మీ కుటుంబ భద్రత కోసం సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి",
]

# On-screen comment-engagement line, drawn directly above the subscribe
# line (AlertCard.comment_prompt_text). Generic devotional prompts, not
# tied to Rahu Kalam/Shubha Ghadiyalu specifically -- explicit goal is
# just getting the ~3k+ daily viewers who watch but don't comment to
# leave ANY comment, non-controversial (no politics, no sect-vs-sect
# framing, nothing beyond a city name for personal info). Reviewed and
# trimmed by hand from a larger draft pool. No emoji -- the Telugu font
# used for on-screen rendering (Noto Sans Telugu, see module docstring
# in images/alert_card_renderer.py) has no emoji glyphs, so an emoji
# character rendered as a broken tofu box in a real render; confirmed
# and removed rather than pulling in a second emoji-capable font just
# for this. Rotates daily like the subscribe lines, but Rahu Kalam and
# Shubha Ghadiyalu deliberately pick DIFFERENT lines on the same day
# (see _pick_comment_prompt's `offset`) so the two Shorts never show an
# identical prompt.
_COMMENT_PROMPT_LINES = [
    "మీ ఇష్టదైవం ఎవరో కామెంట్ చేయండి",
    "ఈరోజు మీరు ఏ దేవుడిని/దేవతను స్మరించుకున్నారు? కామెంట్ చేయండి",
    "మీకు ఇష్టమైన మంత్రం ఏది? కామెంట్ చేయండి",
    "మీరు రోజూ ఏ పూజ చేస్తారు? కామెంట్ చేయండి",
    "మీ ఊరు/నగరం పేరు కామెంట్ చేయండి",
    "ఈ వీడియో నచ్చితే కామెంట్ చేయండి",
    "మీరు ఎప్పుడూ వెళ్లే దేవాలయం పేరు కామెంట్ చేయండి",
    "మీ కులదైవం ఎవరో కామెంట్ చేయండి",
    "మీకు నచ్చిన శ్లోకం ఒకటి కామెంట్ చేయండి",
    "ఈరోజు ఎవరైనా కుటుంబ సభ్యులను ట్యాగ్ చేస్తూ కామెంట్ చేయండి",
    "మీరు ఏ వారం రోజు ఏ దేవుడిని పూజిస్తారు? కామెంట్ చేయండి",
    "మీ భక్తిని తెలియజేయడానికి 'ఓం' అని కామెంట్ చేయండి",
    "మీకు ఇష్టమైన మంత్రం ఏమిటి? కామెంట్ చేయండి",
    "మీ ఇంట్లో ఏ దేవుడి ఫోటో ఉంది? కామెంట్ చేయండి",
    "ఈరోజు మీ మనసులో ఏముంది? కామెంట్ చేయండి",
    "మీరు వేకువజామున లేచి దేవుడిని తలుచుకుంటారా? కామెంట్ చేయండి",
    "మీకు నచ్చిన పండుగ ఏది? కామెంట్ చేయండి",
    "మీ తాత-అమ్మమ్మల నుంచి విన్న భక్తి కథ ఏమిటి? కామెంట్ చేయండి",
    "ఈరోజు మీరు దేనికి కృతజ్ఞత చెప్పాలనుకుంటున్నారు? కామెంట్ చేయండి",
    "మీ ఇష్టమైన ఆలయ యాత్ర గురించి కామెంట్ చేయండి",
    "మీకు నచ్చిన భజన లేదా కీర్తన ఏది? కామెంట్ చేయండి",
    "మీరు ఈరోజు ఎవరి కోసం ప్రార్థిస్తున్నారు? కామెంట్ చేయండి",
    "మీ దైనందిన పూజా విధానం ఏమిటి? కామెంట్ చేయండి",
    "మీ దగ్గరలో ఉన్న ప్రసిద్ధ దేవాలయం పేరు కామెంట్ చేయండి",
    "ఈరోజు ఏ శుభ సమయంలో మీరు ఏం చేయాలనుకుంటున్నారు? కామెంట్ చేయండి",
    "మీరు ఏ నక్షత్రంలో పుట్టారు? కామెంట్ చేయండి",
    "మీకు నచ్చిన దేవుడి పేరుతో కామెంట్ చేయండి",
    "ఈ ఛానల్ మీకు ఎలా ఉపయోగపడుతుంది? కామెంట్ చేయండి",
    "మీ ఇంటి పేరు దేవుడి పేరు మీదుగా ఉందా? కామెంట్ చేయండి",
    "మీరు ఈరోజు ఎవరికి శుభాకాంక్షలు చెప్పాలనుకుంటున్నారు? కామెంట్ చేయండి",
    "మీరు ఏ పండుగకు ఎక్కువ ఎదురుచూస్తారు? కామెంట్ చేయండి",
    "మీ మనసుకు నచ్చిన ఒక్క మాట కామెంట్ చేయండి",
    "మీకు తెలిసిన ఒక పురాణ కథ పేరు కామెంట్ చేయండి",
    "మీరు ఏ దేవాలయంలో ప్రశాంతత పొందారు? కామెంట్ చేయండి",
    "ఈ వీడియో మీకు నచ్చితే కామెంట్ చేయండి",
    "మీరు ఈరోజు ఏ మంచి పని మొదలుపెట్టబోతున్నారు? కామెంట్ చేయండి",
    "మీ కుటుంబంలో ఎవరు ఎక్కువ భక్తిగా ఉంటారు? కామెంట్ చేయండి",
    "మీకు నచ్చిన దేవుడి ఆలయ నిర్మాణ శైలి ఏమిటి? కామెంట్ చేయండి",
    "మీరు ఏ సమయంలో పూజ చేయడం ఇష్టపడతారు? కామెంట్ చేయండి",
    "మీ దైవభక్తి ప్రయాణం ఎలా మొదలైంది? కామెంట్ చేయండి",
    "ఈరోజు మీకు లభించిన ఒక చిన్న ఆశీర్వాదం గురించి కామెంట్ చేయండి",
    "మీరు ఏ దేవుడి మంత్రాన్ని రోజూ జపిస్తారు? కామెంట్ చేయండి",
    "మీకు నచ్చిన ఒక భక్తి పాట పేరు కామెంట్ చేయండి",
    "ఈ ఛానల్‌ను సబ్‌స్క్రైబ్ చేసి, మీ అభిప్రాయం కామెంట్ చేయండి",
]


def _wait_until_wall_clock_slot(
    tz: ZoneInfo, window_start: dt_time, window_end: dt_time, label: str,
) -> None:
    """Sleeps until a random point within TODAY's [window_start, window_end)
    wall-clock window in `tz` (e.g. 00:00-00:30 IST, then 00:30-01:00 IST),
    spreading the two Shorts across two clean halves of the posting window
    instead of them landing back-to-back at virtually the same timestamp
    every single day.

    Deliberately WALL-CLOCK based, not elapsed-time-from-process-start:
    Rahu Kalam / Shubha Ghadiyalu are time-sensitive -- the whole point is
    reaching viewers before/around those periods, early in their day. The
    previous version measured its delay from whenever the process itself
    happened to start, so a late-firing GitHub Actions cron (observed
    ~2h53m late once already) or a manual test run in the middle of the
    day would add ANOTHER up-to-60-minute random delay on top of that,
    with no idea what the actual clock time was. This version targets the
    real 12:00-1:00 AM IST window directly: if we're already past it (a
    late cron fire, or a manual run during the day), it posts immediately
    with no further wait, instead of compounding the delay or waiting for
    a slot that's already gone."""
    now = datetime.now(tz)
    start_dt = datetime.combine(now.date(), window_start, tzinfo=tz)
    end_dt = datetime.combine(now.date(), window_end, tzinfo=tz)

    if now >= end_dt:
        print(f"Already past the {label} window ({window_start}-{window_end} {tz.key}) -- posting now, no wait.")
        return

    lower_bound = max(start_dt, now)
    target = lower_bound + (end_dt - lower_bound) * random.random()
    remaining = max((target - now).total_seconds(), 0.0)
    print(f"Waiting {remaining:.0f}s (~{remaining / 60:.1f}m) before {label}...")
    time.sleep(remaining)


def _pick_subscribe_text(pool: list[str], for_date: date) -> str:
    """Deterministic rotation through a subscribe-line pool -- the same
    date always gets the same line (reproducible), varying day to day."""
    return pool[for_date.toordinal() % len(pool)]


def _pick_comment_prompt(pool: list[str], for_date: date, offset: int) -> str:
    """Deterministic rotation through the comment-prompt pool, same
    reproducible-by-date pattern as _pick_subscribe_text. `offset` lets
    Rahu Kalam and Shubha Ghadiyalu pick different indices on the same
    date -- called with offset=0 and offset=len(pool)//2 respectively,
    which guarantees two different lines (for any pool longer than 1
    item, a half-length shift never lands back on the same index)."""
    return pool[(for_date.toordinal() + offset) % len(pool)]


def _mantra_lines(for_date: date, offset: int) -> list[tuple[str, str]]:
    """Mantra + beeja-mantram line for one alert card, rotated BOTH
    day-to-day AND across the three alert Shorts posted on the same day
    (explicit request, 2026-10-03: "see all this 3 posts today showing
    same mantram let's rotate that ... Also other gods on that day" --
    previously this returned ONE fixed pick per date and all three
    cards shared it verbatim, which is exactly what the screenshot
    showed).

    `offset` distinguishes the three callers (Rahu Kalam=0, Shubha
    Ghadiyalu=1, Durmuhurtham=2) so each gets a different pool entry on
    the same date.

    Today's weekday deity (WEEKDAY_DEITY_MAP) still anchors the pool --
    most entries are ITS OWN mantra namalu variants (content.
    mantra_namalu), per the explicit request to rotate Venkateswara's
    own names/mantras -- but two entries from OTHER deities are folded
    in too, so not all three of a day's Shorts have to be the same
    deity. Which other deities appear also varies day to day."""
    today_deity = WEEKDAY_DEITY_MAP[for_date.weekday()]
    today_content = DEITY_CONTENT[today_deity]
    beeja_today = pick_beeja_mantram(today_content, for_date)

    pool: list[tuple[str, str]] = [(namam, beeja_today) for namam in today_content.mantra_namalu]

    other_deities = [d for d in DEITY_CONTENT if d != today_deity]
    for i in range(2):
        other_deity = other_deities[(for_date.toordinal() + i) % len(other_deities)]
        other_content = DEITY_CONTENT[other_deity]
        pool.append((other_content.mantra_namalu[0], pick_beeja_mantram(other_content, for_date)))

    mantra, beeja = pool[(for_date.toordinal() + offset) % len(pool)]
    return [
        ("మంత్రం", mantra),
        ("బీజ మంత్రం (శుభఫలితాల కోసం 11 సార్లు పఠించండి)", beeja),
    ]


def _process_one(
    kind: str, card: AlertCard, seo: ShortSeoContent, renderer: AlertCardRenderer,
    settings: Settings, for_date: date, uploader: YouTubeShortsUploader, privacy_status: str,
) -> bool:
    print(f"\n--- {kind} ---")
    try:
        image_path = renderer.render(card, for_date)
        print(f"Rendered: {image_path}")

        video_path = settings.output_dir / f"{for_date.isoformat()}_{card.filename_suffix}_short.mp4"
        # Loop-friendly, no fade (per explicit request, 2026-10-02: "it's
        # fading out after ending short it should not happen user should
        # not find our short ended"). These are the channel's OLDEST
        # Shorts (Rahu Kalam / Shubha Ghadiyalu / Durmuhurtham), built
        # before LOOP_FRIENDLY_FADE_*_SECONDS existed for the later
        # Rashi Mantra / Purana series -- they were still using
        # assemble_short()'s plain defaults (0.6s video fade-in, 1.0s
        # audio fade-out), which is exactly the visible/audible "ending"
        # seam a looping Short must not have. Explicitly loop-friendly
        # now, matching every other series on the channel.
        assemble_short(
            image_path, video_path,
            duration_seconds=settings.alert_short_duration_seconds,
            audio_path=settings.alert_short_music_path,
            fade_in_seconds=LOOP_FRIENDLY_FADE_IN_SECONDS,
            fade_out_seconds=LOOP_FRIENDLY_FADE_OUT_SECONDS,
        )
        print(f"Assembled: {video_path}")

        result = uploader.upload(video_path, seo, privacy_status=privacy_status)
        if result.success:
            print(f"Uploaded ({privacy_status}): {result.post_url}")
            if result.video_id:
                comment_text = build_category_comment("muhurtas", for_date.toordinal())
                if uploader.post_comment(result.video_id, comment_text):
                    print(f"Posted category comment: {comment_text}")
                else:
                    print("Note: could not post category comment (non-fatal).")

                db = DatabaseManager(settings.database_path)
                UploadLogRepository(db).log_upload(result.video_id, "muhurtas", seo.title, for_date)

                if settings.playlist_id_muhurtas:
                    if uploader.add_to_playlist(result.video_id, settings.playlist_id_muhurtas):
                        print("Added to playlist.")
                    else:
                        print("Note: could not add to playlist (non-fatal).")
            return True
        print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
        return False

    except MahanaviError as exc:
        print(f"{kind} FAILED: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the results yourself.",
    )
    parser.add_argument(
        "--no-delay", action="store_true",
        help="Skip the natural-timing delays that normally spread the two Shorts across the "
             "12:00-12:30 / 12:30-1:00 AM halves of the posting window. Only meaningful when "
             "--only is NOT given (legacy both-in-one-run mode) -- used for local/manual testing.",
    )
    parser.add_argument(
        "--only", choices=["rahu_kalam", "shubha_ghadiyalu", "durmuhurtham"], default=None,
        help="Post just this one Short and exit -- no wait, posts immediately. This is what the "
             "production hourly-tick workflow always passes (see module docstring); omit it for "
             "the legacy both-Shorts-with-natural-timing-wait local/manual mode.",
    )
    args = parser.parse_args()

    settings = get_settings()
    # Uses settings.timezone (Asia/Kolkata) explicitly, matching main.py's
    # existing pattern -- plain date.today() reads whatever timezone the
    # underlying machine happens to be configured as, which caused a real
    # bug: WSL defaults to UTC internally regardless of the Windows host's
    # timezone, so this returned "yesterday" for any run before 5:30 AM
    # IST (UTC+5:30) -- confirmed by a real run showing the 18th when it
    # was already the 19th in IST.
    tz = ZoneInfo(settings.timezone)
    for_date = date.fromisoformat(args.date) if args.date else datetime.now(tz).date()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the results.")

    panchang_provider = get_panchang_provider(settings)
    renderer = AlertCardRenderer(settings)
    uploader = YouTubeShortsUploader(settings)

    want_rahu = args.only in (None, "rahu_kalam")
    want_shubha = args.only in (None, "shubha_ghadiyalu")
    want_durmuhurtham = args.only in (None, "durmuhurtham")
    # --only always fires immediately (the outer hourly-tick gate already
    # confirmed the timing); the wait is only for the legacy no-args
    # "post both Shorts back to back" local/manual mode.
    should_wait = args.only is None and not args.no_delay

    if want_rahu and should_wait:
        _wait_until_wall_clock_slot(tz, dt_time(0, 0), dt_time(0, 30), "the first Short (12:00-12:30 AM slot)")

    print(f"Fetching Panchang for {for_date.isoformat()}...")
    try:
        panchang = panchang_provider.fetch(for_date)
    except MahanaviError as exc:
        print(f"Could not fetch Panchang: {exc}", file=sys.stderr)
        return 1

    icon_paths = _icon_paths(settings)
    date_text = format_telugu_date(for_date)

    rahu_ok = True
    if want_rahu:
        rahu_comment_prompt = _pick_comment_prompt(_COMMENT_PROMPT_LINES, for_date, offset=0)
        rahu_card = AlertCard(
            title="ఈరోజు రాహు కాలం",
            lines=[("సమయం", panchang.rahu_kalam), *_mantra_lines(for_date, offset=0)],
            top_color=COLOR_RAHU_TOP, bottom_color=COLOR_RAHU_BOTTOM,
            filename_suffix="rahu_kalam", icon_paths=icon_paths,
            date_text=date_text, secondary_info=_other_inauspicious_periods(panchang),
            subscribe_text=_pick_subscribe_text(_RAHU_KALAM_SUBSCRIBE_LINES, for_date),
            comment_prompt_text=rahu_comment_prompt,
        )
        # Same comment_prompt text/rotation as the on-screen card above --
        # the description echoes it instead of posing a second, different
        # ask (see alert_seo.build_rahu_kalam_seo's docstring note).
        rahu_seo = build_rahu_kalam_seo(
            panchang.rahu_kalam, for_date_ordinal=for_date.toordinal(), comment_prompt_te=rahu_comment_prompt,
        )
        rahu_ok = _process_one(
            "Rahu Kalam", rahu_card, rahu_seo, renderer, settings, for_date, uploader, privacy_status,
        )

    if want_shubha and should_wait:
        _wait_until_wall_clock_slot(tz, dt_time(0, 30), dt_time(1, 0), "the second Short (12:30-1:00 AM slot)")

    shubha_ok = True
    if want_shubha:
        shubha_lines = _shubha_lines(panchang)
        shubha_comment_prompt = _pick_comment_prompt(
            _COMMENT_PROMPT_LINES, for_date, offset=len(_COMMENT_PROMPT_LINES) // 3,
        )
        shubha_card = AlertCard(
            title="ఈరోజు శుభ ఘడియలు",
            lines=[*shubha_lines, *_mantra_lines(for_date, offset=1)],
            top_color=COLOR_SHUBHA_TOP, bottom_color=COLOR_SHUBHA_BOTTOM,
            filename_suffix="shubha_ghadiyalu", icon_paths=icon_paths,
            date_text=date_text,
            subscribe_text=_pick_subscribe_text(_SHUBHA_GHADIYALU_SUBSCRIBE_LINES, for_date),
            comment_prompt_text=shubha_comment_prompt,
        )
        shubha_seo = build_shubha_ghadiyalu_seo(
            shubha_lines, for_date_ordinal=for_date.toordinal(), comment_prompt_te=shubha_comment_prompt,
        )
        shubha_ok = _process_one(
            "Shubha Ghadiyalu", shubha_card, shubha_seo, renderer, settings, for_date, uploader, privacy_status,
        )

    if want_durmuhurtham and should_wait:
        _wait_until_wall_clock_slot(tz, dt_time(1, 0), dt_time(1, 30), "the third Short (1:00-1:30 AM slot)")

    durmuhurtham_ok = True
    if want_durmuhurtham:
        durmuhurtham_comment_prompt = _pick_comment_prompt(
            _COMMENT_PROMPT_LINES, for_date, offset=(2 * len(_COMMENT_PROMPT_LINES)) // 3,
        )
        durmuhurtham_card = AlertCard(
            title="ఈరోజు దుర్ముహూర్తం",
            lines=[(PANCHANG_LABELS["durmuhurtham"], panchang.durmuhurtham), *_mantra_lines(for_date, offset=2)],
            top_color=COLOR_DURMUHURTHAM_TOP, bottom_color=COLOR_DURMUHURTHAM_BOTTOM,
            filename_suffix="durmuhurtham", icon_paths=icon_paths,
            date_text=date_text,
            subscribe_text=_pick_subscribe_text(_DURMUHURTHAM_SUBSCRIBE_LINES, for_date),
            comment_prompt_text=durmuhurtham_comment_prompt,
        )
        durmuhurtham_seo = build_durmuhurtham_seo(
            panchang.durmuhurtham, for_date_ordinal=for_date.toordinal(), comment_prompt_te=durmuhurtham_comment_prompt,
        )
        durmuhurtham_ok = _process_one(
            "Durmuhurtham", durmuhurtham_card, durmuhurtham_seo, renderer, settings, for_date, uploader, privacy_status,
        )

    rahu_status = "skipped (not requested)" if not want_rahu else ("OK" if rahu_ok else "FAILED")
    shubha_status = "skipped (not requested)" if not want_shubha else ("OK" if shubha_ok else "FAILED")
    durmuhurtham_status = "skipped (not requested)" if not want_durmuhurtham else ("OK" if durmuhurtham_ok else "FAILED")
    print(
        f"\n=== Done. Rahu Kalam: {rahu_status}, Shubha Ghadiyalu: {shubha_status}, "
        f"Durmuhurtham: {durmuhurtham_status} ==="
    )
    return 0 if (rahu_ok and shubha_ok and durmuhurtham_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
