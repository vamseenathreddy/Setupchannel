"""Render/pick configuration for Jesus Worship Waves.

English is drawn FIRST/top (text_primary), Telugu below (text_secondary) -- explicitly the
REVERSE of every other channel in this repo ("jesus channnel is first english and below
telugu text"). A soft sky-blue/white/gold palette distinguishes this channel visually from
the saffron/gold Hindu-devotional channels (mahanavi spirituals, Ramana Maharshi TV, Divine
Mantra Sangam, Devotional Trance Beats) sharing this repo.
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_EN_BOLD = REPO_ROOT / "ramana/assets/fonts/Poppins-Bold.ttf"
FONT_EN_LIGHT = REPO_ROOT / "ramana/assets/fonts/Poppins-Regular.ttf"
FONT_TE = REPO_ROOT / "assets/fonts/Ponnala-Regular.ttf"  # Ponnala has no quote-mark glyphs -- see strip_chars below

SKY, GOLDLT, WHITE, SOFT = (190, 220, 255), (255, 214, 140), (255, 255, 255), (205, 215, 230)

LAYOUTS = [
    dict(anchor=0.50, primary=WHITE, secondary=SKY, accent=GOLDLT, ornament=True),
    dict(anchor=0.42, primary=GOLDLT, secondary=WHITE, accent=SKY, ornament=False),
    dict(anchor=0.55, primary=(255, 250, 240), secondary=SOFT, accent=GOLDLT, ornament=True),
    dict(anchor=0.47, primary=WHITE, secondary=(210, 230, 255), accent=GOLDLT, ornament=False),
]
PALETTES = [  # fallback gradients (no real photos yet) -- soft heavenly blues, not the usual indigo/teal set
    ((18, 28, 56), (58, 90, 150)),
    ((10, 24, 44), (40, 76, 120)),
    ((20, 20, 48), (70, 70, 140)),
    ((14, 22, 40), (50, 86, 130)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Jesus Worship Waves",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_EN_BOLD, size=84, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_TE, size=130, color_key="secondary", bold=True,
                  strip_chars="'\"‘’“”`"),
    ],
    font_channel_label=FONT_EN_LIGHT,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)

# Mon=0..Sun=6. verse/teaching/praise rotate through the week; Sunday (worship day) gets praise.
ROTATION = {0: "verse", 1: "teaching", 2: "verse", 3: "teaching", 4: "verse", 5: "praise", 6: "praise"}
