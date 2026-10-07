"""Render/pick configuration for Devotional Trance Beats -- the second Hindi-only devotional
channel in this repo ("also same hindi version of mahanavi spirituals"). Content leans
Krishna/Radha bhajan-kirtan (vs Divine Mantra Sangam's Shiva/Om-mantra-chanting focus) so the
two channels don't look like duplicates of each other. Hind Bold is a cleaner, more
contemporary Devanagari display font than Divine Mantra Sangam's ornate Yatra One, matching
this channel's more modern "beats" branding; a magenta/violet "trance" palette distinguishes
it from Divine Mantra Sangam's warm gold.
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_HI = REPO_ROOT / "channels/engine/assets/fonts/Hind-Bold.ttf"
FONT_LABEL = REPO_ROOT / "channels/engine/assets/fonts/Hind-Regular.ttf"

PINK, GOLD, WHITE, SOFT = (255, 180, 220), (255, 200, 120), (255, 255, 255), (220, 200, 230)

LAYOUTS = [
    dict(anchor=0.50, primary=WHITE, secondary=PINK, accent=GOLD, ornament=True),
    dict(anchor=0.44, primary=GOLD, secondary=WHITE, accent=PINK, ornament=False),
    dict(anchor=0.56, primary=(255, 240, 250), secondary=SOFT, accent=GOLD, ornament=True),
    dict(anchor=0.48, primary=PINK, secondary=WHITE, accent=GOLD, ornament=False),
]
PALETTES = [  # fallback gradients -- magenta/violet "trance" tones, distinct from mantra_sangam's warm gold
    ((28, 8, 36), (96, 30, 110)),
    ((34, 6, 48), (120, 24, 130)),
    ((20, 8, 40), (80, 30, 120)),
    ((30, 10, 30), (110, 40, 100)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Devotional Trance Beats",
    watermark_handle="@DevotionalTranceBeats",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_HI, size=120, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_LABEL, size=70, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_LABEL,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)

# Mon=0..Sun=6. bhajan/kirtan/quote rotate; Janmashtami-season Wednesdays lean kirtan.
ROTATION = {0: "bhajan", 1: "kirtan", 2: "quote", 3: "bhajan", 4: "kirtan", 5: "bhajan", 6: "kirtan"}
