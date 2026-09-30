"""
PuranaTextRenderer: renders a full Puranam story passage as ONE tall,
transparent-background Telugu text image, word-wrapped to a fixed
width at a large, comfortable-to-read font size. This tall image is
later scrolled vertically over a background image by video/scroll_assembler.py
(via ffmpeg's overlay filter with a time-varying y-offset), the same
technique used for end-credits-style scrolling text.

Rendered as ONE tall image rather than frame-by-frame, for the same
reason video/assembler.py assembles Shorts from one static image: it's
simpler, and ffmpeg's own overlay animation handles the actual motion
far more reliably than generating thousands of individual frames here.

TELUGU-ONLY TEXT (per explicit request): unlike the alert cards, this
renderer's text content is 100% Telugu -- no mixed Latin content, so
there's no need for the alert card's per-line font-fallback logic.

EMPHASIS (per explicit request): mantras and the phalasruti (benefit of
listening) render in Bold with a warm gold accent color, standing out
from the regular narrative text -- pass a TextSegment with
emphasized=True for these paragraphs. Plain strings still work exactly
as before (treated as emphasized=False), so existing callers don't
need to change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from mahanavi.config import Settings
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager

logger = logging.getLogger(__name__)

# Landscape long-form video canvas (16:9) -- per explicit confirmation
# that long-form/mid-roll-ad videos should be landscape, not vertical
# like the Shorts.
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Text column width -- narrower than the full frame, with margin on
# both sides so scrolling text never touches the frame edges.
TEXT_COLUMN_WIDTH = 1400
FONT_SIZE = 46
LINE_SPACING_FRAC = 1.5  # multiplier on raw line height, for readable spacing
PARAGRAPH_GAP_FRAC = 0.8  # extra gap between paragraphs, as a fraction of one line height

COLOR_REGULAR = (255, 250, 240, 255)   # warm off-white, same as before
COLOR_EMPHASIZED = (255, 205, 90, 255)  # warm gold -- mantras and phalasruti


@dataclass(frozen=True, slots=True)
class TextSegment:
    """One paragraph of the scrolling text. emphasized=True renders it
    Bold in a gold accent color instead of the regular white -- used
    for mantras and the phalasruti (benefit of listening) so they
    visually stand out from the surrounding narrative."""
    text: str
    emphasized: bool = False


ParagraphInput = str | TextSegment


class PuranaTextRenderer:
    """Renders a Puranam text passage (list of paragraphs) as one tall image."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(
        self,
        paragraphs: list[ParagraphInput],
        output_path: Path,
        text_column_width: int = TEXT_COLUMN_WIDTH,
    ) -> tuple[Path, int]:
        """Renders `paragraphs` (each a block of Telugu text, plain str or
        TextSegment) as one tall transparent PNG, word-wrapped to
        text_column_width. Returns the output path and the image's total
        height in pixels (the caller needs this to compute the scroll
        animation's duration/speed).

        text_column_width defaults to TEXT_COLUMN_WIDTH (the landscape
        long-form canvas's column) -- callers targeting a narrower canvas
        (e.g. a vertical Shorts scroll video) pass a smaller value so the
        text doesn't overflow the frame width."""
        segments = [p if isinstance(p, TextSegment) else TextSegment(text=p) for p in paragraphs]

        regular_font = self._fonts.get_font(size=FONT_SIZE, weight="Regular")
        bold_font = self._fonts.get_font(size=FONT_SIZE, weight="Bold")

        # Pillow needs a real image to measure text against before the
        # final canvas size is known -- use a throwaway 1x1 image.
        probe = Image.new("RGBA", (1, 1))
        probe_draw = ImageDraw.Draw(probe)
        line_height = probe_draw.textbbox((0, 0), "Ag", font=regular_font)[3]
        line_gap = int(line_height * (LINE_SPACING_FRAC - 1))
        paragraph_gap = int(line_height * PARAGRAPH_GAP_FRAC)

        wrapped_paragraphs = [
            (
                self._wrap_text(probe_draw, seg.text, bold_font if seg.emphasized else regular_font, text_column_width),
                seg.emphasized,
            )
            for seg in segments
        ]

        total_lines = sum(len(wrapped) for wrapped, _ in wrapped_paragraphs)
        total_height = int(
            total_lines * (line_height + line_gap)
            + max(len(wrapped_paragraphs) - 1, 0) * paragraph_gap
            + line_height * 4  # top/bottom padding so text starts/ends off-frame smoothly
        )

        try:
            canvas = Image.new("RGBA", (text_column_width, total_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)

            y = line_height * 2  # top padding
            for wrapped, emphasized in wrapped_paragraphs:
                font = bold_font if emphasized else regular_font
                color = COLOR_EMPHASIZED if emphasized else COLOR_REGULAR
                for line in wrapped:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_w = bbox[2] - bbox[0]
                    draw.text(
                        ((text_column_width - line_w) // 2, y - bbox[1]),
                        line, font=font, fill=color,
                    )
                    y += line_height + line_gap
                y += paragraph_gap

            output_path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output_path)
            logger.info("Rendered Puranam text image: %s (%dx%d)", output_path, text_column_width, total_height)
            return output_path, total_height

        except OSError as exc:
            raise ImageRenderError(f"Puranam text rendering/save failed: {exc}") from exc

    def _wrap_text(self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
        """Same word-wrap approach as AlertCardRenderer._wrap_text."""
        words = text.split()
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
