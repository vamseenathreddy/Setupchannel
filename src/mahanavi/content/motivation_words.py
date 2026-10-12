"""Daily "Purana motivation word" Short for Mahanavi: one short Telugu motivational word/phrase, a one-line
reason drawn from a Purana / Itihasa story, and the source. 2 seconds on screen (loops in the Shorts feed).

Rotation is stateless: bank[date.toordinal() % len(bank)], so a day never repeats until the whole bank has
been shown, and concurrent runs can never clobber a rotation counter. These are paraphrased teachings tied to
the named story, not verbatim quotations.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from datetime import date

from mahanavi.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE
from mahanavi.content.request_shorts import RequestShort, Slide


@dataclass(frozen=True)
class Word:
    word: str      # the motivation word / short phrase (big on the card)
    reason: str    # one line, why (story)
    source: str    # Purana / Itihasa and story
    deity: str = ""  # image folder key (assets/images/deities/<deity>_*.jpg); "" = date-random any


WORDS: tuple[Word, ...] = (
    Word("ధైర్యమే బలం", "ప్రహ్లాదుడు భయపడలేదు, నారసింహుడు రక్షించాడు", "ప్రహ్లాద చరిత్ర · భాగవతం", "narasimha"),
    Word("పట్టుదల విడవకు", "చిన్నవాడైన ధ్రువుడు తపస్సుతో శిఖరం చేరాడు", "ధ్రువ చరిత్ర · విష్ణు పురాణం", "vishnu"),
    Word("సత్యమే నిలుస్తుంది", "హరిశ్చంద్రుడు సత్యం కోసం సర్వం వదిలాడు", "హరిశ్చంద్ర కథ · మార్కండేయ పురాణం", "shiva"),
    Word("అహంకారం పతనం", "రావణుని అహంకారమే అతని అంతమైంది", "రామాయణం", "rama"),
    Word("చిన్న సేవ గొప్పదే", "ఉడుత చేసిన సాయం రాముని ప్రేమను పొందింది", "రామాయణం", "rama"),
    Word("భక్తికి లొంగును దైవం", "శబరి ఇచ్చిన పండ్లను రాముడు ప్రేమగా స్వీకరించాడు", "రామాయణం", "rama"),
    Word("శరణాగతే రక్ష", "గజేంద్రుడు మనసారా పిలవగానే హరి వచ్చాడు", "గజేంద్ర మోక్షం · భాగవతం", "vishnu"),
    Word("తల్లిదండ్రులే దైవం", "తల్లిదండ్రుల చుట్టూ తిరిగి గణపతి విజయం సాధించాడు", "గణపతి కథ · శివ పురాణం", "ganesha"),
    Word("సంకల్పమే శక్తి", "పార్వతి తపస్సుతో శివుని పొందింది", "పార్వతి తపస్సు · శివ పురాణం", "parvati"),
    Word("కృషితో సాధ్యం", "భగీరథుడు ప్రయత్నంతో గంగను భువికి తెచ్చాడు", "భగీరథ ప్రయత్నం · పురాణాలు", "shiva"),
    Word("లక్ష్యంపై దృష్టి", "అర్జునుడికి పక్షి కన్ను మాత్రమే కనిపించింది", "మహాభారతం", "krishna"),
    Word("గర్వం వద్దు", "ఇంద్రుని గర్వాన్ని గోవర్ధనగిరిధారి అణచాడు", "గోవర్ధన లీల · భాగవతం", "krishna"),
    Word("ఐక్యతే బలం", "వానరులంతా కలిసి శ్రీరాముని కోసం సేతువు కట్టారు", "రామసేతు నిర్మాణం · రామాయణం", "rama"),
    Word("బుద్ధిబలం గొప్పది", "హనుమంతుడు సురసను తెలివితో దాటాడు", "సుందరకాండ · రామాయణం", "hanuman"),
    Word("భక్తి మృత్యుంజయం", "మార్కండేయుడు శివభక్తితో మృత్యువును జయించాడు", "మార్కండేయ చరిత్ర · పురాణాలు", "shiva"),
    Word("సేవే సాధన", "హనుమంతుని నిస్వార్థ సేవ ఆయనను చిరంజీవిని చేసింది", "రామాయణం", "hanuman"),
    Word("ఓర్పు ఫలిస్తుంది", "పాండవులు ఓర్పుతో కష్టకాలాన్ని గెలిచారు", "మహాభారతం", "krishna"),
    Word("మంచి చెడుపై గెలుస్తుంది", "దేవి మహిషాసురుని సంహరించింది", "దేవీ మహాత్మ్యం · మార్కండేయ పురాణం", "durga"),
    Word("త్యాగమే గొప్పతనం", "శిబి చక్రవర్తి శరణు కోరిన పావురాన్ని కాపాడాడు", "శిబి కథ · మహాభారతం", "vishnu"),
    Word("గురువే దారి చూపుతాడు", "గురు ఉపదేశంతోనే శిష్యుడు శిఖరం చేరతాడు", "పురాణ బోధ", "saraswati"),
    Word("క్షమయే గొప్ప బలం", "వసిష్ఠుని క్షమ ముందు విశ్వామిత్రుని కోపం ఓడిపోయింది", "వసిష్ఠ విశ్వామిత్ర కథ · రామాయణం", "shiva"),
    Word("విశ్వాసమే వెలుగు", "నమ్మకం ఉన్నవాడికి చీకటిలోనూ దారి కనిపిస్తుంది", "పురాణ బోధ", "surya"),
    Word("ఆశకు అంతం లేదు", "యయాతి ఎన్ని భోగాలు అనుభవించినా తృప్తి చెందలేదు", "యయాతి కథ · భాగవతం", "vishnu"),
    Word("కృతజ్ఞత మరువకు", "చేసిన సాయాన్ని గుర్తుంచుకునేవాడే నిజమైన భక్తుడు", "రామాయణం", "hanuman"),
    Word("మాట నిలబెట్టుకో", "దశరథుడు ఇచ్చిన మాట కోసం ప్రాణం విడిచాడు", "రామాయణం", "rama"),
    Word("శ్రద్ధే విజయం", "ఏకలవ్యుడు శ్రద్ధతో విలువిద్యలో నిపుణుడయ్యాడు", "మహాభారతం", "murugan"),
    Word("వినయమే భూషణం", "వినయం ఉన్నవారిని దేవుడు ప్రేమిస్తాడు", "పురాణ బోధ", "hanuman"),
    Word("కష్టంలో కూడా నమ్ము", "సీతమ్మ కష్టంలోనూ రాముని నమ్మింది", "రామాయణం", "rama"),
    Word("స్నేహమే శక్తి", "కృష్ణ కుచేలుల స్నేహం కాలం గడిచినా నిలిచింది", "కుచేల కథ · భాగవతం", "krishna"),
    Word("నిస్వార్థ ప్రేమ", "గోపికల ప్రేమ ఏ ఫలమూ ఆశించలేదు", "భాగవతం", "krishna"),
)

CHANNEL = dict(token_file="youtube_token.json", expected="Mahanavi", watermark="@MahanaviSpirituals")
SLIDE_SECONDS = 2.0


INVOCATION = {
    "narasimha": "జై శ్రీ నరసింహ", "shiva": "ఓం నమః శివాయ", "rama": "జై శ్రీ రామ్", "krishna": "జై శ్రీ కృష్ణ",
    "hanuman": "జై శ్రీ ఆంజనేయ", "murugan": "ఓం శరవణభవ", "ganesha": "జై గణేశ", "vishnu": "ఓం నమో నారాయణాయ",
    "venkateswara": "ఓం నమో వేంకటేశాయ", "saraswati": "ఓం ఐం సరస్వత్యై నమః", "surya": "ఓం సూర్యాయ నమః",
    "durga": "జై మాతా దుర్గా", "lakshmi": "ఓం శ్రీ మహాలక్ష్మ్యై నమః", "parvati": "ఓం ఉమాయై నమః",
}


def image_for(d: date, w: Word) -> Path:
    """Date-seeded random photo of the word's deity (falls back to any deity photo)."""
    base = Path(__file__).resolve().parents[3] / "assets" / "images" / "deities"
    files = sorted(base.glob(f"{w.deity}_*.jpg")) if w.deity else []
    if not files:
        files = sorted(base.glob("*.jpg"))
    return random.Random(d.toordinal()).choice(files)


