"""Languages, niches, labels, playlists text and render config for the trending-news Shorts channel.

One channel, six languages, seven niches. Each (niche, language) pair has its own playlist. Everything on the card is
text over a niche-coloured gradient with the channel's own approved music, under 5 seconds."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent
FONTS = REPO_ROOT / "channels/engine/assets/fonts"

BRAND = "Pulse Boosting"
HANDLE = "@PulseBoosting"
LANGS = ["te", "hi", "en", "ta", "kn", "ml"]          # rotation order
NICHES = ["breaking", "sports", "cinema", "technology", "business", "health", "viral"]

LANG_EN = {"te": "Telugu", "hi": "Hindi", "en": "English", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
LANG_NATIVE = {"te": "తెలుగు", "hi": "हिन्दी", "en": "English", "ta": "தமிழ்", "kn": "ಕನ್ನಡ", "ml": "മലയാളം"}
NICHE_EN = {"breaking": "Breaking News", "sports": "Sports", "cinema": "Cinema", "technology": "Technology",
            "business": "Business", "health": "Health", "viral": "Viral"}
NICHE_TAG = {"breaking": "BreakingNews", "sports": "SportsNews", "cinema": "CinemaNews", "technology": "TechNews",
             "business": "BusinessNews", "health": "HealthNews", "viral": "Viral"}
NICHE_NATIVE = {
    "te": ["బ్రేకింగ్ న్యూస్", "క్రీడలు", "సినిమా", "టెక్నాలజీ", "వ్యాపారం", "ఆరోగ్యం", "వైరల్"],
    "hi": ["ब्रेकिंग न्यूज़", "खेल", "सिनेमा", "टेक्नोलॉजी", "कारोबार", "स्वास्थ्य", "वायरल"],
    "en": list(NICHE_EN.values()),
    "ta": ["முக்கிய செய்திகள்", "விளையாட்டு", "சினிமா", "தொழில்நுட்பம்", "வணிகம்", "ஆரோக்கியம்", "வைரல்"],
    "kn": ["ಬ್ರೇಕಿಂಗ್ ನ್ಯೂಸ್", "ಕ್ರೀಡೆ", "ಸಿನಿಮಾ", "ತಂತ್ರಜ್ಞಾನ", "ವ್ಯಾಪಾರ", "ಆರೋಗ್ಯ", "ವೈರಲ್"],
    "ml": ["ബ്രേക്കിംഗ് ന്യൂസ്", "കായികം", "സിനിമ", "സാങ്കേതികവിദ്യ", "ബിസിനസ്", "ആരോഗ്യം", "വൈറൽ"],
}
LANG_TAG = {"te": "TeluguNews", "hi": "HindiNews", "en": "IndiaNews", "ta": "TamilNews", "kn": "KannadaNews",
            "ml": "MalayalamNews"}
# (subscribe line, comment-your-opinion line), drawn under the headline
CTA = {
    "te": ("ప్రతి 6 గంటలకు తాజా వార్తలు. సబ్‌స్క్రైబ్ చేయండి", "ఈ వార్తపై మీ అభిప్రాయం కామెంట్ చేయండి"),
    "hi": ("हर 6 घंटे में ताज़ा खबरें। सब्सक्राइब करें", "इस खबर पर अपनी राय कमेंट करें"),
    "en": ("Fresh trending news every 6 hours. Subscribe", "Comment your opinion on this news"),
    "ta": ("ஒவ்வொரு 6 மணி நேரமும் புதிய செய்திகள். சப்ஸ்க்ரைப் செய்யுங்கள்", "இந்த செய்தி குறித்து உங்கள் கருத்தைப் பதிவிடுங்கள்"),
    "kn": ("ಪ್ರತಿ 6 ಗಂಟೆಗೆ ಹೊಸ ಸುದ್ದಿ. ಸಬ್‌ಸ್ಕ್ರೈಬ್ ಮಾಡಿ", "ಈ ಸುದ್ದಿಯ ಬಗ್ಗೆ ನಿಮ್ಮ ಅಭಿಪ್ರಾಯ ಕಾಮೆಂಟ್ ಮಾಡಿ"),
    "ml": ("ഓരോ 6 മണിക്കൂറിലും പുതിയ വാർത്തകൾ. സബ്‌സ്ക്രൈബ് ചെയ്യൂ", "ഈ വാർത്തയെക്കുറിച്ച് നിങ്ങളുടെ അഭിപ്രായം കമന്റ് ചെയ്യൂ"),
}
INTRO = {  # one line about the channel in the viewer's language
    "te": "తాజా ట్రెండింగ్ వార్తలు, ప్రతి 6 గంటలకు ఒక షార్ట్.",
    "hi": "ताज़ा ट्रेंडिंग खबरें, हर 6 घंटे में एक शॉर्ट।",
    "en": "The latest trending news, one Short every 6 hours.",
    "ta": "சமீபத்திய டிரெண்டிங் செய்திகள், ஒவ்வொரு 6 மணி நேரமும் ஒரு ஷார்ட்.",
    "kn": "ತಾಜಾ ಟ್ರೆಂಡಿಂಗ್ ಸುದ್ದಿ, ಪ್ರತಿ 6 ಗಂಟೆಗೆ ಒಂದು ಶಾರ್ಟ್.",
    "ml": "പുതിയ ട്രെൻഡിംഗ് വാർത്തകൾ, ഓരോ 6 മണിക്കൂറിലും ഒരു ഷോർട്ട്.",
}

# (window start hour IST, slot id): one post per slot, a random minute inside the first 40 minutes
SLOTS = [(5, "t1"), (11, "t2"), (17, "t3"), (23, "t4")]
WINDOW_MINUTES = 40

WHITE, GOLD, SOFT = (255, 255, 255), (255, 210, 120), (225, 220, 225)
PALETTES = {
    "breaking": ((30, 8, 8), (130, 26, 24)), "sports": ((6, 28, 16), (18, 104, 62)),
    "cinema": ((24, 8, 38), (104, 34, 124)), "technology": ((8, 16, 38), (24, 74, 150)),
    "business": ((32, 22, 6), (126, 88, 14)), "health": ((6, 30, 32), (14, 104, 108)),
    "viral": ((38, 8, 26), (156, 40, 74)),
}
ACCENT = {"breaking": (255, 150, 130), "sports": (150, 255, 190), "cinema": (240, 180, 255),
          "technology": (150, 200, 255), "business": (255, 215, 120), "health": (150, 245, 240),
          "viral": (255, 170, 200)}


def _fonts(lang: str):
    """(font for all text, native-script font to mix in or ''). Hind covers Devanagari and Latin; the Noto Tamil,
    Kannada and Malayalam fonts also carry Latin, digits and punctuation, so they need no mixing. Telugu keeps
    plain Ponnala for Telugu characters (standing rule) over a Latin-capable Noto font."""
    latin = REPO_ROOT / "assets/fonts/NotoSansTelugu-Variable.ttf"
    if lang == "hi":
        return FONTS / "Hind-Bold.ttf", ""
    if lang == "en":
        return latin, ""
    if lang == "te":
        return latin, str(REPO_ROOT / "assets/fonts/Ponnala-Regular.ttf")
    return {"ta": FONTS / "NotoSansTamil.ttf", "kn": FONTS / "NotoSansKannada.ttf",
            "ml": FONTS / "NotoSansMalayalam.ttf"}[lang], ""


def render_cfg(lang: str, niche: str) -> ChannelConfig:
    main, native = _fonts(lang)
    label_font = FONTS / "Hind-Bold.ttf" if lang == "hi" else main
    accent = ACCENT[niche]
    layouts = [dict(anchor=a, primary=p, secondary=SOFT, accent=accent, ornament=o)
               for a, p, o in ((0.46, WHITE, True), (0.42, GOLD, False), (0.50, (255, 246, 240), True))]
    return ChannelConfig(
        channel_name=BRAND,
        assets_dir=CHANNEL_DIR / "assets",
        blocks=[TextBlock(field="label", font=label_font, size=44, color_key="accent", bold=True),
                TextBlock(field="text_primary", font=main, size=92, color_key="primary", bold=True),
                TextBlock(field="text_secondary", font=main, size=44, color_key="secondary", bold=False)],
        font_channel_label=main,
        telugu_font=native,
        music_glob="music/approved/*.mp3",
        music_rotate=True,
        logo_path=str(CHANNEL_DIR / "assets/logo.png"),
        watermark_handle=HANDLE,
        safe_bottom=1385,
        text_max_w=780,
        text_anchor=0.46,
        cta_text="\n".join(CTA[lang]),
        cta_size=38,
        layouts=layouts,
        palettes=[PALETTES[niche]],
    )


def niche_label(lang: str, niche: str) -> str:
    return NICHE_NATIVE[lang][NICHES.index(niche)]


def plan(seq: int) -> tuple[str, str]:
    """(language, niche) for the seq-th post. 6 and 7 are coprime, so every pair comes up once in 42 posts."""
    return LANGS[seq % len(LANGS)], NICHES[seq % len(NICHES)]


def playlist_for(lang: str, niche: str) -> tuple[str, str]:
    nat, en, ln = niche_label(lang, niche), NICHE_EN[niche], LANG_NATIVE[lang]
    title = f"{en} | {nat} ({LANG_EN[lang]}) - {BRAND}"[:150]
    desc = (f"{INTRO[lang]}\n\nTrending {en.lower()} news in {LANG_EN[lang]} ({ln}), one Short every 6 hours. "
            f"Every Short names its source and links the original story. Subscribe to {BRAND} for fresh "
            f"{en.lower()} updates in Telugu, Hindi, English, Tamil, Kannada and Malayalam.\n\n"
            f"#{NICHE_TAG[niche]} #{LANG_TAG[lang]} #Trending #Shorts #PulseBoosting")
    return title, desc
