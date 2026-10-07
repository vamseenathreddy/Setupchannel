"""Render configuration for Jesus Worship Waves -- TWO Shorts a day, nothing else
(2026-10-07 request):

  * MORNING  "Bible Quote": the verse in English and Telugu at the SAME font size, with its
    reference, then one line each (English / Telugu) on how it applies to our life.
  * EVENING  "Bible Quiz": the SAME verse from the morning (no reference) with a
    which-book-and-chapter question, four options, and an invitation to answer in comments.

English is drawn FIRST/top, Telugu below (explicit earlier request for this channel). The
look (soft sky-blue/white/gold) stays distinct from the saffron Hindu-devotional channels.

BGM: only clips the owner has listened to and approved are ever used -- they live in
assets/music/approved/ (see scripts/dev/slice_bgm.py). With no approved clip the pipeline
posts nothing.
"""
from pathlib import Path

from channels.engine.render import ChannelConfig, TextBlock

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANNEL_DIR = Path(__file__).resolve().parent

FONT_EN_BOLD = REPO_ROOT / "ramana/assets/fonts/Poppins-Bold.ttf"
FONT_EN_LIGHT = REPO_ROOT / "ramana/assets/fonts/Poppins-Regular.ttf"
FONT_TE = REPO_ROOT / "assets/fonts/Ponnala-Regular.ttf"  # Ponnala has no quote-mark glyphs -- see strip_chars below

SKY, GOLDLT, WHITE, SOFT = (190, 220, 255), (255, 214, 140), (255, 255, 255), (205, 215, 230)
QUOTES = "'\"‘’“”`"

LAYOUTS = [
    dict(anchor=0.50, primary=WHITE, secondary=SKY, accent=GOLDLT, ornament=True),
    dict(anchor=0.50, primary=GOLDLT, secondary=WHITE, accent=SKY, ornament=False),
    dict(anchor=0.50, primary=(255, 250, 240), secondary=SOFT, accent=GOLDLT, ornament=True),
    dict(anchor=0.50, primary=WHITE, secondary=(210, 230, 255), accent=GOLDLT, ornament=False),
]
PALETTES = [  # fallback gradients (no real photos yet) -- soft heavenly blues
    ((18, 28, 56), (58, 90, 150)),
    ((10, 24, 44), (40, 76, 120)),
    ((20, 20, 48), (70, 70, 140)),
    ((14, 22, 40), (50, 86, 130)),
]

SHORT_SECONDS = 5.0    # every Short is 5 seconds (owner request); BGM clips are cut to this length
VERSE_SIZE = 70        # English and Telugu verse use the SAME size
APPLY_SIZE = 44

_COMMON = dict(
    assets_dir=CHANNEL_DIR / "assets",
    font_channel_label=FONT_EN_LIGHT,
    music_glob="music/approved/*.mp3",
    music_rotate=True,  # cycle the approved clips in order, one per Short (quote and quiz never share a clip)
    layouts=LAYOUTS,
    palettes=PALETTES,
    watermark_handle="@Jesusworshipwaves",
    photo_text_h=860,       # text-heavy cards: give the text most of the lower photo
    photo_text_bottom=1385, # stay above the Shorts title/channel/Subscribe row (starts ~y1430)
    safe_bottom=1385,
    text_max_w=780,         # x 150..930: clear of the Like/Comment/Save/Share buttons (x>940)
    photo_shade_from=560,
)

QUOTE_CFG = ChannelConfig(
    channel_name="Jesus Worship Waves",
    blocks=[
        TextBlock(field="text_primary", font=FONT_EN_BOLD, size=VERSE_SIZE, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_TE, size=VERSE_SIZE, color_key="secondary", bold=False,
                  strip_chars=QUOTES),
        TextBlock(field="apply_en", font=FONT_EN_LIGHT, size=APPLY_SIZE, color_key="accent", bold=False),
        TextBlock(field="apply_te", font=FONT_TE, size=APPLY_SIZE, color_key="accent", bold=False,
                  strip_chars=QUOTES),
        TextBlock(field="sub_en", font=FONT_EN_LIGHT, size=38, color_key="secondary", bold=False),
        TextBlock(field="sub_te", font=FONT_TE, size=40, color_key="secondary", bold=False),
    ],
    music_offset=0,
    **_COMMON,
)

QUIZ_CFG = ChannelConfig(
    channel_name="Jesus Worship Waves",
    blocks=[
        TextBlock(field="quiz_label", font=FONT_EN_BOLD, size=48, color_key="accent", bold=True),
        TextBlock(field="text_primary", font=FONT_EN_BOLD, size=58, color_key="primary", bold=True),
        TextBlock(field="text_secondary", font=FONT_TE, size=58, color_key="secondary", bold=False,
                  strip_chars=QUOTES),
        TextBlock(field="question_en", font=FONT_EN_BOLD, size=46, color_key="accent", bold=True),
        TextBlock(field="question_te", font=FONT_TE, size=46, color_key="accent", bold=False),
        TextBlock(field="opts_ab", font=FONT_EN_BOLD, size=50, color_key="primary", bold=True),
        TextBlock(field="opts_cd", font=FONT_EN_BOLD, size=50, color_key="primary", bold=True),
        TextBlock(field="sub_en", font=FONT_EN_LIGHT, size=38, color_key="accent", bold=False),
        TextBlock(field="sub_te", font=FONT_TE, size=40, color_key="accent", bold=False),
    ],
    music_offset=1,
    **_COMMON,
)

# Kept for modules that still import the old name.
RENDER_CFG = QUOTE_CFG
