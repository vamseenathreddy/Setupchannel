"""Daily 6 AM beej (seed) mantra Short: one deity per day, chosen by festival, then tithi, then weekday.
Built as a `RequestShort` (intro / mantra / outro) so the viewer-request renderer and assembler are reused.

Honest labelling: a deity's seed syllable mantra (Gam, Kleem, Hreem...) is shown as the beej mantra; deities
whose best-known short mantra has no seed syllable (Shiva, Vishnu, Subrahmanya) are labelled moola mantra.
Festival dates are hardcoded for 2026 (same source as check_festival_today.FESTIVALS_2026): refresh yearly.
"""
from __future__ import annotations
from ytcore.brandcfg import A_HANDLE, A_NAME, A_SHORT, B_HANDLE, B_NAME, B_SHORT, C_HANDLE, C_NAME, C_SHORT  # noqa: E402

from dataclasses import dataclass
from datetime import date
from typing import Any

from ytcore.content.alert_seo import _CHANNEL_FOOTER_EN, _CHANNEL_FOOTER_TE
from ytcore.content.request_shorts import _HI_FOOTER, RequestShort, Slide


@dataclass(frozen=True)
class Deity:
    key: str
    te: str
    hi: str
    mantra_te: str
    mantra_hi: str
    translit: str
    beej: bool                       # True = seed-syllable (beej) mantra, False = moola mantra
    gain_te: str
    gain_hi: str
    palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]


def _p(top: tuple[int, int, int], mid: tuple[int, int, int], glow: tuple[int, int, int]) -> Any:
    return (top, mid, top, glow)


