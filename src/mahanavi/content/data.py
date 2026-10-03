"""
Deity-specific content building blocks used by the SEO/caption generator.

Kept separate from generator.py so a Telugu speaker (or you, later) can
review/tweak the devotional phrasing, mantras, and keyword lists without
touching any generation logic. Add a new deity here and the generator
picks it up automatically — no other code changes needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from mahanavi.core.models import Deity


@dataclass(frozen=True, slots=True)
class DeityContent:
    telugu_name: str
    blessing_phrase: str        # short devotional opening line
    mantra: str                  # traditional chant/mantra
    # 2-3 valid beeja-mantram phrasings for this deity -- see per-deity
    # notes below on confidence. Rotated by date (not truly random) via
    # pick_beeja_mantram() below, so the SAME date always shows the SAME
    # variant (reproducible across retries) while still varying day to
    # day instead of being identical every single week -- explicit
    # request, since a fixed chant every Monday felt repetitive.
    beeja_mantrams: list[str] = field(default_factory=list)
    # 2-5 alternate names/mantras for this deity (distinct from the
    # beeja_mantrams above, which are seed-syllable chants) -- added
    # 2026-10-03 so the alert Shorts (post_alert_shorts.py) can rotate
    # through a deity's own mantra namalu instead of always showing the
    # single fixed `mantra` string above. First entry is conventionally
    # the same as `mantra` so a deity with no extra variants entered yet
    # still works. Rotated the same way as beeja_mantrams.
    mantra_namalu: list[str] = field(default_factory=list)
    telugu_hashtags: list[str] = field(default_factory=list)
    english_keywords: list[str] = field(default_factory=list)


def pick_beeja_mantram(content: DeityContent, for_date: date) -> str:
    """Deterministic day-to-day rotation through a deity's beeja mantram
    pool -- same pattern as the subscribe-line rotation in
    post_alert_shorts.py (pool[date.toordinal() % len(pool)]), so a given
    date always renders the same variant (reproducible on a retry) while
    the chant shown genuinely varies across the week/month."""
    if not content.beeja_mantrams:
        raise ValueError("DeityContent.beeja_mantrams is empty -- every deity needs at least one.")
    return content.beeja_mantrams[for_date.toordinal() % len(content.beeja_mantrams)]


DEITY_CONTENT: dict[Deity, DeityContent] = {
    Deity.SHIVA: DeityContent(
        telugu_name="శివుడు",
        blessing_phrase="ఓం నమః శివాయ 🙏",
        mantra="ఓం నమః శివాయ",
        beeja_mantrams=[
            "ఓం హౌం నమః శివాయ",   # Haum + the core mantra, fuller than a bare syllable
            "ఓం నమః శివాయ",         # the Panchakshari mantra itself, also used as a seed chant
            "ఓం సాంబశివాయ నమః",     # Sambashiva form, commonly chanted on Mondays
        ],
        mantra_namalu=[
            "ఓం నమః శివాయ",
            "ఓం సాంబశివాయ నమః",
            "శివ శివ శంకర భక్త వశంకర",
        ],
        telugu_hashtags=["#శివుడు", "#మహాదేవుడు", "#సోమవారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Shiva", "Shiva Panchangam today", "Monday Shiva special",
            "Om Namah Shivaya", "Shiva devotional", "Telugu panchangam",
        ],
    ),
    Deity.HANUMAN: DeityContent(
        telugu_name="హనుమంతుడు",
        blessing_phrase="జై హనుమాన్ 🙏",
        mantra="ఓం హనుమతే నమః",
        beeja_mantrams=[
            "ఓం హ్రాం హనుమతే నమః",   # Hraam + full mantra, fuller than a bare syllable
            "ఓం హనుమతే నమః",           # base form
            "ఓం ఆంజనేయాయ నమః",        # Anjaneya form, equally common
        ],
        mantra_namalu=[
            "ఓం హనుమతే నమః",
            "జై బజరంగ్ బలీ",
            "ఓం ఆంజనేయాయ నమః",
        ],
        telugu_hashtags=["#హనుమంతుడు", "#ఆంజనేయస్వామి", "#మంగళవారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Hanuman", "Hanuman Panchangam today", "Tuesday Hanuman special",
            "Jai Hanuman", "Hanuman devotional", "Telugu panchangam",
        ],
    ),
    Deity.GANESHA: DeityContent(
        telugu_name="గణేశుడు",
        blessing_phrase="ఓం గణ గణపతయే నమః 🙏",
        mantra="వక్రతుండ మహాకాయ సూర్యకోటి సమప్రభ నిర్విఘ్నం కురు మే దేవ సర్వ కార్యేషు సర్వదా",
        beeja_mantrams=[
            "ఓం గం గణపతయే నమః",     # full traditional Ganesha bija mantra (Om Gam Ganapataye Namaha)
            "ఓం వక్రతుండాయ నమః",     # Vakratunda form
            "ఓం శ్రీ గణేశాయ నమః",
        ],
        mantra_namalu=[
            "ఓం గం గణపతయే నమః",
            "ఓం వక్రతుండాయ నమః",
            "ఓం శ్రీ గణేశాయ నమః",
        ],
        telugu_hashtags=["#గణేశుడు", "#వినాయకుడు", "#బుధవారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Ganesha", "Ganesha Panchangam today", "Wednesday Ganesha special",
            "Vinayaka devotional", "Ganpati", "Telugu panchangam",
        ],
    ),
    Deity.SAI: DeityContent(
        telugu_name="సాయిబాబా",
        blessing_phrase="ఓం సాయి రాం 🙏",
        mantra="శ్రీ సాయినాథాయ నమః",
        # Sai Baba is a 19th/20th-century saint, not a Puranic deity with a
        # classical Vedic bija syllable -- using standard short chants
        # rather than fabricating a beeja that doesn't traditionally
        # exist. NOTE: as of the Thursday deity change below, Sai is no
        # longer in WEEKDAY_DEITY_MAP's daily rotation (Thursday now goes
        # to Dattatreya, per explicit request to stop it always being
        # Sai) -- kept here so it's a one-line change to bring back for a
        # Sai-specific festival post later.
        beeja_mantrams=[
            "ఓం సాయి రాం",
            "శ్రీ సాయినాథాయ నమః",
        ],
        mantra_namalu=[
            "శ్రీ సాయినాథాయ నమః",
            "ఓం సాయి రాం",
        ],
        telugu_hashtags=["#సాయిబాబా", "#షిర్డీసాయి"],
        english_keywords=[
            "Shirdi Sai Baba", "Sai Baba devotional", "Om Sai Ram", "Telugu panchangam",
        ],
    ),
    Deity.LAKSHMI: DeityContent(
        telugu_name="లక్ష్మీదేవి",
        blessing_phrase="ఓం శ్రీ మహాలక్ష్మ్యై నమః 🙏",
        mantra="ఓం శ్రీం మహాలక్ష్మ్యై నమః",
        beeja_mantrams=[
            "ఓం శ్రీం నమః",                    # Shreem + namah, fuller than a bare syllable
            "ఓం శ్రీం మహాలక్ష్మ్యై నమః",
            "ఓం హ్రీం శ్రీం క్లీం మహాలక్ష్మ్యై నమః",  # fuller tantric form, still widely used
        ],
        mantra_namalu=[
            "ఓం శ్రీం మహాలక్ష్మ్యై నమః",
            "శ్రీ మహాలక్ష్మీ నమస్తుభ్యం",
            "ఓం హ్రీం శ్రీం క్లీం మహాలక్ష్మ్యై నమః",
        ],
        telugu_hashtags=["#లక్ష్మీదేవి", "#మహాలక్ష్మి", "#శుక్రవారం_ప్రత్యేకం"],
        english_keywords=[
            "Goddess Lakshmi", "Lakshmi Panchangam today", "Friday Lakshmi special",
            "Mahalakshmi devotional", "Telugu panchangam", "wealth goddess blessings",
        ],
    ),
    Deity.VENKATESWARA: DeityContent(
        telugu_name="వేంకటేశ్వర స్వామి",
        blessing_phrase="ఓం నమో వేంకటేశాయ 🙏",
        mantra="గోవిందా గోవిందా",
        # Less standardized across traditions than Ganesha/Lakshmi's bija --
        # worth a native speaker's confirmation before treating as final.
        beeja_mantrams=[
            "ఓం క్లీం వేంకటేశాయ నమః",
            "ఓం నమో వేంకటేశాయ",
            "ఓం శ్రీనివాసాయ నమః",
        ],
        # Explicit request (2026-10-03): rotate through Venkateswara's
        # OWN mantra namalu instead of always showing "గోవిందా గోవిందా"
        # -- see post_alert_shorts._mantra_lines.
        mantra_namalu=[
            "గోవిందా గోవిందా",
            "ఓం నమో వేంకటేశాయ",
            "శ్రీనివాసా గోవిందా",
            "వేంకటరమణా గోవిందా",
            "ఓం శ్రీనివాసాయ నమః",
        ],
        telugu_hashtags=["#వేంకటేశ్వరుడు", "#తిరుమల", "#శనివారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Venkateswara", "Venkateswara Panchangam today", "Saturday Balaji special",
            "Tirumala Tirupati", "Govinda Govinda", "Telugu panchangam",
        ],
    ),
    Deity.SURYA: DeityContent(
        telugu_name="సూర్యభగవానుడు",
        blessing_phrase="ఓం సూర్యాయ నమః 🙏",
        mantra="ఓం ఘృణి సూర్యాయ నమః",
        beeja_mantrams=[
            "ఓం హ్రాం సూర్యాయ నమః",   # Hraam + full mantra, fuller than a bare syllable
            "ఓం ఘృణి సూర్యాయ నమః",     # matches the main mantra, also valid as a seed chant
            "ఓం సూర్యాయ నమః",
        ],
        mantra_namalu=[
            "ఓం ఘృణి సూర్యాయ నమః",
            "ఓం సూర్యాయ నమః",
            "ఓం హ్రాం మిత్రాయ నమః",
        ],
        telugu_hashtags=["#సూర్యభగవానుడు", "#ఆదిత్యహృదయం", "#ఆదివారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Surya", "Surya Panchangam today", "Sunday Surya special",
            "Surya Namaskar devotional", "Aditya Hrudayam", "Telugu panchangam",
        ],
    ),
    Deity.DATTATREYA: DeityContent(
        telugu_name="దత్తాత్రేయ స్వామి",
        blessing_phrase="ఓం శ్రీ గురుదేవ దత్త 🙏",
        mantra="ఓం శ్రీ గురుదేవ దత్త",
        # Replaces Sai Baba as Thursday's (Guruvaram's) deity per explicit
        # request. Dattatreya -- combined form of Brahma/Vishnu/Shiva as
        # the primordial Guru -- is the classical Thursday/Guruvaram
        # deity in Telugu tradition, distinct from (and older than) the
        # Sai Baba association. Worth a native speaker's confirmation on
        # phrasing before treating as final, same caveat as Venkateswara
        # above.
        beeja_mantrams=[
            "ఓం ద్రాం దత్తాత్రేయాయ నమః",   # classical beeja (Om Draam Dattatreyaya Namaha)
            "ఓం శ్రీ గురుదేవ దత్త",          # most common simple chant among devotees
            "దిగంబరా దిగంబరా శ్రీపాద వల్లభ దిగంబరా",  # very popular Datta-tradition chant
        ],
        mantra_namalu=[
            "ఓం శ్రీ గురుదేవ దత్త",
            "దిగంబరా దిగంబరా శ్రీపాద వల్లభ దిగంబరా",
            "ఓం ద్రాం దత్తాత్రేయాయ నమః",
        ],
        telugu_hashtags=["#దత్తాత్రేయుడు", "#గురుదేవదత్త", "#గురువారం_ప్రత్యేకం"],
        english_keywords=[
            "Lord Dattatreya", "Dattatreya Panchangam today", "Thursday Guruvaram special",
            "Om Sri Gurudev Datta", "Dattatreya devotional", "Telugu panchangam",
        ],
    ),
}

# Which deity corresponds to which weekday -- matches
# config.WEEKDAY_FOLDER_MAP's day assignments (Python's date.weekday():
# Monday=0 ... Sunday=6). Used by anything that needs "today's deity"
# without also needing an actual selected image (e.g. the alert Shorts,
# which have no deity image of their own but still want today's mantra).
#
# NOTE: Thursday was changed from Sai to Dattatreya per explicit request
# (Sai was showing every single Thursday with no variety) -- if the main
# community-post pipeline (currently disabled) is ever revived, its
# Images/Thursday_Sai folder won't match this mapping until it's renamed
# or a Thursday_Dattatreya folder with real images is added; the Shorts
# pipeline (post_alert_shorts.py) doesn't use deity images at all, so
# this change is fully effective for Shorts right away.
WEEKDAY_DEITY_MAP: dict[int, Deity] = {
    0: Deity.SHIVA,
    1: Deity.HANUMAN,
    2: Deity.GANESHA,
    3: Deity.DATTATREYA,
    4: Deity.LAKSHMI,
    5: Deity.VENKATESWARA,
    6: Deity.SURYA,
}

# General hashtags applied across every post regardless of deity.
GENERAL_TELUGU_HASHTAGS: list[str] = [
    "#పంచాంగం", "#తెలుగుపంచాంగం", "#భక్తి", "#దైవం", "#మహానవిస్పిరిచువల్స్",
]

# Curated devotional hashtags that tend to have broad reach/trend cyclically.
# Review and refresh this list periodically — hashtag popularity shifts over time.
TRENDING_DEVOTIONAL_HASHTAGS: list[str] = [
    "#Devotional", "#Bhakti", "#TeluguPanchangam", "#DailyPanchangam",
    "#HinduDevotional", "#Spirituality", "#TempleVibes", "#GodBless",
]

GENERAL_ENGLISH_KEYWORDS: list[str] = [
    "Telugu panchangam today", "daily panchangam", "Hindu devotional content",
    "Telugu devotional channel", "today's panchangam", "rahu kalam today",
    "auspicious time today",
]
