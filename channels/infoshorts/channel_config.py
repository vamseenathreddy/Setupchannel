"""Render/pick configuration for InfoShorts Telugu ("unknown fact in telugu"). Telugu is the
star -- drawn first/top, big and bold; a short English gloss is drawn below, smaller, for
viewers who don't read Telugu. A cool teal/violet "trivia" palette distinguishes this channel
from the warmer gold/saffron devotional channels sharing this repo.
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_TE = REPO_ROOT / "assets/fonts/Ponnala-Regular.ttf"
FONT_EN = REPO_ROOT / "ramana/assets/fonts/Poppins-Regular.ttf"
FONT_EN_LIGHT = REPO_ROOT / "ramana/assets/fonts/Poppins-Regular.ttf"

TEAL, VIOLET, WHITE, SOFT = (150, 230, 220), (220, 180, 255), (255, 255, 255), (205, 210, 220)

LAYOUTS = [
    dict(anchor=0.48, primary=WHITE, secondary=TEAL, accent=VIOLET, ornament=True),
    dict(anchor=0.42, primary=TEAL, secondary=WHITE, accent=VIOLET, ornament=False),
    dict(anchor=0.52, primary=(235, 250, 245), secondary=SOFT, accent=TEAL, ornament=True),
    dict(anchor=0.46, primary=VIOLET, secondary=WHITE, accent=TEAL, ornament=False),
]
PALETTES = [  # fallback gradients (no real photos yet) -- cool "trivia" teal/violet, not the warm devotional set
    ((8, 24, 30), (20, 70, 80)),
    ((18, 10, 36), (60, 36, 96)),
    ((6, 22, 26), (18, 60, 64)),
    ((14, 14, 30), (50, 40, 90)),
]

RENDER_CFG = ChannelConfig(
    channel_name="InfoShorts Telugu",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_TE, size=120, color_key="primary", bold=False,
                  strip_chars="'\"‘’“”`"),
        TextBlock(field="text_secondary", font=FONT_EN, size=56, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_EN_LIGHT,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)

# Mon=0..Sun=6. science/history/nature/space/india rotate through the week.
ROTATION = {0: "science", 1: "history", 2: "nature", 3: "space", 4: "india", 5: "science", 6: "nature"}
