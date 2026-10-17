"""Languages, niches, labels, playlists text and render config for the trending-news Shorts channel.

One channel, six languages, seven niches. Each (niche, language) pair has its own playlist. Everything on the card is
text over a niche-coloured gradient with the channel's own approved music, under 5 seconds."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock
from channels.trending import portraits

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent
FONTS = REPO_ROOT / "channels/engine/assets/fonts"

BRAND = "Pulse Boosting"
HANDLE = "@PulseBoosting"
LANGS = ["te"]          # 2026-10-17: Telugu only (TDP-supportive channel)
NICHES = ["chandrababu", "lokesh", "tdp", "nda", "development", "innovations"]

LANG_EN = {"te": "Telugu", "hi": "Hindi", "en": "English", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam"}
LANG_NATIVE = {"te": "తెలుగు", "hi": "हिन्दी", "en": "English", "ta": "தமிழ்", "kn": "ಕನ್ನಡ", "ml": "മലയാളം"}
NICHE_EN = {"chandrababu": "Chandrababu Naidu", "lokesh": "Nara Lokesh", "tdp": "Telugu Desam Party",
            "nda": "NDA Alliance", "development": "AP Development", "innovations": "CM Innovations"}
NICHE_TAG = {"chandrababu": "ChandrababuNaidu", "lokesh": "NaraLokesh", "tdp": "TDP", "nda": "NDAAlliance",
             "development": "APDevelopment", "innovations": "Innovations"}
NICHE_NATIVE = {
    "te": ["చంద్రబాబు", "నారా లోకేశ్", "తెలుగుదేశం", "కూటమి", "అభివృద్ధి", "ఆవిష్కరణలు"],
    "en": list(NICHE_EN.values()),
}
LANG_TAG = {"te": "TeluguNews", "en": "IndiaNews"}
# Join links for the community channels. Fill in when the user creates them; empty = line omitted.
WHATSAPP_URL = ""
TELEGRAM_URL = ""
# (subscribe line, join-groups line, comment line), drawn under the headline
CTA = {
    "te": ("రాష్ట్ర ప్రజలారా, మీ ప్రభుత్వం గురించి తెలుసుకోవడానికి ఇప్పుడే సబ్‌స్క్రైబ్ చేయండి", "వాట్సాప్, టెలిగ్రామ్ గ్రూపుల్లో చేరండి",
           "ఈ వార్తపై మీ అభిప్రాయం కామెంట్ చేయండి"),
    "en": ("12 Telugu updates daily. Subscribe", "Join our WhatsApp and Telegram groups",
           "Comment your opinion on this news"),
}
INTRO = {
    "te": "తెలుగుదేశం, చంద్రబాబు, లోకేశ్ గారి పాలన, అభివృద్ధిపై వార్తలు. రోజుకు 12 షార్ట్స్.",
    "en": "News on TDP, Chandrababu Naidu, Nara Lokesh and Andhra Pradesh development. 12 Shorts a day.",
}

# (window start hour IST, slot id): one post every 2 hours from midnight, at a random minute inside the first
# 40 minutes of its window. The language rotates each post, so the first six posts (00:00 to 10:00) cover all six.
SLOTS = [(2 * i, f"t{i + 1}") for i in range(12)]
WINDOW_MINUTES = 40

WHITE, GOLD, SOFT = (255, 255, 255), (255, 210, 120), (225, 220, 225)
INK, RED, BROWN = (28, 8, 0), (150, 10, 20), (70, 30, 0)   # dark text on the TDP-yellow cards
_YELLOW = ((255, 222, 20), (250, 190, 0))
PALETTES = {k: _YELLOW for k in NICHES}
ACCENT = {k: RED for k in NICHES}


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
    raise ValueError(f"unsupported language {lang}")


def render_cfg(lang: str, niche: str) -> ChannelConfig:
    main, native = _fonts(lang)
    label_font = FONTS / "Hind-Bold.ttf" if lang == "hi" else main
    accent = ACCENT[niche]
    layouts = [dict(anchor=a, primary=p, secondary=BROWN, accent=accent, ornament=o)
               for a, p, o in ((0.44, INK, True), (0.42, (90, 0, 10), False), (0.46, INK, True))]
    return ChannelConfig(
        channel_name=BRAND,
        assets_dir=CHANNEL_DIR / "assets",
        # 2026-10-17: no "TRENDING #n" label on the Short (rank and niche live in the description); bigger text,
        # more reading matter (summary + up to four related headlines) filling the space the label and big logo used.
        blocks=[TextBlock(field="text_primary", font=main, size=104, color_key="primary", bold=True),
                TextBlock(field="text_summary", font=main, size=84, color_key="secondary", bold=False),
                TextBlock(field="text_related", font=main, size=76, color_key="secondary", bold=False)],
        corner_field="text_secondary",
        bg_overlay=portraits.make_overlay(str(main)),
        text_shadow=False,
        scrim=False,
        font_channel_label=main,
        telugu_font=native,
        music_glob="music/approved/*.mp3",
        music_rotate=True,
        logo_path=str(CHANNEL_DIR / "assets/logo.png"),
        watermark_handle=HANDLE,
        safe_bottom=1340,
        text_max_w=780,
        text_anchor=0.46,
        cta_text=CTA[lang][0],  # subscribe line only (no join-groups line on the card)
        cta_size=40,
        logo_width=170,
        logo_y=235,
        safe_top=350,
        layouts=layouts,
        palettes=[PALETTES[niche]],
    )


def niche_label(lang: str, niche: str) -> str:
    return NICHE_NATIVE[lang][NICHES.index(niche)]


def plan(seq: int) -> tuple[str, str]:
    """(language, niche) for the seq-th post: Telugu always, niches in rotation."""
    return LANGS[0], NICHES[seq % len(NICHES)]


def playlist_for(lang: str, niche: str) -> tuple[str, str]:
    nat, en = niche_label(lang, niche), NICHE_EN[niche]
    title = f"{en} | {nat} (Telugu) - {BRAND}"[:150]
    desc = (f"{INTRO[lang]}\n\nSourced coverage of {en} in Telugu. Every Short names its source and links "
            f"the original story. Subscribe to {BRAND}.\n\n"
            f"#{NICHE_TAG[niche]} #{LANG_TAG[lang]} #TDP #Shorts #PulseBoosting")
    return title, desc
