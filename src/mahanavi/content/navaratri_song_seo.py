"""
navaratri_song_seo.py: SEO content (title, description, hashtags) for
the first AI-generated devotional SONG video -- "Swarnakavachadharini
Kanakadurgamma", a Dasara Navaratri Day 1 bhakti geetam, original
composition with the channel owner's wife's own voice (via Suno),
visuals generated with fal.ai. Built 2026-10-03.

This is a one-off piece (not a rotating daily series like the other
content modules in this package), so unlike alert_seo.py /
purana_short_seo.py etc. there's no rotation/template logic here --
just the actual, final copy for this one upload.
"""

from __future__ import annotations

from mahanavi.content.alert_seo import ShortSeoContent

# Kept under YouTube's 100-character title limit (this is 83) --
# "Special"/"Bhakti Geetam" were dropped from an earlier 105-char draft.
TITLE = (
    "స్వర్ణకవచధారిణి కనకదుర్గమ్మా | Dasara Navaratri Day 1 Song 2026 "
    "| Kanaka Durga Devi"
)

_DESCRIPTION_TE = (
    "స్వర్ణకవచధారిణి కనకదుర్గమ్మా -- విజయవాడ ఇంద్రకీలాద్రిపై వెలసిన శ్రీ కనకదుర్గమ్మ తల్లిపై "
    "రచించిన ఒక సంపూర్ణ భక్తి గీతం. ఈ దసరా నవరాత్రుల సందర్భంగా, తొలి రోజు పూజకు అంకితం చేస్తూ "
    "ఈ పాటను మా ఛానల్ తరఫున అందిస్తున్నాం.\n\n"
    "ఈ గీతం పూర్తిగా స్వీయ రచన, స్వీయ స్వరకల్పన -- సాహిత్యం మొదటి నుండి కొత్తగా రాయబడింది, "
    "గానం మా కుటుంబ సభ్యురాలి స్వంత స్వరంతో చేయబడింది (AI-ఆధారిత సంగీత సాధనాల సహాయంతో రికార్డ్ "
    "చేయబడింది), మరియు దృశ్యాలు కూడా AI సాధనాలతో రూపొందించబడ్డాయి -- ఇది పూర్తిగా మా స్వంత సృజన, "
    "ఎవరి హక్కులను ఉల్లంఘించదు.\n\n"
    "కృష్ణా నదీ తీరాన, ఇంద్రకీలాద్రి శిఖరంపై స్వయంభువుగా వెలసిన అమ్మవారు త్రిశూలం, చక్రం వంటి "
    "ఆయుధాలు ధరించి సింహవాహినిగా దర్శనమిస్తుంది. నవరాత్రుల్లో ప్రత్యేక రోజున అమ్మవారికి చేసే "
    "స్వర్ణకవచాలంకరణ ఈ ఆలయానికే ప్రత్యేకం -- ఆ దివ్య రూపాన్ని స్మరిస్తూ ఈ గీతాన్ని అందిస్తున్నాం.\n\n"
    "భక్తులు ఈ పాటను నవరాత్రి పూజా సమయంలో ప్లే చేసుకోవచ్చు. మీకు నచ్చితే షేర్ చేయండి, లైక్ చేయండి, "
    "మా ఛానల్‌ని సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి -- ఈ నవరాత్రుల్లో రాబోయే మిగతా రోజుల పాటల "
    "కోసం.\n"
)

_DESCRIPTION_EN = (
    "Swarnakavachadharini Kanakadurgamma -- an original Telugu devotional song "
    "(bhakti geetam) composed for Goddess Kanaka Durga, enshrined atop "
    "Indrakeeladri hill on the banks of the Krishna river in Vijayawada. "
    "Released for Day 1 of Dasara Navaratri 2026.\n\n"
    "Original lyrics and composition, sung in the channel family's own voice "
    "(recorded with AI-assisted music production tools), with visuals created "
    "using AI generation tools. This is wholly original work and does not "
    "infringe on anyone else's content.\n\n"
    "The song honors the Devi's form at Indrakeeladri -- trishul and chakra in "
    "hand, seated on her lion vahana -- and her famous Swarna Kavacham (golden "
    "armor) alankaram, a tradition unique to this temple during Navaratri.\n\n"
    "Play this during your Navaratri puja. Like, share, and subscribe with the "
    "bell on for more songs through the rest of this Navaratri season.\n\n"
    "Disclosure: this video uses AI-assisted vocal production and AI-generated "
    "visuals as part of its original creative process."
)

DESCRIPTION = f"{_DESCRIPTION_TE}\n{_DESCRIPTION_EN}"

HASHTAGS = [
    "#KanakaDurga", "#DasaraNavaratri2026", "#NavaratriSongs",
    "#TeluguDevotionalSong", "#దుర్గమ్మ", "#DurgaDevi", "#Indrakeeladri",
    "#BhaktiGeetam", "#Navaratri2026", "#VijayawadaDurgaTemple",
]

TAGS = [
    "Kanaka Durga", "Kanakadurgamma", "Indrakeeladri", "Dasara Navaratri 2026",
    "Navaratri songs telugu", "Durga devi songs", "Telugu devotional song",
    "Swarna Kavacham", "Vijayawada Durga temple", "Navaratri day 1 song",
    "Durga bhakti geetam", "Telugu bhakti songs 2026", "Mahanavi Spirituals",
]


def build_navaratri_song_seo() -> ShortSeoContent:
    return ShortSeoContent(title=TITLE, description=DESCRIPTION, hashtags=HASHTAGS)
