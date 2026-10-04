"""
navaratri_day2_song_seo.py: SEO content (title, description, hashtags)
for the Dasara Navaratri Day 2 devotional SONG video -- "Sri Bala
Tripurasundari Devi", an original bhakti geetam honoring the child form
of the Goddess worshipped in the Sri Vidya tradition. Built 2026-10-04,
following the same credits/copyright/chapters/lyrics pattern established
for the Day 1 Kanaka Durga song (see navaratri_song_seo.py) -- vocals by
Revathy V S L (standing credit for every song on this channel), visuals
this time are channel-owner-supplied stills (NOT fal.ai-generated),
animated locally with a Ken Burns effect -- see
scripts/post_navaratri_day2_song.py.

Unlike navaratri_song_seo.py, this module does NOT hardcode chapter
timestamps -- build_navaratri_day2_song_seo() takes the real measured
song duration (ffprobe, at upload time) and computes them from
SCENE_SEQUENCE's weights, so the description is correct for whatever the
final exported song's exact length turns out to be, without needing a
manual follow-up edit like Day 1 required.
"""

from __future__ import annotations

from dataclasses import dataclass

from mahanavi.content.navaratri_song_seo import (
    NAVARATRI_PLAYLIST_URL,
    NavaratriSongSeoContent,
)

# key -> weight. Mirrors post_navaratri_day2_song.py's SCENE_SEQUENCE
# exactly (duplicated here, not imported, to keep this content module
# free of any video/ffmpeg dependency) -- weights sum to 1.0 and are
# multiplied by the REAL measured song duration to compute chapters.
SCENE_SEQUENCE_WEIGHTS: list[tuple[str, float]] = [
    ("intro", 0.08),
    ("verse1", 0.16),
    ("chorus", 0.16),
    ("verse2", 0.16),
    ("chorus", 0.16),
    ("bridge", 0.16),
    ("outro", 0.12),
]

# Bilingual chapter labels, in SCENE_SEQUENCE_WEIGHTS order -- same
# labels as Day 1 for consistency across the series.
_CHAPTER_LABELS: dict[str, str] = {
    "intro": "పరిచయం (Intro)",
    "verse1": "చరణం 1 (Verse 1)",
    "chorus": "పల్లవి (Chorus)",
    "verse2": "చరణం 2 (Verse 2)",
    "bridge": "మధ్యభాగం (Bridge)",
    "outro": "ముగింపు (Outro)",
}


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def build_chapters_te(total_duration_seconds: float) -> str:
    """Computes real chapter timestamps from SCENE_SEQUENCE_WEIGHTS x the
    real measured song duration. Meets YouTube's auto-chapters
    requirements (starts at 0:00, >=3 entries, each gap >=10s) for any
    song longer than ~2 minutes, given these weights' smallest gap
    (0.08 x duration)."""
    lines = ["📍 పాట విభాగాలు (Song Sections):"]
    elapsed = 0.0
    for key, weight in SCENE_SEQUENCE_WEIGHTS:
        lines.append(f"{_format_timestamp(elapsed)} {_CHAPTER_LABELS[key]}")
        elapsed += total_duration_seconds * weight
    return "\n".join(lines) + "\n"


