"""
AlertCardRenderer: renders simple, punchy single-message cards — e.g.
"రాహు కాలం today" (red background, avoid this time) or "శుభ ఘడియలు today"
(green background, auspicious moments). A solid color background, a
small icon row, a title, and a short list of time/mantra lines, all
large and readable, centered, and filling the available space.

This is the VISUAL FRAME for a YouTube Short (9:16 vertical), not a
Community Post image — per explicit request, "short only". See
video/assembler.py for turning this static frame into an actual .mp4
Short (baked audio + fade-in already added there).

WRAPPING, NOT SHRINKING (v2 redesign): the original version picked ONE
font size per column, sized to fit the LONGEST value across every line
on the card. Once a full mantra shloka got added as a line, that one
long string forced every other line -- including short time values --
down to a tiny, barely-readable size (confirmed via a real render).
Fixed by wrapping long text across multiple lines at a fixed, generous
font size instead, so a short line stays large regardless of what else
is on the card. Available vertical space is also distributed across
whatever content exists, so a card with fewer/shorter lines fills the
frame rather than leaving a large empty gap above the subscribe text.

SINGLE-FONT DESIGN (reverted from an earlier Ponnala attempt): Ponnala
was tried per an explicit request for a more decorative look, but a
real render on Windows showed visibly broken/garbled Telugu text --
conjuncts and vowel signs not shaping correctly. This is a genuine,
hard-to-fix platform limitation: proper complex-text-shaping (libraqm)
is not readily installable on Windows. Noto (telugu_font_path) has
rendered cleanly throughout the rest of this project without libraqm,
so everything here uses it exclusively rather than risk broken text.

ICON ROW: up to 3 icon images (e.g. Lakshmi, Ganesha, Kubera) placed in
a horizontal row near the top, in the order given in
AlertCard.icon_paths. Caller supplies real image files — this module
does not generate devotional artwork itself.

Deliberately its OWN small renderer rather than a shared base class with
the (since-removed) Daily Community Post renderer — the two had almost
nothing in common visually (no deity image, no Panchang panel, no
logo/watermark), so sharing code would have meant threading a lot of
"skip this part" conditionals through one class instead of just...
not doing that.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.layout import vertical_gradient

logger = logging.getLogger(__name__)

# True YouTube Shorts vertical format (9:16). NOT the same as the main
# branded card's canvas_width/canvas_height (4:5, meant for Community
# Posts) -- Shorts specifically need 9:16 to display full-screen/be
# eligible for the Shorts shelf rather than the regular feed.
ALERT_CARD_WIDTH = 1080
ALERT_CARD_HEIGHT = 1920

COLOR_RAHU_TOP = (120, 15, 15)      # deep red
COLOR_RAHU_BOTTOM = (70, 5, 5)
COLOR_SHUBHA_TOP = (20, 90, 45)     # deep green
COLOR_SHUBHA_BOTTOM = (10, 55, 25)
COLOR_TEXT_LIGHT = (255, 250, 240)

ICON_SIZE = int(ALERT_CARD_WIDTH * 0.16)
ICON_GAP = int(ALERT_CARD_WIDTH * 0.06)
ICON_ROW_TOP = int(ALERT_CARD_HEIGHT * 0.06)

# Fixed, generous sizes (fraction of width) -- long content WRAPS instead
# of shrinking these, so a short line always stays this large.
TITLE_FONT_FRAC = 0.10
DATE_FONT_FRAC = 0.042
LABEL_FONT_FRAC = 0.048
VALUE_FONT_FRAC = 0.062
SUBSCRIBE_FONT_FRAC = 0.045
SECONDARY_FONT_FRAC = 0.032  # notably smaller than LABEL_FONT_FRAC -- for de-emphasized extra info

DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు ముహూర్తాలకొరకు సబ్‌స్క్రైబ్ చేయండి"  # "Subscribe for daily muhurtams"


@dataclass(frozen=True, slots=True)
class AlertCard:
    """One alert card's content — icon row, title, date, main lines, and
    optional compact secondary info (e.g. other inauspicious periods on
    the Rahu Kalam card, shown smaller than the main content)."""
    title: str
    lines: list[tuple[str, str]]  # (label, value) pairs
    top_color: tuple[int, int, int]
    bottom_color: tuple[int, int, int]
    filename_suffix: str  # e.g. "rahu_kalam" -- used to build the output filename
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)  # e.g. [Lakshmi, Ganesha, Kubera], left-to-right order
    date_text: str = ""  # e.g. "17 సెప్టెంబర్ 2026, గురువారం" -- shown below the title
    secondary_info: str = ""  # compact extra info shown in a smaller font below the main lines


class AlertCardRenderer:
    """Renders a single AlertCard to a 9:16 image file."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: AlertCard, for_date: date) -> Path:
        width = ALERT_CARD_WIDTH
        height = ALERT_CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            canvas = vertical_gradient(width, height, card.top_color, card.bottom_color).convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            icons_bottom = self._draw_icon_row(canvas, card.icon_paths, width)

            title_font = self._fit_font_to_width(
                draw, card.title, max_width=content_width, start_size=int(width * TITLE_FONT_FRAC), weight="Bold",
            )
            date_font = self._fit_font_to_width(
                draw, card.date_text, max_width=content_width, start_size=int(width * DATE_FONT_FRAC), weight="Regular",
            )
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            title_bbox = draw.textbbox((0, 0), card.title, font=title_font)
            title_h = int(title_bbox[3] - title_bbox[1])

            date_h = 0
            if card.date_text:
                date_bbox = draw.textbbox((0, 0), card.date_text, font=date_font)
                date_h = int(date_bbox[3] - date_bbox[1])

            subscribe_bbox = draw.textbbox((0, 0), card.subscribe_text, font=subscribe_font)
            subscribe_h = int(subscribe_bbox[3] - subscribe_bbox[1])
            # Real evidence from the actual mobile app (a screenshot showed
            # our own content overlapping YouTube's channel handle, caption
            # text, and visibility badge) -- those occupy roughly the
            # bottom 25% of the frame, not the ~14% originally assumed.
            # Moved up substantially so ALL our content, not just the
            # subscribe line, finishes well clear of that zone.
            subscribe_zone_top = int(height * 0.68)

            content_top = icons_bottom + int(height * 0.05) if icons_bottom else int(height * 0.30)
            available_bottom = subscribe_zone_top - int(height * 0.03)
            available_height = max(available_bottom - content_top, 0)

            n_gaps = len(card.lines) + 1 + (1 if card.date_text else 0) + (1 if card.secondary_info else 0)
            min_gap = 2
            line_gap = int(height * 0.012)

            # Shrink-to-fit loop: moving the safe zone up (above) means
            # less room than before, and dense days (mantra + secondary
            # periods together) can need more than gap-shrinking alone can
            # supply -- confirmed via a real render that even minimum gaps
            # weren't enough and text started overlapping itself. Try
            # progressively smaller label/value/secondary font sizes
            # (never below 65% of the base size, which stays readable)
            # until the content actually fits at MINIMUM gaps, then hand
            # off to the normal gap-distribution logic below.
            font_scale = 1.0
            while True:
                label_font = self._fonts.get_font(size=max(int(width * LABEL_FONT_FRAC * font_scale), 18), weight="Regular")
                value_font = self._fonts.get_font(size=max(int(width * VALUE_FONT_FRAC * font_scale), 22), weight="Bold")
                secondary_font = self._fonts.get_font(size=max(int(width * SECONDARY_FONT_FRAC * font_scale), 16), weight="Regular")

                wrapped_lines = []
                for label, value in card.lines:
                    label_wrapped = self._wrap_text(draw, label, label_font, content_width)
                    value_wrapped = self._wrap_text(draw, value, value_font, content_width)
                    label_h = self._block_height(draw, label_wrapped, label_font)
                    value_h = self._block_height(draw, value_wrapped, value_font)
                    wrapped_lines.append((label_wrapped, value_wrapped, label_h + line_gap + value_h))

                secondary_wrapped = []
                secondary_h = 0
                if card.secondary_info:
                    secondary_wrapped = self._wrap_text(draw, card.secondary_info, secondary_font, content_width)
                    secondary_h = self._block_height(draw, secondary_wrapped, secondary_font)

                total_lines_height = sum(h for _, _, h in wrapped_lines)
                needed_at_min_gap = title_h + date_h + secondary_h + n_gaps * min_gap + total_lines_height

                if needed_at_min_gap <= available_height or font_scale <= 0.65:
                    break
                font_scale -= 0.08

            # Correct formula: solve directly for the gap that makes
            # content_fixed_height + n_gaps*gap == available_height,
            # rather than scaling baseline_gap by a needed/available ratio
            # (that ratio approach was mathematically wrong -- it doesn't
            # account for how much of needed_height is fixed content vs.
            # gaps, and under-shot badly once content_fixed was a large
            # share of the total, causing exactly the overlap a real
            # render caught: gaps looked "shrunk" but not by enough).
            # The font-shrink loop above already guarantees
            # content_fixed_height + n_gaps*min_gap <= available_height,
            # so this quotient is always >= min_gap when that holds.
            content_fixed_height = title_h + date_h + secondary_h + total_lines_height
            ideal_gap = (available_height - content_fixed_height) // n_gaps
            gap = max(ideal_gap, min_gap)

            cursor_y = content_top
            title_w = title_bbox[2] - title_bbox[0]
            draw.text(
                ((width - title_w) // 2, cursor_y - title_bbox[1]),
                card.title, font=title_font, fill=COLOR_TEXT_LIGHT,
            )
            cursor_y += title_h + gap

            if card.date_text:
                date_bbox = draw.textbbox((0, 0), card.date_text, font=date_font)
                date_w = date_bbox[2] - date_bbox[0]
                draw.text(
                    ((width - date_w) // 2, cursor_y - date_bbox[1]),
                    card.date_text, font=date_font, fill=COLOR_TEXT_LIGHT,
                )
                cursor_y += date_h + gap

            for label_wrapped, value_wrapped, _ in wrapped_lines:
                cursor_y = self._draw_centered_block(draw, label_wrapped, label_font, width, cursor_y)
                cursor_y += line_gap
                cursor_y = self._draw_centered_block(draw, value_wrapped, value_font, width, cursor_y)
                cursor_y += gap

            if card.secondary_info:
                cursor_y = self._draw_centered_block(draw, secondary_wrapped, secondary_font, width, cursor_y)
                cursor_y += gap

            subscribe_w = subscribe_bbox[2] - subscribe_bbox[0]
            subscribe_y = subscribe_zone_top - subscribe_h // 2
            draw.text(
                ((width - subscribe_w) // 2, subscribe_y - subscribe_bbox[1]),
                card.subscribe_text, font=subscribe_font, fill=COLOR_TEXT_LIGHT,
            )

            output_path = self._build_output_path(card, for_date)
            final = canvas.convert("RGB")
            final.save(
                output_path,
                format=self._settings.image_output_format,
                quality=self._settings.image_output_quality,
                optimize=True,
            )
            logger.info("Rendered alert card '%s' to %s", card.filename_suffix, output_path)
            return output_path

        except OSError as exc:
            raise ImageRenderError(f"Alert card rendering/save failed: {exc}") from exc

    def _draw_icon_row(self, canvas: Image.Image, icon_paths: list[Path], width: int) -> int:
        """Paste up to 3 icons in a centered horizontal row near the top.
        Returns the y-coordinate where the icon row ends (0 if no icons),
        so the caller knows where it's safe to start the text block."""
        if not icon_paths:
            return 0

        icons: list[Image.Image] = []
        for path in icon_paths:
            try:
                with Image.open(path) as raw:
                    icon = raw.convert("RGBA")
                    icon.thumbnail((ICON_SIZE, ICON_SIZE))
                    icons.append(icon)
            except (OSError, UnidentifiedImageError) as exc:
                logger.warning("Could not load icon at %s (%s) -- skipping it.", path, exc)

        if not icons:
            return 0

        total_w = sum(icon.width for icon in icons) + ICON_GAP * (len(icons) - 1)
        x = (width - total_w) // 2
        max_h = max(icon.height for icon in icons)

        for icon in icons:
            y = ICON_ROW_TOP + (max_h - icon.height) // 2
            canvas.alpha_composite(icon, (x, y))
            x += icon.width + ICON_GAP

        return ICON_ROW_TOP + max_h

    def _wrap_text(
        self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", max_width: int,
    ) -> list[str]:
        """Word-wrap text into however many lines are needed to fit
        max_width at this font size -- used instead of shrinking the
        font, so short lines elsewhere on the card stay large."""
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

    def _block_height(
        self, draw: ImageDraw.ImageDraw, wrapped: list[str], font: "ImageFont.FreeTypeFont",
    ) -> int:
        """Total rendered height of a wrapped multi-line block."""
        line_height = int(draw.textbbox((0, 0), "Ag", font=font)[3])
        return line_height * len(wrapped)

    def _draw_centered_block(
        self, draw: ImageDraw.ImageDraw, wrapped: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int,
    ) -> int:
        """Draw each wrapped line centered horizontally, stacked from
        `top`. Returns the y-coordinate just below the block."""
        line_height = int(draw.textbbox((0, 0), "Ag", font=font)[3])
        y = top
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            draw.text(((width - line_w) // 2, y - bbox[1]), line, font=font, fill=COLOR_TEXT_LIGHT)
            y += line_height
        return y

    def _fit_font_to_width(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, weight: str,
        min_size: int = 24,
    ) -> "ImageFont.FreeTypeFont":
        """Return the largest font (at or below start_size) that fits text
        within max_width on ONE line, shrinking in steps if needed. Used
        only for the title and subscribe text, which are meant to stay
        single-line rather than wrap."""
        size = start_size
        while size > min_size:
            font = self._fonts.get_font(size=size, weight=weight)
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                return font
            size -= 4
        return self._fonts.get_font(size=min_size, weight=weight)

    def _build_output_path(self, card: AlertCard, for_date: date) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        filename = f"{for_date.isoformat()}_alert_{card.filename_suffix}.{ext}"
        return self._settings.output_dir / filename