DEITIES: dict[str, Deity] = {d.key: d for d in (
    Deity("ganesha", "శ్రీ గణపతి", "श्री गणेश", "ఓం గం గణపతయే నమః", "ॐ गं गणपतये नमः", "Om Gam Ganapataye Namah", True,
          "విఘ్నాలు తొలగి కార్యసిద్ధి కలుగుతుందని నమ్మకం", "विघ्न दूर हों और कार्य सिद्ध हों", _p((60, 24, 6), (140, 70, 16), (255, 170, 60))),
    Deity("shiva", "శ్రీ శివుడు", "भगवान शिव", "ఓం నమః శివాయ", "ॐ नमः शिवाय", "Om Namah Shivaya", False,
          "మనశ్శాంతి మరియు శివానుగ్రహం కోసం", "मन की शांति और शिवकृपा के लिए", _p((8, 18, 40), (22, 60, 100), (150, 210, 255))),
    Deity("vishnu", "శ్రీ మహావిష్ణువు", "भगवान विष्णु", "ఓం నమో నారాయణాయ", "ॐ नमो नारायणाय", "Om Namo Narayanaya", False,
          "శాంతి, రక్షణ మరియు విష్ణు అనుగ్రహం కోసం", "शांति, रक्षा और विष्णुकृपा के लिए", _p((6, 22, 50), (16, 70, 120), (255, 214, 110))),
    Deity("krishna", "శ్రీ కృష్ణుడు", "श्री कृष्ण", "ఓం క్లీం కృష్ణాయ నమః", "ॐ क्लीं कृष्णाय नमः", "Om Kleem Krishnaya Namah", True,
          "ప్రేమ, భక్తి మరియు కృష్ణానుగ్రహం కోసం", "प्रेम, भक्ति और कृष्णकृपा के लिए", _p((10, 20, 60), (30, 50, 130), (255, 220, 120))),
    Deity("rama", "శ్రీ రాముడు", "श्री राम", "ఓం రాం రామాయ నమః", "ॐ रां रामाय नमः", "Om Raam Ramaya Namah", True,
          "ధైర్యం, ధర్మబలం మరియు రామానుగ్రహం కోసం", "साहस, धर्मबल और रामकृपा के लिए", _p((10, 36, 40), (20, 90, 90), (255, 224, 140))),
    Deity("narasimha", "శ్రీ నరసింహ స్వామి", "भगवान नरसिंह", "ఓం నృం నృం నృం నరసింహాయ నమః", "ॐ नृं नृं नृं नरसिंहाय नमः",
          "Om Nrim Nrim Nrim Narasimhaya Namah", True, "భయం తొలగి రక్షణ కలుగుతుందని నమ్మకం", "भय दूर हो और रक्षा मिले", _p((60, 14, 6), (150, 50, 14), (255, 190, 80))),
    Deity("hanuman", "శ్రీ ఆంజనేయ స్వామి", "श्री हनुमान", "ఓం హం హనుమతే నమః", "ॐ हं हनुमते नमः", "Om Ham Hanumate Namah", True,
          "బలం, ధైర్యం మరియు ఆంజనేయ అనుగ్రహం కోసం", "बल, साहस और हनुमानकृपा के लिए", _p((70, 20, 4), (170, 60, 10), (255, 200, 90))),
    Deity("subrahmanya", "శ్రీ సుబ్రహ్మణ్య స్వామి", "भगवान कार्तिकेय", "ఓం శరవణభవాయ నమః", "ॐ शरवणभवाय नमः", "Om Saravanabhavaya Namah", False,
          "జ్ఞానం, ధైర్యం మరియు సుబ్రహ్మణ్య అనుగ్రహం కోసం", "ज्ञान, साहस और कार्तिकेय कृपा के लिए", _p((40, 10, 40), (110, 30, 100), (255, 190, 100))),
    Deity("durga", "శ్రీ దుర్గా దేవి", "माँ दुर्गा", "ఓం దుం దుర్గాయై నమః", "ॐ दुं दुर्गायै नमः", "Om Dum Durgayai Namah", True,
          "శక్తి, రక్షణ మరియు అమ్మవారి అనుగ్రహం కోసం", "शक्ति, रक्षा और माँ की कृपा के लिए", _p((64, 6, 14), (150, 20, 40), (255, 190, 120))),
    Deity("lakshmi", "శ్రీ మహాలక్ష్మి", "माँ लक्ष्मी", "ఓం శ్రీం మహాలక్ష్మ్యై నమః", "ॐ श्रीं महालक्ष्म्यै नमः", "Om Shreem Mahalakshmyai Namah", True,
          "ఐశ్వర్యం, శుభం మరియు లక్ష్మీ కటాక్షం కోసం", "सुख-समृद्धि और लक्ष्मीकृपा के लिए", _p((50, 30, 4), (140, 100, 14), (255, 230, 130))),
    Deity("saraswati", "శ్రీ సరస్వతీ దేవి", "माँ सरस्वती", "ఓం ఐం సరస్వత్యై నమః", "ॐ ऐं सरस्वत्यै नमः", "Om Aim Saraswatyai Namah", True,
          "విద్య, జ్ఞానం మరియు వాక్శుద్ధి కోసం", "विद्या, ज्ञान और वाणी की शुद्धि के लिए", _p((20, 22, 56), (60, 70, 150), (255, 255, 235))),
    Deity("kali", "శ్రీ కాళికా దేవి", "माँ काली", "ఓం క్రీం కాళికాయై నమః", "ॐ क्रीं कालिकायै नमः", "Om Kreem Kalikayai Namah", True,
          "భయ నివారణ మరియు శక్తి కోసం", "भय निवारण और शक्ति के लिए", _p((20, 4, 20), (80, 10, 50), (255, 120, 120))),
    Deity("dattatreya", "శ్రీ దత్తాత్రేయ స్వామి", "भगवान दत्तात्रेय", "ఓం ద్రాం దత్తాత్రేయాయ నమః", "ॐ द्रां दत्तात्रेयाय नमः", "Om Draam Dattatreyaya Namah", True,
          "గురు అనుగ్రహం మరియు జ్ఞానం కోసం", "गुरुकृपा और ज्ञान के लिए", _p((50, 34, 6), (130, 90, 20), (255, 215, 120))),
    Deity("surya", "శ్రీ సూర్య భగవానుడు", "भगवान सूर्य", "ఓం హ్రాం హ్రీం హ్రౌం సః సూర్యాయ నమః", "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
          "Om Hraam Hreem Hraum Sah Suryaya Namah", True, "ఆరోగ్యం, తేజస్సు మరియు సూర్యానుగ్రహం కోసం", "स्वास्थ्य, तेज और सूर्यकृपा के लिए", _p((70, 24, 4), (180, 80, 10), (255, 210, 80))),
    Deity("shani", "శని దేవుడు", "शनिदेव", "ఓం ప్రాం ప్రీం ప్రౌం సః శనయే నమః", "ॐ प्रां प्रीं प्रौं सः शनये नमः",
          "Om Praam Preem Proum Sah Shanaye Namah", True, "శని దోష శాంతి మరియు క్రమశిక్షణ కోసం", "शनि दोष की शांति के लिए", _p((8, 8, 16), (26, 28, 58), (130, 150, 255))),
)}