# Full lyrics, original composition -- added to the description per the
# same standing practice established for Day 1 (devotional song
# descriptions are high-intent searches for printed lyrics).
LYRICS_TE = (
    "సాహిత్యం (పూర్తి) / Full Lyrics:\n\n"
    "[పరిచయం]\n"
    "ఓం ఐం హ్రీం శ్రీం బాలా త్రిపురసుందరీ\n"
    "శ్రీవిద్యా రూపిణి జగదంబా\n"
    "బాల రూపమున వెలిగే తల్లి\n\n"
    "[చరణం 1]\n"
    "శ్రీచక్ర మధ్యమున కొలువైన తల్లి\n"
    "కామేశ్వరీ రూపున వెలిగే జ్యోతి\n"
    "పుస్తకం అక్షమాల చేతపట్టి\n"
    "జ్ఞాన సిద్ధి నొసగు బాలా దేవి\n\n"
    "[పల్లవి]\n"
    "బాలా త్రిపురసుందరీ శ్రీమాతా\n"
    "శరణు శరణు అంటూ మొక్కేము తల్లీ\n"
    "కరుణతో మమ్ము కాపాడవమ్మా\n"
    "విద్యాబుద్ధులు నొసగు జగదంబా\n\n"
    "[చరణం 2]\n"
    "నవరాత్రి రెండవ రోజు పూజలలో\n"
    "బాల రూపమున అలంకారం నీదే\n"
    "పంచదశీ మంత్ర స్వరూపిణివి\n"
    "షోడశీ కళలతో శోభిల్లు తల్లి\n\n"
    "[పల్లవి]\n"
    "బాలా త్రిపురసుందరీ శ్రీమాతా\n"
    "శరణు శరణు అంటూ మొక్కేము తల్లీ\n"
    "కరుణతో మమ్ము కాపాడవమ్మా\n"
    "విద్యాబుద్ధులు నొసగు జగదంబా\n\n"
    "[మధ్యభాగం]\n"
    "లలితా సహస్రనామముల తల్లి\n"
    "త్రిపుర సుందరివి నీవే అమ్మా\n"
    "బాలికా రూపమున భక్తుల కాచే\n"
    "శ్రీవిద్యా దేవత నీకిదే వందనం\n\n"
    "[ముగింపు]\n"
    "జయ జయ బాలా త్రిపురసుందరీ\n"
    "శ్రీవిద్యా రూపిణి జగదంబా\n"
    "ఓం ఐం హ్రీం శ్రీం నమః\n"
    "ఓం ఐం హ్రీం శ్రీం నమః\n"
)

# Kept under YouTube's 100-char title limit.
TITLE = (
    "శ్రీ బాలా త్రిపురసుందరీ దేవి | Dasara Navaratri Day 2 Song 2026 "
    "| Bala Tripurasundari"
)

_DESCRIPTION_TE_BASE = (
    "శ్రీ బాలా త్రిపురసుందరీ దేవి -- శ్రీవిద్యా సంప్రదాయంలో పూజింపబడే బాల రూప జగజ్జననిపై "
    "రచించిన ఒక సంపూర్ణ భక్తి గీతం. ఈ దసరా నవరాత్రుల రెండవ రోజు పూజకు అంకితం చేస్తూ ఈ "
    "పాటను మా ఛానల్ తరఫున అందిస్తున్నాం.\n\n"
    "ఈ గీతం పూర్తిగా స్వీయ రచన, స్వీయ స్వరకల్పన -- సాహిత్యం మొదటి నుండి కొత్తగా రాయబడింది, "
    "గానం మా కుటుంబ సభ్యురాలి స్వంత స్వరంతో చేయబడింది (AI-ఆధారిత సంగీత సాధనాల సహాయంతో రికార్డ్ "
    "చేయబడింది), మరియు దృశ్యాలు కూడా AI సాధనాలతో రూపొందించబడ్డాయి -- ఇది పూర్తిగా మా స్వంత సృజన, "
    "ఎవరి హక్కులను ఉల్లంఘించదు.\n\n"
    "బాలా త్రిపురసుందరి శ్రీవిద్యా దేవతల్లో ఒక ప్రధాన రూపం -- చేతిలో పుస్తకం, అక్షమాల ధరించి, "
    "శ్రీచక్ర మధ్యమున కొలువై, భక్తులకు జ్ఞానాన్ని, విద్యాబుద్ధులను ప్రసాదించే బాలికా రూప జగన్మాత. "
    "నవరాత్రుల రెండవ రోజున ఈ బాల రూప అలంకరణను స్మరిస్తూ ఈ గీతాన్ని అందిస్తున్నాం.\n\n"
    "భక్తులు ఈ పాటను నవరాత్రి పూజా సమయంలో ప్లే చేసుకోవచ్చు. మీకు నచ్చితే షేర్ చేయండి, లైక్ చేయండి, "
    "మా ఛానల్‌ని సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి -- ఈ నవరాత్రుల్లో రాబోయే మిగతా రోజుల పాటల "
    "కోసం.\n\n"
    f"🎵 నవరాత్రి 2026 పాటలు అన్నీ ఇక్కడ: {NAVARATRI_PLAYLIST_URL}\n\n"
)

