"""Viewer-request Shorts: a one-off mantra Short made because a viewer asked for it in the comments
(first one: "Narsimha Swamy mantram send me", 2026-10-09). The Short is tagged to the viewer, uses a
background colour no scheduled Short uses, and is uploaded PRIVATE so the owner can verify it in
Studio before publishing.

Each request is a `RequestShort` spec: the slides (intro, one per mantra, outro), the SEO and the
reply text for the viewer's comment. Add a new spec to SPECS to make the next one.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE
from mahanavi.content.branding import BRAND_NAME


@dataclass(frozen=True)
class Slide:
    kind: str                 # "intro" | "mantra" | "outro"
    seconds: float
    label_te: str = ""        # small gold heading, e.g. "బీజ మంత్రం"
    text_te: str = ""         # the mantra (Telugu script); "\n" keeps verse lines apart
    translit: str = ""        # English transliteration
    meaning_te: str = ""      # one short Telugu line


@dataclass(frozen=True)
class RequestShort:
    slug: str
    handle: str               # the viewer's @handle, shown on the Short and tagged in the description
    comment_id: str           # the viewer's comment (for the reply once the Short is public)
    deity_te: str
    bg_top: tuple[int, int, int]
    bg_mid: tuple[int, int, int]
    bg_bottom: tuple[int, int, int]
    glow: tuple[int, int, int]
    slides: tuple[Slide, ...]
    title: str
    description_te: str
    description_en: str
    title_en: str
    hashtags: list[str]
    tags: list[str] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        return sum(s.seconds for s in self.slides)

    def description(self) -> str:
        return (f"{self.description_te}\n\n{_CHANNEL_FOOTER_TE}\n\n---\n\n{self.description_en}\n\n"
                f"{_CHANNEL_FOOTER_EN}\n\n{' '.join(self.hashtags)}")

    def reply_text(self, video_url: str) -> str:
        """Reply to the viewer's own comment once the Short is public."""
        return (f"{self.handle} మీరు అడిగిన {self.deity_te} మంత్రాలను ఈ వీడియోలో అందించాం 🙏 "
                f"బీజ మంత్రం, గాయత్రి, మహా మంత్రం అన్నీ ఉన్నాయి. చూడండి: {video_url}")

    def first_comment(self) -> str:
        lines = "\n".join(f"{s.label_te}: {s.text_te.replace(chr(10), ' ')}" for s in self.slides if s.kind == "mantra")
        return (f"🙏 {self.handle} గారి కోరిక మేరకు {self.deity_te} మంత్రాలు:\n\n{lines}\n\n"
                "ఏ మంత్రం మీకు ఇష్టం? కామెంట్ చేయండి 🙏")


HANDLE = "@SsudharshanSsudharshan-h7n"

_NARASIMHA_SLIDES = (
    Slide("intro", 3.5),
    Slide("mantra", 5.5, "బీజ మంత్రం", "ఓం నృం నృం నృం నరసింహాయ నమః",
          "Om Nrim Nrim Nrim Narasimhaya Namah",
          "నరసింహ బీజాక్షరాలు: నృం · క్ష్రౌం"),
    Slide("mantra", 5.5, "మూల మంత్రం", "ఓం నమో భగవతే నరసింహాయ",
          "Om Namo Bhagavate Narasimhaya",
          "భగవంతుడైన నరసింహ స్వామికి నమస్కారం"),
    Slide("mantra", 7.5, "నరసింహ గాయత్రి", "ఓం వజ్రనఖాయ విద్మహే\nతీక్ష్ణదంష్ట్రాయ ధీమహి\nతన్నో నృసింహః ప్రచోదయాత్",
          "Om Vajranakhaya Vidmahe, Tikshna Damshtraya Dhimahi, Tanno Narasimhah Prachodayat",
          "వజ్రాల వంటి గోళ్లు, వాడి కోరలు గల నరసింహుడిని ధ్యానిస్తున్నాం"),
    Slide("mantra", 7.5, "మహా మంత్రం", "ఉగ్రం వీరం మహావిష్ణుం జ్వలంతం సర్వతోముఖమ్\nనృసింహం భీషణం భద్రం మృత్యుమృత్యుం నమామ్యహమ్",
          "Ugram Veeram Maha Vishnum Jwalantam Sarvato Mukham, Nrisimham Bhishanam Bhadram Mrityu-Mrityum Namamyaham",
          "మృత్యువుకే మృత్యువైన శుభకరుడు నృసింహునికి నమస్కారం"),
    Slide("outro", 4.5),
)

