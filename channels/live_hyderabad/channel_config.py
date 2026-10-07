"""Render/pick configuration for Live Hyderabad -- Pattern B (one real trending Hyderabad-city
headline/day, see channels/engine/trending.py). Uses NotoSansTelugu (same choice as Pulse
Boosting/Tollywood News -- headlines can come back in English or Telugu and Ponnala has no
Latin glyphs at all).
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_MAIN = REPO_ROOT / "assets/fonts/NotoSansTelugu-Variable.ttf"

CYAN, BLUE, WHITE, SKY = (120, 220, 230), (130, 180, 255), (255, 255, 255), (210, 235, 250)

LAYOUTS = [
    dict(anchor=0.46, primary=WHITE, secondary=CYAN, accent=BLUE, ornament=True),
    dict(anchor=0.40, primary=CYAN, secondary=WHITE, accent=BLUE, ornament=False),
    dict(anchor=0.50, primary=SKY, secondary=BLUE, accent=CYAN, ornament=True),
    dict(anchor=0.44, primary=BLUE, secondary=WHITE, accent=CYAN, ornament=False),
]
PALETTES = [  # cool cyan/blue "city skyline at night" tones, distinct from the other two Pattern-B channels
    ((6, 14, 22), (10, 46, 70)),
    ((8, 16, 20), (14, 50, 60)),
    ((6, 12, 24), (12, 40, 80)),
    ((4, 16, 18), (8, 54, 66)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Live Hyderabad",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_MAIN, size=90, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_MAIN, size=48, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_MAIN,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)
