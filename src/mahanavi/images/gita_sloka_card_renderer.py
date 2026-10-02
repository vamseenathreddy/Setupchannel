"""
GitaSlokaCardRenderer: renders one "Bhagavad Gita Sloka" Short -- a
static card (STATIC, not scrolling, no narration, same "read it
yourself" design as every other static card on this channel) showing
one Gita verse (Sanskrit + Telugu meaning), per explicit request
(2026-10-02): "from bhagavadgeetha get daily one sloka and meening
shorts card at 3 to 4 pm daily with different colour with krishna and
Arjuna background image".

BACKGROUND: a deep teal-to-midnight-blue gradient (COLOR_GITA_TOP/
BOTTOM below) -- distinct from every other card family on this channel
(Rahu Kalam red, Shubha Ghadiyalu green, Durmuhurtham amber/brown,
Rashi Mantra green muggu, Purana Story indigo-maroon, Purana Concept
navy-violet). Teal/peacock-blue is also a deliberate thematic nod to
Krishna iconography (the peacock feather) without depicting anything
specific enough to be "a copy" of any one artwork.

KRISHNA-ARJUNA MOTIF: a static (not rotating -- unlike the Sri Chakra
cards, no rotation was requested for this series) line-art chariot
silhouette (images/krishna_arjuna_motif.py), drawn as a low-alpha gold
watermark behind the text -- see that module's docstring for why it's
abstract/geometric rather than a realistic depiction.

BORDER: same thin double-line gold border technique used on every other
card on this channel.

AUTO-FIT TEXT: the Sanskrit verse and its Telugu meaning are each
fit-to-box independently (same shrink-and-rewrap approach as
PuranaShortCardRenderer/PuranaConceptCardRenderer), since verse length
varies quite a bit across the Gita.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.bhagavad_gita_slokas import GitaSloka
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.krishna_arjuna_motif import draw_krishna_arjuna_chariot
from mahanavi.images.layout import vertical_gradient

logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# Deep teal-to-midnight-blue -- see module docstring for why this stays
# distinct from every other series' palette.
COLOR_GITA_TOP = (6, 56, 60)
COLOR_GITA_BOTTOM = (8, 12, 40)

COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (230, 190, 90)

INVOCATION_FONT_FRAC = 0.046
SERIES_LABEL_FONT_FRAC = 0.040
BADGE_FONT_FRAC = 0.036
SANSKRIT_START_FONT_FRAC = 0.054
SANSKRIT_MIN_FONT_FRAC = 0.032
MEANING_START_FONT_FRAC = 0.046
MEANING_MIN_FONT_FRAC = 0.028
SOURCE_FONT_FRAC = 0.030
SUBSCRIBE_FONT_FRAC = 0.038

TEXT_LINE_SPACING = 1.35

DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు గీతా శ్లోకం కోసం సబ్‌స్క్రైబ్ చేయండి"
DEFAULT_INVOCATION = "ఓం శ్రీ కృష్ణాయ నమః"

ICON_FRAC = 0.078
ICON_GAP_FRAC = 0.045

BORDER_OUTER_MARGIN_FRAC = 0.035
BORDER_ACCENT = (230, 190, 90)

# Chariot motif sizing/placement -- see images/krishna_arjuna_motif.py.
# Kept low-alpha, same watermark treatment as the Sri Chakra cards.
CHARIOT_ALPHA = 95
CHARIOT_SCALE_FRAC = 0.30       # motif "wheel diameter" as a fraction of card width
CHARIOT_BASELINE_Y_FRAC = 0.655  # where the wheel's bottom sits on the full card


@dataclass(frozen=True, slots=True)
class GitaSlokaCard:
    sloka: GitaSloka
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)


class GitaSlokaCardRenderer:
    """Renders a GitaSlokaCard as one flattened static image -- no
    rotation/layers needed for this series (unlike the Purana cards),
    so there's just the one render() path, assembled into video via the
    plain video/assembler.assemble_short()."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: GitaSlokaCard) -> Path:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            canvas = vertical_gradient(width, height, COLOR_GITA_TOP, COLOR_GITA_BOTTOM).convert("RGBA")
            self._draw_border(canvas)
            self._draw_chariot_watermark(canvas, width, height)

            draw = ImageDraw.Draw(canvas)
            sloka = card.sloka

            content_top = int(height * 0.06)
            footer_bottom = int(height * 0.68)

            invocation_font = self._fit_font_to_width(
                draw, DEFAULT_INVOCATION, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            badge_text = f"అధ్యాయం {sloka.chapter} • శ్లోకం {sloka.verse} — {sloka.chapter_name_te}"
            badge_font = self._fit_font_to_width(
                draw, badge_text, max_width=content_width,
                start_size=int(width * BADGE_FONT_FRAC), weight="SemiBold",
            )
            source_font = self._fonts.get_font(size=int(width * SOURCE_FONT_FRAC), weight="Regular")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            source_line = "— భగవద్గీత"

            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            badge_h = int(badge_font.size * 1.2)
            source_h = int(source_font.size * 1.2)
            subscribe_h = int(subscribe_font.size * 1.15)

            block_gap = int(height * 0.020)
            icon_size = int(width * ICON_FRAC)

            subscribe_top = footer_bottom - subscribe_h
            icon_row_top = subscribe_top - block_gap - icon_size if card.icon_paths else subscribe_top
            source_top = icon_row_top - block_gap - source_h

            header_bottom = (
                content_top + invocation_h + block_gap + series_h + block_gap + badge_h + block_gap
            )

            # Split the remaining vertical space between the Sanskrit
            # verse (top half) and its Telugu meaning (bottom half),
            # each auto-fit independently within its own half.
            body_box_top = header_bottom
            body_box_bottom = source_top - block_gap
            body_box_height = max(body_box_bottom - body_box_top, int(height * 0.15))
            sanskrit_box_height = int(body_box_height * 0.42)
            meaning_box_height = body_box_height - sanskrit_box_height - block_gap

            sanskrit_font, sanskrit_lines, sanskrit_block_h = self._fit_block_to_box(
                draw, sloka.sanskrit_deva, max_width=content_width, max_height=sanskrit_box_height,
                start_frac=SANSKRIT_START_FONT_FRAC, min_frac=SANSKRIT_MIN_FONT_FRAC,
            )
            meaning_font, meaning_lines, meaning_block_h = self._fit_block_to_box(
                draw, sloka.telugu_meaning, max_width=content_width, max_height=meaning_box_height,
                start_frac=MEANING_START_FONT_FRAC, min_frac=MEANING_MIN_FONT_FRAC,
            )

            sanskrit_top = body_box_top + max((sanskrit_box_height - sanskrit_block_h) // 2, 0)
            meaning_top = (
                body_box_top + sanskrit_box_height + block_gap
                + max((meaning_box_height - meaning_block_h) // 2, 0)
            )

            cursor_y = content_top
            cursor_y = self._draw_centered_line(draw, DEFAULT_INVOCATION, invocation_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, "నేటి గీతా శ్లోకం", series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, badge_text, badge_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, sanskrit_lines, sanskrit_font, width, sanskrit_top, COLOR_GOLD)
            self._draw_paragraph(draw, meaning_lines, meaning_font, width, meaning_top, COLOR_TEXT_LIGHT)

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
            logger.info("Rendered Gita sloka card for %s.%s to %s", sloka.chapter, sloka.verse, output_path)
            return output_path

        except OSError as exc:
            raise ImageRenderError(f"Gita sloka card rendering/save failed: {exc}") from exc

    def _draw_border(self, canvas: Image.Image) -> None:
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

    def _draw_chariot_watermark(self, canvas: Image.Image, width: int, height: int) -> None:
        watermark = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        scale = int(width * CHARIOT_SCALE_FRAC)
        baseline_y = int(height * CHARIOT_BASELINE_Y_FRAC)
        draw_krishna_arjuna_chariot(
            draw, center_x=width // 2, baseline_y=baseline_y, scale=scale,
            accent=(*COLOR_GOLD, CHARIOT_ALPHA), line_width=3,
        )
        canvas.alpha_composite(watermark)

    def _fit_block_to_box(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int,
        start_frac: float, min_frac: float,
    ) -> tuple["ImageFont.FreeTypeFont", list[str], int]:
        """Shrinks a (possibly multi-line, \\n-separated) text block down
        to fit max_height, re-wrapping each explicit line at every size
        tried. Returns the chosen font, the final wrapped lines, and the
        block's total pixel height."""
        start_size = int(CARD_WIDTH * start_frac)
        min_size = int(CARD_WIDTH * min_frac)

        size = start_size
        while size >= min_size:
            font = self._fonts.get_font(size=size, weight="Regular")
            lines: list[str] = []
            for raw_line in text.split("\n"):
                lines.extend(self._wrap_text(draw, raw_line, font, max_width))
            line_height = int(size * TEXT_LINE_SPACING)
            total_height = line_height * len(lines)
            if total_height <= max_height or size == min_size:
                return font, lines, total_height
            size -= 2

        font = self._fonts.get_font(size=min_size, weight="Regular")
        lines = []
        for raw_line in text.split("\n"):
            lines.extend(self._wrap_text(draw, raw_line, font, max_width))
        return font, lines, int(min_size * TEXT_LINE_SPACING) * len(lines)

    def _draw_paragraph(
        self, draw: ImageDraw.ImageDraw, lines: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int, color: tuple[int, int, int],
    ) -> None:
        line_height = int(font.size * TEXT_LINE_SPACING)
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
                logger.warning("Could not load Gita sloka card icon at %s (%s) -- skipping it.", path, exc)

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

    def _build_output_path(self, card: GitaSlokaCard) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        filename = f"gita_sloka_{card.sloka.chapter}_{card.sloka.verse}.{ext}"
        return self._settings.output_dir / filename
