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

logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# Deep indigo-to-maroon -- distinct from every other card family on this
# channel (see module docstring).
COLOR_PURANA_TOP = (35, 15, 60)
COLOR_PURANA_BOTTOM = (90, 20, 45)

COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (230, 190, 90)

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


@dataclass(frozen=True, slots=True)
class PuranaShortCard:
    story: PuranaShortStory
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)


class PuranaShortCardRenderer:
    """Renders a single PuranaShortCard to a static 9:16 image file."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: PuranaShortCard) -> Path:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            canvas = vertical_gradient(width, height, COLOR_PURANA_TOP, COLOR_PURANA_BOTTOM).convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            content_top = int(height * 0.08)
            footer_bottom = int(height * 0.68)

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

            series_label = "పురాణ కథ"
            source_line = f"— {card.story.purana_name_te}"

            # Fixed-height elements (everything except the story body)
            # measured first, same bottom-up-anchoring approach already
            # validated on the alert/rashi cards -- the story body then
            # gets whatever vertical space is left, and fits itself into
            # exactly that.
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

            story_box_top = content_top + series_h + block_gap + title_h + block_gap
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
            cursor_y = self._draw_centered_line(draw, series_label, series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, card.story.title_te, title_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, story_lines, story_font, width, story_top, COLOR_TEXT_LIGHT)

            self._draw_centered_line(draw, card.story.moral_te, moral_font, width, moral_top, COLOR_GOLD)
            self._draw_centered_line(draw, source_line, source_font, width, source_top, COLOR_TEXT_LIGHT)

            if card.icon_paths:
                self._draw_icon_row(canvas, card.icon_paths, width, icon_row_top)

            self._draw_centered_line(draw, card.subscribe_text, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)

            output_path = self._build_output_path(card)
            final = canvas.convert("RGB")
            final.save(
                output_path,
                format=self._settings.image_output_format,
                quality=self._settings.image_output_quality,
                optimize=True,
            )
            logger.info("Rendered purana short card for %s to %s", card.story.title_en, output_path)
            return output_path

        except OSError as exc:
            raise ImageRenderError(f"Purana short card rendering/save failed: {exc}") from exc

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
            draw.text(((width - line_w) // 2, y - bbox[1]), line, font=font, fill=color)
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
        draw.text(((width - line_w) // 2, top - bbox[1]), text, font=font, fill=color)
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
