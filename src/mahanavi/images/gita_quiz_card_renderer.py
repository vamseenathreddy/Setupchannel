"""
GitaQuizCardRenderer: renders the Gita Sloka series' QUIZ-DAY card -- a
static card (same "read it yourself" design as every other card on this
channel) showing YESTERDAY's verse again (Sanskrit only, no meaning, no
chapter/verse badge) with a "which chapter & verse was this?" question
and 4 lettered options, exactly one of which is correct.

Explicit request (2026-10-03): "i want to change plan to not every day
one sloka it should be like one day verse nextday quiz with 4 options
on before days verse so total 1400 days this pipeline will work. so
users will learn from yesterday also we have to push them to know
answer look yesterday verse post number." The chapter/verse badge is
deliberately OMITTED here (unlike GitaSlokaCardRenderer, which always
shows it) -- the whole point is that the answer can only be confirmed
by finding yesterday's Short on the channel again, not read directly
off this card.

Shares the exact same palette, border, and Krishna-Arjuna chariot
watermark as GitaSlokaCardRenderer (imported from that module, not
redefined) so quiz-day and verse-day cards read as the same series,
just a different day's format -- not two different channels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.gita_sloka_quiz import GitaQuizOptions
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.gita_sloka_card_renderer import (
    BORDER_ACCENT,
    BORDER_OUTER_MARGIN_FRAC,
    CHARIOT_ALPHA,
    CHARIOT_BASELINE_Y_FRAC,
    CHARIOT_SCALE_FRAC,
    COLOR_GITA_BOTTOM,
    COLOR_GITA_TOP,
    COLOR_GOLD,
    COLOR_TEXT_LIGHT,
    DEFAULT_INVOCATION,
    TEXT_LINE_SPACING,
)
from mahanavi.images.krishna_arjuna_motif import draw_krishna_arjuna_chariot
from mahanavi.images.layout import vertical_gradient

logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

INVOCATION_FONT_FRAC = 0.046
SERIES_LABEL_FONT_FRAC = 0.040
QUESTION_FONT_FRAC = 0.042
SANSKRIT_START_FONT_FRAC = 0.050
SANSKRIT_MIN_FONT_FRAC = 0.030
OPTION_FONT_FRAC = 0.040
CTA_START_FONT_FRAC = 0.034
CTA_MIN_FONT_FRAC = 0.024

ICON_FRAC = 0.078
ICON_GAP_FRAC = 0.045

DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు గీతా శ్లోకం కోసం సబ్‌స్క్రైబ్ చేయండి"
DEFAULT_QUESTION = "ఈ శ్లోకం ఏ అధ్యాయం, శ్లోకం?"
DEFAULT_CTA = "సమాధానం కామెంట్‌లో చెప్పండి! నిర్ధారణ కోసం నిన్నటి Short చూడండి 👆"


@dataclass(frozen=True, slots=True)
class GitaQuizCard:
    quiz: GitaQuizOptions
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    question_text: str = DEFAULT_QUESTION
    cta_text: str = DEFAULT_CTA
    icon_paths: list[Path] = field(default_factory=list)


class GitaQuizCardRenderer:
    """Renders a GitaQuizCard as one flattened static image -- same
    static-card, no-rotation design as GitaSlokaCardRenderer."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: GitaQuizCard) -> Path:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            canvas = vertical_gradient(width, height, COLOR_GITA_TOP, COLOR_GITA_BOTTOM).convert("RGBA")
            self._draw_border(canvas)
            self._draw_chariot_watermark(canvas, width, height)

            draw = ImageDraw.Draw(canvas)
            target = card.quiz.target

            content_top = int(height * 0.055)
            footer_bottom = int(height * 0.68)

            invocation_font = self._fit_font_to_width(
                draw, DEFAULT_INVOCATION, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            question_font = self._fit_font_to_width(
                draw, card.question_text, max_width=content_width,
                start_size=int(width * QUESTION_FONT_FRAC), weight="Bold",
            )
            option_font = self._fonts.get_font(size=int(width * OPTION_FONT_FRAC), weight="SemiBold")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * 0.038), weight="Bold",
            )

            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            question_h = int(question_font.size * 1.3)
            subscribe_h = int(subscribe_font.size * 1.15)

            block_gap = int(height * 0.018)
            icon_size = int(width * ICON_FRAC)

            option_labels = [
                f"{letter}) అధ్యాయం {s.chapter}, శ్లోకం {s.verse}"
                for letter, s in zip(["A", "B", "C", "D"], card.quiz.options)
            ]
            option_line_h = int(option_font.size * 1.3)
            options_block_h = option_line_h * len(option_labels)

            cta_font, cta_lines, cta_block_h = self._fit_block_to_box(
                draw, card.cta_text, max_width=content_width, max_height=int(height * 0.09),
                start_frac=CTA_START_FONT_FRAC, min_frac=CTA_MIN_FONT_FRAC,
            )

            subscribe_top = footer_bottom - subscribe_h
            icon_row_top = subscribe_top - block_gap - icon_size if card.icon_paths else subscribe_top
            cta_top = icon_row_top - block_gap - cta_block_h

            header_bottom = (
                content_top + invocation_h + block_gap + series_h + block_gap + question_h + block_gap
            )

            # Remaining space between the header (invocation/series/
            # question) and the footer (CTA/icons/subscribe) is split
            # between the Sanskrit verse (memory cue, top) and the 4
            # options (bottom).
            body_box_top = header_bottom
            body_box_bottom = cta_top - block_gap
            body_box_height = max(body_box_bottom - body_box_top, int(height * 0.15))
            sanskrit_box_height = body_box_height - options_block_h - block_gap

            sanskrit_font, sanskrit_lines, sanskrit_block_h = self._fit_block_to_box(
                draw, target.sanskrit_deva, max_width=content_width, max_height=sanskrit_box_height,
                start_frac=SANSKRIT_START_FONT_FRAC, min_frac=SANSKRIT_MIN_FONT_FRAC,
            )

            sanskrit_top = body_box_top + max((sanskrit_box_height - sanskrit_block_h) // 2, 0)
            options_top = body_box_top + sanskrit_box_height + block_gap

            cursor_y = content_top
            cursor_y = self._draw_centered_line(draw, DEFAULT_INVOCATION, invocation_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, "నేటి క్విజ్ — Quiz Time!", series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, card.question_text, question_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, sanskrit_lines, sanskrit_font, width, sanskrit_top, COLOR_GOLD)

            y = options_top
            for label in option_labels:
                bbox = draw.textbbox((0, 0), label, font=option_font)
                text_w = bbox[2] - bbox[0]
                draw.text((margin_x, y - bbox[1]), label, font=option_font, fill=(*COLOR_TEXT_LIGHT, 255))
                y += option_line_h

            self._draw_paragraph(draw, cta_lines, cta_font, width, cta_top, COLOR_GOLD)

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
            logger.info(
                "Rendered Gita quiz card (target %s.%s) to %s",
                target.chapter, target.verse, output_path,
            )
            return output_path

        except OSError as exc:
            raise ImageRenderError(f"Gita quiz card rendering/save failed: {exc}") from exc

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
                logger.warning("Could not load Gita quiz card icon at %s (%s) -- skipping it.", path, exc)

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

    def _build_output_path(self, card: GitaQuizCard) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        t = card.quiz.target
        filename = f"gita_quiz_{t.chapter}_{t.verse}.{ext}"
        return self._settings.output_dir / filename