_DESC_TE = f"""🙏 {HANDLE} గారి కోరిక మేరకు శ్రీ నరసింహ స్వామి మంత్రాలు (బీజ మంత్రంతో సహా)

1) బీజ మంత్రం: ఓం నృం నృం నృం నరసింహాయ నమః
2) మూల మంత్రం: ఓం నమో భగవతే నరసింహాయ
3) నరసింహ గాయత్రి: ఓం వజ్రనఖాయ విద్మహే తీక్ష్ణదంష్ట్రాయ ధీమహి తన్నో నృసింహః ప్రచోదయాత్
4) మహా మంత్రం: ఉగ్రం వీరం మహావిష్ణుం జ్వలంతం సర్వతోముఖమ్ | నృసింహం భీషణం భద్రం మృత్యుమృత్యుం నమామ్యహమ్

ఎలా చదవాలి: శుభ్రంగా, ప్రశాంతంగా కూర్చుని ప్రతి మంత్రం 11, 21 లేదా 108 సార్లు చదవండి. శనివారం మరియు నరసింహ జయంతి రోజున చదవడం శుభప్రదమని సంప్రదాయం. ఉచ్చారణ కోసం గురువు లేదా పెద్దల వద్ద నేర్చుకోవడం మంచిది.

మీ అభిప్రాయాన్ని కామెంట్ చేయండి. మరిన్ని మంత్రాల కోసం మహానవి స్పిరిచువల్స్ ఛానల్‌ను సబ్‌స్క్రైబ్ చేయండి 🙏"""

_DESC_EN = f"""Narasimha Swamy mantras, including the Beeja (seed) mantra, made on request for {HANDLE}.

1) Beeja mantra: Om Nrim Nrim Nrim Narasimhaya Namah
2) Moola mantra: Om Namo Bhagavate Narasimhaya
3) Narasimha Gayatri: Om Vajranakhaya Vidmahe, Tikshna Damshtraya Dhimahi, Tanno Narasimhah Prachodayat
4) Maha mantra: Ugram Veeram Maha Vishnum Jwalantam Sarvato Mukham, Nrisimham Bhishanam Bhadram Mrityu-Mrityum Namamyaham

How to chant: sit calmly in a clean place and chant each mantra 11, 21 or 108 times. Saturdays and Narasimha Jayanti are traditionally considered auspicious. Learn the pronunciation from a guru or elder if you can.

Tell us which mantra you chant in the comments, and subscribe to {BRAND_NAME} for more mantras."""

NARASIMHA = RequestShort(
    slug="narasimha_mantras",
    handle=HANDLE,
    comment_id="UgxXYvZw2NgMcZ7F28d4AaABAg",
    deity_te="శ్రీ నరసింహ స్వామి",
    bg_top=(6, 14, 52), bg_mid=(14, 40, 116), bg_bottom=(6, 18, 60), glow=(255, 176, 64),
    slides=_NARASIMHA_SLIDES,
    title="నరసింహ స్వామి బీజ మంత్రం + 3 మంత్రాలు | Narasimha Mantra",
    title_en="Narasimha Swamy Beeja Mantra + 3 Powerful Mantras | Narasimha Gayatri",
    description_te=_DESC_TE,
    description_en=_DESC_EN,
    hashtags=["#Shorts", "#నరసింహస్వామి", "#NarasimhaMantra", "#NarasimhaSwamy", "#Devotional"],
    tags=[
        "narasimha mantra", "narasimha swamy mantram", "narasimha beeja mantra", "narasimha gayatri",
        "ugram veeram mahavishnum", "lakshmi narasimha mantra", "narasimha mantra telugu",
        "నరసింహ స్వామి మంత్రం", "నరసింహ మంత్రం", "నరసింహ బీజ మంత్రం", "నరసింహ గాయత్రి",
        "నరసింహ జయంతి", "telugu devotional", "mahanavi spirituals", "shorts",
    ],
)

SPECS: dict[str, RequestShort] = {NARASIMHA.slug: NARASIMHA}
