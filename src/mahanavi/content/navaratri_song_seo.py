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

from dataclasses import dataclass

# The "Dussehra Navaratri Songs 2026" playlist -- matches
# MAHANAVI_PLAYLIST_ID_NAVARATRI_SONGS (set up via
# youtube_playlists_setup.py, 2026-10-03). Linked from the description
# below so viewers land on the rest of the season's songs as they go
# up, instead of this being a dead-end upload.
NAVARATRI_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLR7mQSUcrHXM"

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
    "కోసం.\n\n"
    f"🎵 నవరాత్రి 2026 పాటలు అన్నీ ఇక్కడ: {NAVARATRI_PLAYLIST_URL}\n\n"
    "క్రెడిట్స్:\n"
    "గానం: Revathy V S L\n"
    "సాహిత్యం & స్వరకల్పన: Mahanavi Spirituals\n"
    "దృశ్యాలు: AI సాధనాలతో రూపొందించబడ్డాయి\n\n"
    "© 2026 Mahanavi Spirituals. అన్ని హక్కులు రక్షించబడ్డాయి.\n"
    "సంప్రదించండి: mahanavispirituals@gmail.com\n"
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

DESCRIPTION = f"{_DESCRIPTION_TE}\n{_DESCRIPTION_EN}"

HASHTAGS = [
    "#KanakaDurga", "#DasaraNavaratri2026", "#NavaratriSongs",
    "#TeluguDevotionalSong", "#దుర్గమ్మ", "#DurgaDevi", "#Indrakeeladri",
    "#BhaktiGeetam", "#Navaratri2026", "#VijayawadaDurgaTemple",
]

TAGS = [
    # "Dasara Navaratri 2026" and "Telugu devotional song" deliberately
    # left out here -- near-duplicates of the "DasaraNavaratri2026" and
    # "TeluguDevotionalSong" hashtags already folded into api_tags
    # below, and the combined list has to stay under the API's 500
    # tag-character limit (build_navaratri_song_seo() hit 510 with
    # these included -- trimmed instead of cutting something unique).
    "Kanaka Durga", "Kanakadurgamma", "Indrakeeladri",
    "Navaratri songs telugu", "Durga devi songs",
    "Swarna Kavacham", "Vijayawada Durga temple", "Navaratri day 1 song",
    "Durga bhakti geetam", "Telugu bhakti songs 2026", "Mahanavi Spirituals",
    # Added 2026-10-03: Telugu-script tags -- the Latin-transliterated
    # tags above don't match searches typed in Telugu script, which is
    # how a large share of this channel's actual audience searches.
    "కనకదుర్గమ్మ పాట", "దసరా నవరాత్రి పాటలు", "నవరాత్రి పాటలు తెలుగు",
    "దుర్గమ్మ భక్తి గీతాలు", "ఇంద్రకీలాద్రి కనకదుర్గ", "స్వర్ణకవచం అలంకారం",
]


@dataclass(frozen=True, slots=True)
class NavaratriSongSeoContent:
    """Satisfies YouTubeShortsUploader's UploadableSeoContent protocol
    (title / hashtags / full_caption()) like alert_seo.ShortSeoContent
    does, but SPLITS what that shared dataclass conflates: the
    `hashtags` property there does double duty as both the visible
    description hashtags AND the video's hidden API `tags` field
    (uploader code: `"tags": [tag.lstrip("#") for tag in seo.hashtags]`).
    That's fine for the rotating daily series, which only ever want
    one small hashtag set either way, but this one-off song has a
    much richer keyword list (TAGS, including Telugu-script terms)
    that should reach the API tags field WITHOUT also being dumped as
    20 visible hashtags under the title -- so `hashtags` below returns
    the combined keyword-rich set for the API, while `full_caption()`
    uses only `display_hashtags` (HASHTAGS) for what's actually shown.
    """
    title: str
    description: str
    display_hashtags: list[str]
    api_tags: list[str]

    @property
    def hashtags(self) -> list[str]:
        return self.api_tags

    def full_caption(self) -> str:
        return f"{self.description}\n\n{' '.join(self.display_hashtags)}"


def build_navaratri_song_seo() -> NavaratriSongSeoContent:
    # Combine the visible hashtags (minus '#') with the long-tail TAGS
    # for the API tags field, deduping case-insensitively so near-dupes
    # like "#KanakaDurga" / "Kanaka Durga" don't both burn space.
    seen: set[str] = set()
    api_tags: list[str] = []
    for tag in [t.lstrip("#") for t in HASHTAGS] + TAGS:
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            api_tags.append(tag)

    return NavaratriSongSeoContent(
        title=TITLE, description=DESCRIPTION, display_hashtags=HASHTAGS, api_tags=api_tags,
    )
