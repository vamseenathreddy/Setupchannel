"""Render/pick configuration for Divine Mantra Sangam -- "same like mahanavi spirituals but
hindi only" -- so this reuses mahanavi's own warm gold/saffron devotional palette, but draws
ONLY Hindi text (text_secondary is left blank in every content row; the render engine skips
empty blocks automatically). Yatra One is a decorative, devotional-feeling Devanagari display
font (visually in the same spirit as Ponnala, the Telugu font the rest of this repo uses).
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_HI = REPO_ROOT / "channels/engine/assets/fonts/YatraOne-Regular.ttf"
FONT_LABEL = REPO_ROOT / "channels/engine/assets/fonts/Hind-Regular.ttf"

CREAM, GOLD, WHITE, SOFT = (255, 236, 196), (244, 190, 90), (245, 245, 245), (210, 205, 195)

LAYOUTS = [
    dict(anchor=0.50, primary=CREAM, secondary=WHITE, accent=GOLD, ornament=True),
    dict(anchor=0.44, primary=GOLD, secondary=WHITE, accent=CREAM, ornament=False),
    dict(anchor=0.56, primary=(255, 245, 225), secondary=SOFT, accent=GOLD, ornament=True),
    dict(anchor=0.48, primary=CREAM, secondary=(255, 214, 140), accent=WHITE, ornament=False),
]
PALETTES = [  # same warm devotional gradients as mahanavi/ramana -- deliberately consistent
    ((10, 16, 40), (36, 52, 104)),
    ((8, 28, 34), (22, 84, 82)),
    ((24, 12, 44), (84, 40, 112)),
    ((10, 14, 24), (46, 58, 78)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Divine Mantra Sangam",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_HI, size=130, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_LABEL, size=70, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_LABEL,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)

# Mon=0..Sun=6. mantra/quote/aarti rotate; Monday (Shiva) and Thursday get mantra emphasis via content choice.
ROTATION = {0: "mantra", 1: "quote", 2: "mantra", 3: "aarti", 4: "quote", 5: "mantra", 6: "aarti"}


# ---- Daily timing Shorts (Hindi version of Mahanavi's Rahu Kalam / Shubha Ghadiyalu / Durmuhurtham) ----
FONT_HI_BOLD = REPO_ROOT / "channels/engine/assets/fonts/Hind-Bold.ttf"
TIMING_CFG = ChannelConfig(
    channel_name="Divine Mantra Sangam",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="t_date", font=FONT_LABEL, size=48, color_key="secondary", bold=False),
        TextBlock(field="t_title", font=FONT_HI, size=116, color_key="primary", bold=True),
        TextBlock(field="t_label", font=FONT_LABEL, size=56, color_key="accent", bold=False),
        TextBlock(field="t_time", font=FONT_HI_BOLD, size=84, color_key="secondary", bold=False),
        TextBlock(field="t_place", font=FONT_LABEL, size=38, color_key="accent", bold=False),
        TextBlock(field="t_note", font=FONT_LABEL, size=50, color_key="primary", bold=False),
        TextBlock(field="t_mantra_label", font=FONT_LABEL, size=46, color_key="accent", bold=False),
        TextBlock(field="t_mantra", font=FONT_HI, size=64, color_key="primary", bold=False),
        TextBlock(field="t_other", font=FONT_LABEL, size=40, color_key="secondary", bold=False),
        TextBlock(field="t_comment", font=FONT_LABEL, size=44, color_key="primary", bold=False),
        TextBlock(field="t_sub", font=FONT_HI_BOLD, size=48, color_key="accent", bold=False),
        TextBlock(field="t_opinion", font=FONT_LABEL, size=44, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_LABEL,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
    watermark_handle="@DivineMantraSangam",
    photo_text_h=1000, photo_text_bottom=1385, safe_bottom=1385, safe_top=240, text_max_w=780,
    photo_shade_from=420, photo_shade_alpha=0.88,
)