_DESCRIPTION_TE_CREDITS = (
    "క్రెడిట్స్:\n"
    "గానం: Revathy V S L\n"
    "సాహిత్యం & స్వరకల్పన: Mahanavi Spirituals\n"
    "దృశ్యాలు: AI సాధనాలతో రూపొందించబడ్డాయి\n\n"
    "© 2026 Mahanavi Spirituals. అన్ని హక్కులు రక్షించబడ్డాయి.\n"
    "సంప్రదించండి: mahanavispirituals@gmail.com\n\n"
)

_DESCRIPTION_EN = (
    "Sri Bala Tripurasundari Devi -- an original Telugu devotional song "
    "(bhakti geetam) composed for the child (Bala) form of the Goddess "
    "worshipped in the Sri Vidya tradition. Released for Day 2 of Dasara "
    "Navaratri 2026.\n\n"
    "Original lyrics and composition, sung in the channel family's own voice "
    "(recorded with AI-assisted music production tools), with visuals created "
    "using AI generation tools. This is wholly original work and does not "
    "infringe on anyone else's content.\n\n"
    "Bala Tripurasundari is one of the principal forms worshipped in Sri "
    "Vidya -- holding a book and a rosary, enshrined at the center of the "
    "Sri Chakra, granting knowledge and wisdom to her devotees in her child "
    "form. This song honors that form as part of Day 2 of the Navaratri "
    "celebrations.\n\n"
    "Play this during your Navaratri puja. Like, share, and subscribe with the "
    "bell on for more songs through the rest of this Navaratri season.\n\n"
    f"🎵 All Navaratri 2026 songs in one place: {NAVARATRI_PLAYLIST_URL}\n\n"
    "Credits:\n"
    "Vocals: Revathy V S L\n"
    "Lyrics & Composition: Mahanavi Spirituals\n"
    "Visuals: AI-generated\n\n"
    "© 2026 Mahanavi Spirituals. All Rights Reserved.\n"
    "Contact: mahanavispirituals@gmail.com\n\n"
    "Disclosure: this video uses AI-assisted vocal production and AI-generated "
    "visuals as part of its original creative process."
)

HASHTAGS = [
    "#BalaTripurasundari", "#DasaraNavaratri2026", "#NavaratriSongs",
    "#TeluguDevotionalSong", "#శ్రీవిద్య", "#LalithaDevi", "#SriChakra",
    "#BhaktiGeetam", "#Navaratri2026", "#DasaraDay2",
]

TAGS = [
    "Bala Tripurasundari", "Sri Vidya devi songs", "Lalitha Tripurasundari",
    "Navaratri songs telugu", "Sri Chakra devi", "Panchadasi mantra",
    "Navaratri day 2 song", "Devi bhakti geetam", "Telugu bhakti songs 2026",
    "Mahanavi Spirituals",
    "బాలా త్రిపురసుందరీ పాట", "దసరా నవరాత్రి పాటలు", "నవరాత్రి పాటలు తెలుగు",
    "శ్రీవిద్య భక్తి గీతాలు", "శ్రీచక్ర బాలా దేవి", "పంచదశీ మంత్రం",
]


def build_navaratri_day2_song_seo(total_duration_seconds: float) -> NavaratriSongSeoContent:
    """Builds the full Day 2 SEO content. `total_duration_seconds` must
    be the REAL measured song duration (ffprobe), not an assumed value
    -- used to compute real, correctly-gapped chapter timestamps (see
    build_chapters_te's docstring)."""
    description_te = (
        _DESCRIPTION_TE_BASE
        + build_chapters_te(total_duration_seconds)
        + "\n"
        + _DESCRIPTION_TE_CREDITS
        + LYRICS_TE
    )
    description = f"{description_te}\n{_DESCRIPTION_EN}"

    seen: set[str] = set()
    api_tags: list[str] = []
    for tag in [t.lstrip("#") for t in HASHTAGS] + TAGS:
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            api_tags.append(tag)

    return NavaratriSongSeoContent(
        title=TITLE, description=description, display_hashtags=HASHTAGS, api_tags=api_tags,
    )
