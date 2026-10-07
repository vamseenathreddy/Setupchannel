"""Render/pick configuration for Pulse Boosting -- Pattern B (one real trending India
headline/day, see channels/engine/trending.py). Uses NotoSansTelugu (already in this repo,
see src/mahanavi/config.py's telugu_font_path comment) as the single text font because it
covers BOTH Telugu and Latin cleanly -- headlines from Google News can come back in either
script and this repo's other Telugu-only display font (Ponnala) has no Latin glyphs at all
(confirmed by a render test: English text came out as blank tofu boxes).
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_MAIN = REPO_ROOT / "assets/fonts/NotoSansTelugu-Variable.ttf"

RED, GOLD, WHITE, SOFT = (255, 150, 130), (255, 200, 120), (255, 255, 255), (220, 210, 210)

LAYOUTS = [
    dict(anchor=0.46, primary=WHITE, secondary=GOLD, accent=RED, ornament=True),
    dict(anchor=0.40, primary=GOLD, secondary=WHITE, accent=RED, ornament=False),
    dict(anchor=0.50, primary=(255, 245, 240), secondary=SOFT, accent=RED, ornament=True),
    dict(anchor=0.44, primary=RED, secondary=WHITE, accent=GOLD, ornament=False),
]
PALETTES = [  # energetic red/orange "breaking news" tones, distinct from the devotional channels
    ((30, 10, 10), (110, 30, 20)),
    ((26, 14, 6), (100, 46, 10)),
    ((24, 8, 14), (90, 24, 40)),
    ((28, 12, 8), (104, 38, 16)),
]

RENDER_CFG = ChannelConfig(
    channel_name="Pulse Boosting",
    assets_dir=CHANNEL_DIR / "assets",
    blocks=[
        TextBlock(field="text_primary", font=FONT_MAIN, size=92, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_MAIN, size=48, color_key="secondary", bold=False),
    ],
    font_channel_label=FONT_MAIN,
    music_glob="music/*.mp3",
    layouts=LAYOUTS,
    palettes=PALETTES,
)
