"""
PuranaShortCardRenderer: renders one "Purana Story" Short -- a single
STATIC (non-scrolling) card holding a condensed Puranic story, title,
one-line moral, and source attribution, all on one still frame.

STATIC, NOT SCROLLING, NO NARRATION (per explicit request, 2026-10-02):
"static page short with all text should adjust in same frame not
scrolling... no need of reading that text because its not hearing
natural" -- same "read it yourself" design as RashiCardRenderer, not the
scrolling-text treatment images/purana_text_renderer.py uses for the
long-form video. Short duration (video/assembler.py's loop-friendly, no-
fade settings) is intentionally shorter than a comfortable read, so
viewers loop 2-3x to finish -- same loop-bait pattern already validated
for the Rashi Mantra cards.

AUTO-FIT TEXT ("if little big adjust text", explicit request): unlike
the Rashi Mantra card's single shared font size (fit to the LONGEST
string across all 12 cards), a Purana story's length genuinely varies
story to story, and forcing one shared size would either waste space on
short stories or overflow on long ones. This renderer instead fits EACH
story's own text individually: it shrinks the story font size (and
re-wraps at each size) until the wrapped paragraph's total height fits
the available content box, stopping at a legibility floor
(STORY_MIN_FONT_FRAC). If even the floor size would overflow (meaning a
future story entry was written too long), it logs a warning rather than
silently clipping text off-frame -- the content should be shortened in
content/purana_short_stories.py instead.

BACKGROUND: a dedicated indigo-to-maroon gradient (COLOR_PURANA_TOP/
BOTTOM below), deliberately distinct from every other card family on
this channel (Rahu Kalam red, Shubha Ghadiyalu green, Durmuhurtham
amber/brown, Rashi Mantra's green muggu backgrounds) -- per the earlier,
separately-raised "cards look the same, viewers get confused" concern,
giving this series its own unmistakable visual identity on top of
already being a different content pillar.

SAFE ZONES: same validated boundaries as every other Short card on this
channel -- content centered in an 84%-width column (8% margin each
side), finishing at or above height*0.68 (YouTube's own Shorts UI
chrome -- channel handle, caption, visibility badge -- occupies roughly
the bottom 25% of a real posted Short, confirmed via screenshot).

EPISODE NUMBER (per explicit request, 2026-10-02: "i want story number
count beside purana katha - 1, 2, 3 etc... this should be endless
story posting shorts"): PuranaShortCard.episode_number is an
EVER-INCREMENTING count of posts made, tracked separately from the
0-9 content-rotation index in content/purana_short_stories.py. The
content pool will eventually repeat (10 stories, reused in rotation),
but the episode number never resets and never wraps -- so the series
reads as an endless, ongoing count ("పురాణ కథ - 47") even on a day it
happens to repost a story the audience already saw. Persisted by
scripts/post_purana_short.py as data/purana_short_episode_count.txt,
synced via Drive like every other piece of this channel's state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.purana_short_stories import PuranaShortStory
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.layout import vertical_gradient
from mahanavi.images.sri_chakra import draw_sri_chakra_roundel

logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# Deep indigo-to-maroon -- distinct from every other card family on this
# channel (see module docstring).
COLOR_PURANA_TOP = (35, 15, 60)
COLOR_PURANA_BOTTOM = (90, 20, 45)

COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (230, 190, 90)

INVOCATION_FONT_FRAC = 0.046
SERIES_LABEL_FONT_FRAC = 0.040
TITLE_FONT_FRAC = 0.072
STORY_START_FONT_FRAC = 0.052   # starting size the auto-fit shrinks DOWN from
STORY_MIN_FONT_FRAC = 0.030     # legibility floor -- see module docstring
MORAL_FONT_FRAC = 0.042
SOURCE_FONT_FRAC = 0.030
SUBSCRIBE_FONT_FRAC = 0.038

STORY_LINE_SPACING = 1.3  # multiplier on font size, for readable line height within the story block

DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు పురాణ కథల కోసం సబ్‌స్క్రైబ్ చేయండి"

ICON_FRAC = 0.078
ICON_GAP_FRAC = 0.045

# Border + Sri Chakra watermark (per explicit request, 2026-10-02: "muggu
# like design... at border or in middle... to bring live feel instead
# of static", then again 2026-10-02: "i want slowly rotating sri chakram
# in background its not visible currently, can increase brightness a
# little more" -- swapped the generic muggu motif for an actual Sri
# Chakra/Sri Yantra (images/sri_chakra.py) and raised the watermark alpha
# from an earlier, too-faint 40 up to 110, confirmed visually legible
# against the card's dark background without competing with the text).
# A thin double-line gold border is inset from the card edge, and the
# Sri Chakra is centered in the content column, behind all text -- a
# watermark, not a competing foreground element. render() below bakes
# this in as a STATIC image (used as a plain fallback / for tests);
# the production pipeline uses render_layers() instead, which keeps the
# Sri Chakra on its own transparent layer so
# video/assembler.py's assemble_purana_short_with_rotating_chakra can
# animate it (a slow back-and-forth sway, see that function's docstring
# for why a sway rather than a continuous spin) while the backdrop and
# text stay perfectly still.
BORDER_OUTER_MARGIN_FRAC = 0.035
BORDER_ACCENT = (230, 190, 90)
CHAKRA_WATERMARK_ALPHA = 110  # raised from 40 -- "not visible currently, increase brightness"
CHAKRA_ACCENT_RGB = (235, 200, 110)  # slightly lighter/warmer gold, reads better at this alpha
CHAKRA_RADIUS_FRAC = 0.30


@dataclass(frozen=True, slots=True)
class PuranaShortCard:
    story: PuranaShortStory
    episode_number: int = 1  # ever-incrementing posting count, NOT the 0-9 content rotation index -- see module docstring
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PuranaShortCardLayers:
    """Three separate images consumed by the rotating-chakra video
    pipeline (video/assembler.py's assemble_purana_short_with_rotating_chakra)
    instead of one flattened frame, so the Sri Chakra motif can be
    animated on its own layer while the backdrop and text stay fixed.

    background_path: opaque gradient + border. No motif, no text.
    chakra_path: transparent PNG, Sri Chakra motif only, full canvas size,
        sits BEHIND the text layer once composited.
    text_path: transparent PNG, every text element + the icon row, full
        canvas size, sits on TOP of the (rotating) chakra layer.
    """
    background_path: Path
    chakra_path: Path
    text_path: Path


class PuranaShortCardRenderer:
    """Renders a PuranaShortCard either as one flattened static image
    (render()) or as three separate layers for the rotating-chakra video
    pipeline (render_layers()) -- both share the same layout/fit logic
    via _compose()."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: PuranaShortCard) -> Path:
        """Flattens background + chakra watermark + text into one static
        .mp4-ready still image -- a plain fallback for callers that don't
        need the rotating variant (e.g. a quick preview or test)."""
        background, chakra_layer, text_layer = self._compose(card)
        canvas = background.copy()
        canvas.alpha_composite(chakra_layer)
        canvas.alpha_composite(text_layer)

        output_path = self._build_output_path(card)
        final = canvas.convert("RGB")
        final.save(
            output_path,
            format=self._settings.image_output_format,
            quality=self._settings.image_output_quality,
            optimize=True,
        )
        logger.info("Rendered purana short card (static) for %s to %s", card.story.title_en, output_path)
        return output_path

    def render_layers(self, card: PuranaShortCard) -> PuranaShortCardLayers:
        """Saves background/chakra/text as three separate files for
        video/assembler.py's rotating-chakra assembly -- the production
        path per the "slowly rotating sri chakram" request."""
        background, chakra_layer, text_layer = self._compose(card)

        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        slug = card.story.title_en.split(" ")[0].lower()
        background_path = self._settings.output_dir / f"purana_short_{slug}_bg.jpg"
        chakra_path = self._settings.output_dir / f"purana_short_{slug}_chakra.png"
        text_path = self._settings.output_dir / f"purana_short_{slug}_text.png"

        background.convert("RGB").save(
            background_path, format="JPEG", quality=self._settings.image_output_quality, optimize=True,
        )
        chakra_layer.save(chakra_path, format="PNG")
        text_layer.save(text_path, format="PNG")

        logger.info("Rendered purana short card layers for %s to %s", card.story.title_en, self._settings.output_dir)
        return PuranaShortCardLayers(background_path, chakra_path, text_path)

    def _compose(self, card: PuranaShortCard) -> tuple[Image.Image, Image.Image, Image.Image]:
        """Does all the layout/fit work once, drawing onto three separate
        RGBA canvases (background, chakra, text) so callers can either
        flatten them (render()) or keep them apart (render_layers())."""
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            background = vertical_gradient(width, height, COLOR_PURANA_TOP, COLOR_PURANA_BOTTOM).convert("RGBA")
            self._draw_border(background)

            chakra_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            self._draw_chakra_watermark(chakra_layer, width, height)

            text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            content_top = int(height * 0.08)
            footer_bottom = int(height * 0.68)

            invocation_font = self._fit_font_to_width(
                draw, card.story.invocation_te, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            title_font = self._fit_font_to_width(
                draw, card.story.title_te, max_width=content_width,
                start_size=int(width * TITLE_FONT_FRAC), weight="Bold",
            )
            moral_font = self._fit_font_to_width(
                draw, card.story.moral_te, max_width=content_width,
                start_size=int(width * MORAL_FONT_FRAC), weight="Bold",
            )
            source_font = self._fonts.get_font(size=int(width * SOURCE_FONT_FRAC), weight="Regular")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            series_label = f"పురాణ కథ - {card.episode_number}"
            source_line = f"— {card.story.purana_name_te}"

            # Fixed-height elements (everything except the story body)
            # measured first, same bottom-up-anchoring approach already
            # validated on the alert/rashi cards -- the story body then
            # gets whatever vertical space is left, and fits itself into
            # exactly that.
            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            title_h = int(title_font.size * 1.2)
            moral_h = int(moral_font.size * 1.2)
            source_h = int(source_font.size * 1.2)
            subscribe_h = int(subscribe_font.size * 1.15)

            block_gap = int(height * 0.022)
            icon_size = int(width * ICON_FRAC)

            subscribe_top = footer_bottom - subscribe_h
            icon_row_top = subscribe_top - block_gap - icon_size if card.icon_paths else subscribe_top
            source_top = icon_row_top - block_gap - source_h
            moral_top = source_top - int(block_gap * 0.6) - moral_h

            story_box_top = (
                content_top + invocation_h + block_gap + series_h + block_gap + title_h + block_gap
            )
            story_box_bottom = moral_top - block_gap
            story_box_height = max(story_box_bottom - story_box_top, int(height * 0.1))

            story_font, story_lines, story_block_height = self._fit_paragraph_to_box(
                draw, card.story.story_te, max_width=content_width, max_height=story_box_height,
            )
            if story_block_height > story_box_height:
                logger.warning(
                    "Purana short story '%s' still overflows its box at the font floor "
                    "(needs %dpx, has %dpx) -- consider shortening content/purana_short_stories.py.",
                    card.story.title_en, story_block_height, story_box_height,
                )

            # Vertically center the (possibly shorter-than-budgeted) story
            # block within its box, so a short story doesn't look stranded
            # near the top with a big gap before the moral line.
            story_top = story_box_top + max((story_box_height - story_block_height) // 2, 0)

            cursor_y = content_top
            cursor_y = self._draw_centered_line(
                draw, card.story.invocation_te, invocation_font, width, cursor_y, COLOR_GOLD,
            )
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, series_label, series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, card.story.title_te, title_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, story_lines, story_font, width, story_top, COLOR_TEXT_LIGHT)

            self._draw_centered_line(draw, card.story.moral_te, moral_font, width, moral_top, COLOR_GOLD)
            self._draw_centered_line(draw, source_line, source_font, width, source_top, COLOR_TEXT_LIGHT)

            if card.icon_paths:
                self._draw_icon_row(text_layer, card.icon_paths, width, icon_row_top)

            self._draw_centered_line(draw, card.subscribe_text, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)

            return background, chakra_layer, text_layer

        except OSError as exc:
            raise ImageRenderError(f"Purana short card rendering/save failed: {exc}") from exc

    def _draw_border(self, canvas: Image.Image) -> None:
        """Thin double-line gold border inset from the card edge -- same
        generic, copyright-free "traditional border" technique already
        used for the Rashi Mantra backgrounds, reused here per the
        explicit request to highlight the card's border."""
        width, height = canvas.size
        draw = ImageDraw.Draw(canvas)
        outer_margin = int(width * BORDER_OUTER_MARGIN_FRAC)
        inner_margin = outer_margin + 10
        draw.rectangle(
            [outer_margin, outer_margin, width - outer_margin, height - outer_margin],
            outline=BORDER_ACCENT, width=4,
        )
        draw.rectangle(
            [inner_margin, inner_margin, width - inner_margin, height - inner_margin],
            outline=BORDER_ACCENT, width=2,
        )

    def _draw_chakra_watermark(self, chakra_layer: Image.Image, width: int, height: int) -> None:
        """Draws the Sri Chakra motif directly onto its own transparent
        layer, centered in the content column -- a clearly-visible (but
        still background, not foreground) watermark per the explicit
        "not visible currently, increase brightness" request. Kept on its
        own layer (rather than composited onto a shared canvas) so
        video/assembler.py's assemble_purana_short_with_rotating_chakra
        can rotate this exact image independently of the backdrop/text."""
        draw = ImageDraw.Draw(chakra_layer)
        draw_sri_chakra_roundel(
            draw, center=(width // 2, int(height * 0.42)),
            radius=int(width * CHAKRA_RADIUS_FRAC),
            accent=(*CHAKRA_ACCENT_RGB, CHAKRA_WATERMARK_ALPHA),
        )

    def _fit_paragraph_to_box(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int,
    ) -> tuple["ImageFont.FreeTypeFont", list[str], int]:
        """Shrink the story font (re-wrapping at each size) until the
        wrapped paragraph's total height fits max_height, or until
        STORY_MIN_FONT_FRAC is reached -- see module docstring. Returns
        the chosen font, the wrapped lines, and the block's total pixel
        height (so the caller can vertically center it)."""
        start_size = int(CARD_WIDTH * STORY_START_FONT_FRAC)
        min_size = int(CARD_WIDTH * STORY_MIN_FONT_FRAC)

        size = start_size
        while size >= min_size:
            font = self._fonts.get_font(size=size, weight="Regular")
            lines = self._wrap_text(draw, text, font, max_width)
            line_height = int(size * STORY_LINE_SPACING)
            total_height = line_height * len(lines)
            if total_height <= max_height or size == min_size:
                return font, lines, total_height
            size -= 2

        # Unreachable in practice (loop always returns at size == min_size),
        # kept only as an explicit fallback for static analysis.
        font = self._fonts.get_font(size=min_size, weight="Regular")
        lines = self._wrap_text(draw, text, font, max_width)
        return font, lines, int(min_size * STORY_LINE_SPACING) * len(lines)

    def _draw_paragraph(
        self, draw: ImageDraw.ImageDraw, lines: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int, color: tuple[int, int, int],
    ) -> None:
        line_height = int(font.size * STORY_LINE_SPACING)
        y = top
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            draw.text(((width - line_w) // 2, y - bbox[1]), line, font=font, fill=(*color, 255))
            y += line_height

    def _draw_icon_row(self, canvas: Image.Image, icon_paths: list[Path], width: int, top: int) -> None:
        icon_size = int(width * ICON_FRAC)
        icon_gap = int(width * ICON_GAP_FRAC)

        icons: list[Image.Image] = []
        for path in icon_paths:
            try:
                with Image.open(path) as raw:
                    icon = raw.convert("RGBA")
                    icon.thumbnail((icon_size, icon_size))
                    icons.append(icon)
            except (OSError, UnidentifiedImageError) as exc:
                logger.warning("Could not load purana short card icon at %s (%s) -- skipping it.", path, exc)

        if not icons:
            return

        total_w = sum(icon.width for icon in icons) + icon_gap * (len(icons) - 1)
        x = (width - total_w) // 2
        max_h = max(icon.height for icon in icons)

        for icon in icons:
            y = top + (max_h - icon.height) // 2
            canvas.alpha_composite(icon, (x, y))
            x += icon.width + icon_gap

    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
        if not text:
            return [""]
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if (bbox[2] - bbox[0]) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_centered_line(
        self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont",
        width: int, top: int, color: tuple[int, int, int],
    ) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text(((width - line_w) // 2, top - bbox[1]), text, font=font, fill=(*color, 255))
        return top + int(font.size * 1.15)

    def _fit_font_to_width(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, weight: str,
        min_size: int = 24,
    ) -> "ImageFont.FreeTypeFont":
        size = start_size
        while size > min_size:
            font = self._fonts.get_font(size=size, weight=weight)
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                return font
            size -= 4
        return self._fonts.get_font(size=min_size, weight=weight)

    def _build_output_path(self, card: PuranaShortCard) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        slug = card.story.title_en.split(" ")[0].lower()
        filename = f"purana_short_{slug}.{ext}"
        return self._settings.output_dir / filename