# Weekday (Mon=0): the day's traditional deity.
WEEKDAY = {0: "shiva", 1: "hanuman", 2: "ganesha", 3: "dattatreya", 4: "lakshmi", 5: "shani", 6: "surya"}

# (paksha-agnostic or per paksha) tithi -> deity. (shukla, krishna)
TITHI_DEITY: dict[str, tuple[str, str]] = {
    "chaturthi": ("ganesha", "ganesha"), "panchami": ("lakshmi", "lakshmi"), "shashthi": ("subrahmanya", "subrahmanya"),
    "saptami": ("surya", "surya"), "ashtami": ("durga", "krishna"), "navami": ("rama", "durga"),
    "ekadashi": ("vishnu", "vishnu"), "dwadashi": ("krishna", "krishna"), "trayodashi": ("shiva", "shiva"),
    "chaturdashi": ("narasimha", "shiva"), "purnima": ("lakshmi", "lakshmi"), "amavasya": ("kali", "kali"),
}

# 2026 festival overrides: date -> (deity, label_te, label_hi). Navaratri 11-19 Oct (3 days each Durga/Lakshmi/Saraswati).
FESTIVAL_DEITY: dict[date, tuple[str, str, str]] = {}
for _d in (11, 12, 13):
    FESTIVAL_DEITY[date(2026, 10, _d)] = ("durga", "శరన్నవరాత్రులు · దుర్గా రూపం", "शारदीय नवरात्रि · दुर्गा रूप")
for _d in (14, 15, 16):
    FESTIVAL_DEITY[date(2026, 10, _d)] = ("lakshmi", "శరన్నవరాత్రులు · లక్ష్మీ రూపం", "शारदीय नवरात्रि · लक्ष्मी रूप")
for _d in (17, 18, 19):
    FESTIVAL_DEITY[date(2026, 10, _d)] = ("saraswati", "శరన్నవరాత్రులు · సరస్వతీ రూపం", "शारदीय नवरात्रि · सरस्वती रूप")
FESTIVAL_DEITY.update({
    date(2026, 10, 20): ("durga", "విజయదశమి", "विजयादशमी (दशहरा)"),
    date(2026, 11, 8): ("lakshmi", "దీపావళి", "दीपावली"),
    date(2026, 11, 10): ("shiva", "కార్తీక మాసం ప్రారంభం", "कार्तिक मास आरंभ"),
    date(2026, 11, 16): ("shiva", "కార్తీక సోమవారం", "कार्तिक सोमवार"),
    date(2026, 11, 23): ("shiva", "కార్తీక సోమవారం", "कार्तिक सोमवार"),
    date(2026, 11, 24): ("shiva", "కార్తీక పౌర్ణమి", "कार्तिक पूर्णिमा"),
    date(2026, 11, 30): ("shiva", "కార్తీక సోమవారం", "कार्तिक सोमवार"),
    date(2026, 12, 7): ("shiva", "కార్తీక సోమవారం", "कार्तिक सोमवार"),
    date(2026, 12, 8): ("shiva", "కార్తీక మాసం ముగింపు", "कार्तिक मास समाप्ति"),
})

TITHI_NAME = {  # tithi key -> (te, hi)
    "pratipada": ("పాడ్యమి", "प्रतिपदा"), "dwitiya": ("విదియ", "द्वितीया"), "tritiya": ("తదియ", "तृतीया"),
    "chaturthi": ("చవితి", "चतुर्थी"), "panchami": ("పంచమి", "पंचमी"), "shashthi": ("షష్ఠి", "षष्ठी"),
    "saptami": ("సప్తమి", "सप्तमी"), "ashtami": ("అష్టమి", "अष्टमी"), "navami": ("నవమి", "नवमी"),
    "dashami": ("దశమి", "दशमी"), "ekadashi": ("ఏకాదశి", "एकादशी"), "dwadashi": ("ద్వాదశి", "द्वादशी"),
    "trayodashi": ("త్రయోదశి", "त्रयोदशी"), "chaturdashi": ("చతుర్దశి", "चतुर्दशी"),
    "purnima": ("పౌర్ణమి", "पूर्णिमा"), "amavasya": ("అమావాస్య", "अमावस्या"),
}
PAKSHA = {"shukla": ("శుక్ల", "शुक्ल"), "krishna": ("కృష్ణ", "कृष्ण")}
WEEKDAY_NAME = [("సోమవారం", "सोमवार"), ("మంగళవారం", "मंगलवार"), ("బుధవారం", "बुधवार"), ("గురువారం", "गुरुवार"),
                ("శుక్రవారం", "शुक्रवार"), ("శనివారం", "शनिवार"), ("ఆదివారం", "रविवार")]
