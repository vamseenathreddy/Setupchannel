"""Render/pick configuration for Tollywood News -- Pattern B (one real trending Telugu-film
headline/day, see channels/engine/trending.py). Uses NotoSansTelugu (same choice as Pulse
Boosting -- see that channel's channel_config.py for why: headlines can come back in English
or Telugu and Ponnala has no Latin glyphs at all).
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_MAIN = REPO_ROOT / "assets/fonts/NotoSansTelugu-Variable.ttf"   # Latin/digits
FONT_TELUGU = REPO_ROOT / "assets/fonts/Ponnala-Regular.ttf"          # every Telugu character (owner, 2026-10-07)

GOLD, MAGENTA, WHITE, CREAM = (255, 210, 110), (255, 120, 180), (255, 255, 255), (250, 235, 215)

LAYOUTS = [
    dict(anchor=0.46, primary=WHITE, secondary=GOLD, accent=MAGENTA, ornament=True),
    dict(anchor=0.40, primary=GOLD, secondary=WHITE, accent=MAGENTA, ornament=False),
    dict(anchor=0.50, primary=CREAM, secondary=MAGENTA, accent=GOLD, ornament=True),
    dict(anchor=0.44, primary=MAGENTA, secondary=WHITE, accent=GOLD, ornament=False),
]
PALETTES = [  # glamorous gold/magenta "Tollywood" tones, distinct from Pulse Boosting's red/orange
    ((24, 10, 20), (90, 20, 60)),
    ((26, 16, 6), (104, 70, 10)),
    ((22, 8, 16), (86, 22, 50)),
    ((28, 14, 6), (108, 60, 14)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Tollywood News",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_MAIN, size=90, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_MAIN, size=48, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_MAIN,
    telugu_font=str(FONT_TELUGU),
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)