def pick(d: date) -> Word:
    return WORDS[d.toordinal() % len(WORDS)]


def build(d: date) -> RequestShort:
    w = pick(d)
    label = "నేటి పురాణ ప్రేరణ"
    title = f"{w.word} | నేటి పురాణ ప్రేరణ | Purana Motivation"
    desc = (f"🙏 నేటి పురాణ ప్రేరణ: {w.word}\n{w.reason}\n— {w.source}\n\n"
            "రోజూ రాత్రి 9 గంటలకు ఒక కొత్త పురాణ ప్రేరణ పదం. సబ్‌స్క్రైబ్ చేయండి.")
    desc_en = (f"Daily Purana motivation word ({d.strftime('%d %b %Y')}): {w.word}. {w.reason}. Source: {w.source}.")
    return RequestShort(
        slug=f"motivation_{d.isoformat()}", handle="", comment_id="", deity_te=w.word,
        bg_top=(10, 6, 40), bg_mid=(60, 24, 110), bg_bottom=(10, 6, 40), glow=(255, 190, 90),
        slides=(Slide("mantra", SLIDE_SECONDS, label, w.word, w.source, w.reason),),
        title=title, title_en=f"Purana Motivation of the Day - {d.strftime('%d %b %Y')}",
        description_te=desc, description_en=desc_en,
        hashtags=["#Shorts", "#Motivation", "#Puranas", "#TeluguMotivation", "#Devotional"],
        tags=["purana motivation", "telugu motivation", "puranas", "ప్రేరణ", "పురాణ ప్రేరణ", w.word, "mahanavi spirituals", "shorts"],
        lang="te", token_file=CHANNEL["token_file"], expected_channel=CHANNEL["expected"], watermark=CHANNEL["watermark"],
        header=d.strftime("%d %b %Y"), tag_footer="రోజూ రాత్రి 9 గంటలకు · సబ్‌స్క్రైబ్",
        cta_lines=(), footer_main=_CHANNEL_FOOTER_TE, footer_en=_CHANNEL_FOOTER_EN,
    )