MONTH_NAME = [("జనవరి", "जनवरी"), ("ఫిబ్రవరి", "फ़रवरी"), ("మార్చి", "मार्च"), ("ఏప్రిల్", "अप्रैल"), ("మే", "मई"),
              ("జూన్", "जून"), ("జూలై", "जुलाई"), ("ఆగస్టు", "अगस्त"), ("సెప్టెంబర్", "सितंबर"), ("అక్టోబర్", "अक्टूबर"),
              ("నవంబర్", "नवंबर"), ("డిసెంబర్", "दिसंबर")]

# channel key -> (lang, token_file, expected_channel, watermark, state slot)
CHANNELS: dict[str, dict[str, str]] = {
    "mahanavi": dict(lang="te", token_file="youtube_token.json", expected=f"{A_SHORT}", watermark=f"{A_HANDLE}"),
    "mantra_sangam": dict(lang="hi", token_file="youtube_token_mantra_sangam.json", expected=f"{B_SHORT}", watermark=f"{B_HANDLE}"),
    "trance_beats": dict(lang="hi", token_file="youtube_token_trance_beats.json", expected=C_SHORT.split()[0], watermark=f"{C_HANDLE}"),
}
_TRANCE_FOOTER = (f"🎬 और भक्ति Shorts देखें: https://www.youtube.com/{C_HANDLE}/shorts\n\n"
                  f"{C_NAME} - हिंदी भक्ति मंत्र, भजन और कीर्तन। सनातन धर्म को सबके करीब लाना हमारा उद्देश्य है।")


def split_tithi(tithi: str) -> tuple[str, str]:
    """"Shukla Chaturthi" -> ("shukla", "chaturthi"); tolerant of spelling variants."""
    low = tithi.lower().replace("shashti", "shashthi").replace("poornima", "purnima").replace("pournami", "purnima")
    paksha = "krishna" if "krishna" in low or "bahula" in low else "shukla"
    for key in TITHI_NAME:
        if key in low:
            return paksha, key
    return paksha, ""


def pick(d: date, tithi: str) -> tuple[Deity, str, str]:
    """-> (deity, reason_te, reason_hi). Festival beats tithi beats weekday."""
    if d in FESTIVAL_DEITY:
        key, te, hi = FESTIVAL_DEITY[d]
        return DEITIES[key], te, hi
    paksha, t = split_tithi(tithi)
    wd = d.weekday()
    if t == "amavasya" and wd == 5:  # Shani Amavasya
        return DEITIES["shani"], "శని అమావాస్య", "शनि अमावस्या"
    if t in TITHI_DEITY:
        key = TITHI_DEITY[t][0 if paksha == "shukla" else 1]
        return DEITIES[key], f"{PAKSHA[paksha][0]} {TITHI_NAME[t][0]}", f"{PAKSHA[paksha][1]} {TITHI_NAME[t][1]}"
    return DEITIES[WEEKDAY[wd]], WEEKDAY_NAME[wd][0], WEEKDAY_NAME[wd][1]


def build(channel: str, d: date, tithi: str) -> RequestShort:
    cfg = CHANNELS[channel]
    hi = cfg["lang"] == "hi"
    dei, why_te, why_hi = pick(d, tithi)
    paksha, t = split_tithi(tithi)
    i = 1 if hi else 0
    name = dei.hi if hi else dei.te
    mantra = dei.mantra_hi if hi else dei.mantra_te
    why = why_hi if hi else why_te
    gain = dei.gain_hi if hi else dei.gain_te
    kind = ("बीज मंत्र" if dei.beej else "मूल मंत्र") if hi else ("బీజ మంత్రం" if dei.beej else "మూల మంత్రం")
    kind_en = "Beej" if dei.beej else "Moola"
    date_line = f"{WEEKDAY_NAME[d.weekday()][i]} · {d.day} {MONTH_NAME[d.month - 1][i]} {d.year}"
    tithi_line = (f"{PAKSHA[paksha][i]} {TITHI_NAME[t][i]}" if t else "")
    count = "108 बार जपें (कम से कम 11 बार)" if hi else "108 సార్లు జపించండి (కనీసం 11 సార్లు)"
    if hi:
        title = f"{name} {kind} | {why} {d.day} {MONTH_NAME[d.month - 1][1]} | Beej Mantra"
        ctas = ("इस वीडियो पर अपनी राय कमेंट करें", "रोज़ सुबह 6 बजे नया मंत्र - सब्सक्राइब करें")
        footer_line = "रोज़ सुबह 6 बजे नया मंत्र · सब्सक्राइब करें"
    else:
        title = f"{name} {kind} | {why} {d.day} {MONTH_NAME[d.month - 1][0]} | Beeja Mantra"
        ctas = ("ఈ వీడియోపై మీ అభిప్రాయాన్ని కామెంట్ చేయండి", "ప్రతి రోజూ ఉదయం 6 గంటలకు కొత్త మంత్రం - సబ్‌స్క్రైబ్ చేయండి")
        footer_line = "ప్రతి రోజూ ఉదయం 6 గంటలకు కొత్త మంత్రం · సబ్‌స్క్రైబ్"
    if len(title) > 100:
        title = title[:99] + "…"
    desc_head = (f"🙏 {date_line}\n{why}" + (f" ({tithi_line})" if tithi_line and tithi_line not in why else "") +
                 f"\n\n{name} {kind}: {mantra}\n{dei.translit}\n\n{gain}\n{count}")
    desc_en = (f"{dei.key.title()} {kind_en} mantra for {d.day} {d.strftime('%B %Y')}: {dei.translit}\n"
               f"Chant 108 times (at least 11) with a calm mind. Chosen by today's festival / tithi / weekday.")
    base_tags = [f"{dei.key} mantra", f"{dei.key} beej mantra", f"{dei.key} beeja mantra", "beej mantra", "beeja mantra",
                 "daily mantra", "today mantra", dei.translit.lower(), name, f"{name} {kind}", "shorts"]
    if hi:
        base_tags += ["hindi mantra", "बीज मंत्र", "आज का मंत्र", "सनातन धर्म"]
        tags_ch = {"mantra_sangam": f"{B_NAME.lower()}", "trance_beats": f"{C_NAME.lower()}"}[channel]
        footer = _HI_FOOTER if channel == "mantra_sangam" else _TRANCE_FOOTER
        footer_en = (f"{B_NAME} is a Hindi devotional channel: daily Rahu Kaal, Shubh Muhurat, mantras and Purana stories."
                     if channel == "mantra_sangam" else f"{C_NAME}: Hindi devotional mantras, bhajans and kirtan.")
    else:
        base_tags += ["telugu mantra", "బీజ మంత్రం", "నేటి మంత్రం", "telugu devotional"]
        tags_ch = f"{A_NAME.lower()}"
        footer, footer_en = _CHANNEL_FOOTER_TE, _CHANNEL_FOOTER_EN
    tags = base_tags + [tags_ch]
    while len(", ".join(tags)) > 480:
        tags.pop(-2)
    hashtags = ["#Shorts", "#BeejMantra" if dei.beej else "#Mantra", f"#{dei.key.title()}", "#DailyMantra", "#Devotional"]
    bg_top, bg_mid, bg_bottom, glow = dei.palette
    return RequestShort(
        slug=f"beej_{channel}_{d.isoformat()}", handle="", comment_id="", deity_te=name,
        bg_top=bg_top, bg_mid=bg_mid, bg_bottom=bg_bottom, glow=glow,
        slides=(  # ONE card, 12 s: date + tithi on top, then the mantra, transliteration and count
            Slide("mantra", 12.0, f"{name} {kind}", mantra, dei.translit, count),
        ),
        title=title, title_en=f"{dei.key.title()} {kind_en} Mantra - {d.strftime('%d %b %Y')} | Chant 108 Times",
        description_te=desc_head, description_en=desc_en, hashtags=hashtags, tags=tags,
        lang=cfg["lang"], token_file=cfg["token_file"], expected_channel=cfg["expected"], watermark=cfg["watermark"],
        header=f"{date_line} · {tithi_line if why == WEEKDAY_NAME[d.weekday()][i] else why}", tag_footer=footer_line, cta_lines=ctas, footer_main=footer, footer_en=footer_en,
    )
