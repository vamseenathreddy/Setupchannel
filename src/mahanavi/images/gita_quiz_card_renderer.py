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

Shares the exact same palette, border, and real Krishna-Arjuna
background photo as GitaSlokaCardRenderer (imported constants, same
_build_background technique) so quiz-day and verse-day cards read as
the same series, just a different day's format -- not two different
channels.

NEXT-EPISODE HINT (explicit request, 2026-10-03: "also in quiz short
below post repati short lo yem nerchukobotunnamo hint or intro like
that one line at bottom") -- the quiz card also shows a one-line
teaser at the very bottom for TOMORROW's verse (which chapter it's
from, not the verse itself), so every Short ends by pointing at the
next one. This is knowable in advance because the rotation is
deterministic: see post_gita_sloka_short.py, which computes it as
GITA_SLOKAS[(target_index + 1) % len(GITA_SLOKAS)] without yet writing
that as the persisted state (state only advances after a successful
upload).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.bhagavad_gita_slokas import GitaSloka
from mahanavi.content.gita_sloka_quiz import GitaQuizOptions
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.gita_sloka_card_renderer import (
    BORDER_ACCENT,
    BORDER_OUTER_MARGIN_FRAC,
    COLOR_GITA_BOTTOM,
    COLOR_GITA_TOP,
    COLOR_GOLD,
    COLOR_TEXT_LIGHT,
    DEFAULT_INVOCATION,
    GITA_BG_OVERLAY_ALPHA,
    TEXT_LINE_SPACING,
    strip_danda_marks,
)
from mahanavi.images.flow import StickerZone, wrap_block
from mahanavi.images.layout import vertical_gradient
from mahanavi.video.watermark import bake_watermark

from mahanavi.images.opinion_line import OPINION_TE
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

SUBSCRIBE_START_FONT_FRAC = 0.038
SUBSCRIBE_MIN_FONT_FRAC = 0.026

# Same quiz-competition CTA as GitaSlokaCardRenderer -- explicit
# request, 2026-10-03 (see that module's docstring).
DEFAULT_SUBSCRIBE_TEXT = (
    "ప్రతిరోజు ఒక గీతా శ్లోకం నేర్చుకోండి — "
    "మా భగవద్గీత క్విజ్ పోటీలో పాల్గొనడానికి సబ్‌స్క్రైబ్ చేయండి!"
)
# "ee sloka ye adyaayam lonidi" (explicit correction, 2026-10-04) --
# "this verse belongs to which chapter", not the old "ఏ అధ్యాయం,
# శ్లోకం?" phrasing, which read like broken Telugu grammar.
DEFAULT_QUESTION = "ఈ శ్లోకం ఏ అధ్యాయంలోనిది?"
DEFAULT_CTA = "సమాధానం కామెంట్‌లో చెప్పండి! నిర్ధారణ కోసం నిన్నటి Short చూడండి 👆"

NEXT_HINT_LABEL_TEXT = "రేపటి ఎపిసోడ్‌లో"
NEXT_HINT_LABEL_FONT_FRAC = 0.034
NEXT_HINT_TEXT_START_FONT_FRAC = 0.036
NEXT_HINT_TEXT_MIN_FONT_FRAC = 0.026


@dataclass(frozen=True, slots=True)
class GitaQuizCard:
    quiz: GitaQuizOptions
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    question_text: str = DEFAULT_QUESTION
    cta_text: str = DEFAULT_CTA
    icon_paths: list[Path] = field(default_factory=list)
    # Tomorrow's verse -- shown at the card's bottom as a one-line
    # teaser (chapter name only, not the verse itself). See module
    # docstring's "NEXT-EPISODE HINT" section. None skips the teaser.
    next_verse_hint: GitaSloka | None = None
    # Krishna/Vishnu invocation shown at the very top -- same rotation
    # as the verse-day card (see gita_sloka_card_renderer.pick_invocation).
    invocation_text: str = DEFAULT_INVOCATION


class GitaQuizCardRenderer:
    """Renders a GitaQuizCard as one flattened static image -- same
    static-card, no-rotation design as GitaSlokaCardRenderer."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: GitaQuizCard) -> Path:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.14)  # keeps text clear of Shorts side buttons
        content_width = width - 2 * margin_x

        try:
            canvas = self._build_background(width, height)
            self._draw_border(canvas)

            draw = ImageDraw.Draw(canvas)
            target = card.quiz.target

            content_top = int(height * 0.055)
            footer_bottom = int(height * 0.68)

            invocation_font = self._fit_font_to_width(
                draw, card.invocation_text, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            question_font = self._fit_font_to_width(
                draw, card.question_text, max_width=content_width,
                start_size=int(width * QUESTION_FONT_FRAC), weight="Bold",
            )
            option_font = self._fonts.get_font(size=int(width * OPTION_FONT_FRAC), weight="SemiBold")
            subscribe_font, subscribe_lines, subscribe_h = self._fit_block_to_box(
                draw, card.subscribe_text, max_width=content_width, max_height=int(height * 0.085),
                start_frac=SUBSCRIBE_START_FONT_FRAC, min_frac=SUBSCRIBE_MIN_FONT_FRAC,
            )

            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            question_h = int(question_font.size * 1.3)

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

            # Fixed engagement line ("comment your opinion on this video") sits at the validated
            # footer_bottom; the subscribe line (and everything above it) moves up by its height.
            opinion_font = self._fit_font_to_width(
                draw, OPINION_TE, max_width=content_width, start_size=int(width * 0.036), weight="Bold",
            )
            opinion_h = int(opinion_font.size * 1.15)
            opinion_top = footer_bottom - opinion_h
            zone = StickerZone(height, width - margin_x)
            # Footer rows that land in the product-tag sticker zone wrap into the column to its right at the
            # same font size (2026-10-11); iterate until the bottom-anchored position settles.
            sub_line_h = int(subscribe_font.size * TEXT_LINE_SPACING)
            subscribe_lines = [card.subscribe_text]
            for _ in range(4):
                subscribe_top = opinion_top - int(height * 0.012) - sub_line_h * len(subscribe_lines)
                new_lines = wrap_block(
                    draw, card.subscribe_text, subscribe_font, content_width, subscribe_top, sub_line_h, zone,
                    lambda t: self._wrap_text(draw, t, subscribe_font, content_width),
                )
                if len(new_lines) == len(subscribe_lines):
                    subscribe_lines = new_lines
                    break
                subscribe_lines = new_lines
            subscribe_h = sub_line_h * len(subscribe_lines)
            subscribe_top = opinion_top - int(height * 0.012) - subscribe_h
            icon_row_top = subscribe_top - block_gap - icon_size if card.icon_paths else subscribe_top
            cta_line_h = int(cta_font.size * TEXT_LINE_SPACING)
            cta_top = icon_row_top - block_gap - cta_block_h
            for _ in range(3):
                cta_lines = wrap_block(
                    draw, card.cta_text, cta_font, content_width, cta_top, cta_line_h, zone,
                    lambda t: self._wrap_text(draw, t, cta_font, content_width),
                )
                new_top = icon_row_top - block_gap - cta_line_h * len(cta_lines)
                if new_top == cta_top:
                    break
                cta_top = new_top
            cta_block_h = cta_line_h * len(cta_lines)

            header_bottom = (
                content_top + invocation_h + block_gap + series_h + block_gap + question_h + block_gap
            )

            # Verse first, options directly under it (text moves UP, clear of the sticker zone).
            body_box_top = header_bottom
            body_box_bottom = cta_top - block_gap
            body_box_height = max(body_box_bottom - body_box_top, int(height * 0.15))
            sanskrit_box_height = body_box_height - options_block_h - block_gap

            sanskrit_font, sanskrit_lines, sanskrit_block_h = self._fit_block_to_box(
                draw, strip_danda_marks(target.sanskrit_deva), max_width=content_width, max_height=sanskrit_box_height,
                start_frac=SANSKRIT_START_FONT_FRAC, min_frac=SANSKRIT_MIN_FONT_FRAC, y0=body_box_top, zone=zone,
            )

            sanskrit_top = body_box_top
            options_top = sanskrit_top + sanskrit_block_h + block_gap

            cursor_y = content_top
            cursor_y = self._draw_centered_line(draw, card.invocation_text, invocation_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, "నేటి క్విజ్ — Quiz Time!", series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, card.question_text, question_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, sanskrit_lines, sanskrit_font, width, sanskrit_top, COLOR_GOLD, zone)

            y = options_top
            for label in option_labels:
                bbox = draw.textbbox((0, 0), label, font=option_font)
                text_w = bbox[2] - bbox[0]
                ox = zone.left if zone.hits(y, option_line_h) else margin_x
                draw.text((ox, y - bbox[1]), label, font=option_font, fill=(*COLOR_TEXT_LIGHT, 255))
                y += option_line_h

            self._draw_paragraph(draw, cta_lines, cta_font, width, cta_top, COLOR_GOLD, zone)

            if card.icon_paths:
                self._draw_icon_row(canvas, card.icon_paths, width, icon_row_top, zone)

            self._draw_paragraph(draw, subscribe_lines, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT, zone)
            self._draw_centered_line(draw, OPINION_TE, opinion_font, width, opinion_top, COLOR_TEXT_LIGHT)

            if card.next_verse_hint is not None:
                self._draw_next_hint_block(
                    draw, card.next_verse_hint, width, content_width, footer_bottom, block_gap,
                )

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

    def _draw_next_hint_block(
        self, draw: ImageDraw.ImageDraw, next_sloka: GitaSloka, width: int, content_width: int,
        footer_bottom: int, block_gap: int,
    ) -> None:
        """Drawn BELOW footer_bottom, in the card's lower margin (same
        spot GitaSlokaCardRenderer uses for its "yesterday's Q&A"
        block) -- a one-line teaser for tomorrow's verse: which chapter
        it's from, not the verse itself. See module docstring."""
        label_font = self._fonts.get_font(size=int(width * NEXT_HINT_LABEL_FONT_FRAC), weight="SemiBold")
        hint_text = f"రేపు {next_sloka.chapter_name_te} నుండి ఒక కొత్త శ్లోకం — మిస్ అవ్వకండి!"
        hint_font, hint_lines, _ = self._fit_block_to_box(
            draw, hint_text, max_width=content_width, max_height=int(width * 0.12),
            start_frac=NEXT_HINT_TEXT_START_FONT_FRAC, min_frac=NEXT_HINT_TEXT_MIN_FONT_FRAC,
        )

        top = footer_bottom + block_gap
        top = self._draw_centered_line(draw, NEXT_HINT_LABEL_TEXT, label_font, width, top, COLOR_GOLD)
        self._draw_paragraph(draw, hint_lines, hint_font, width, top, COLOR_TEXT_LIGHT)

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

    def _build_background(self, width: int, height: int) -> Image.Image:
        """Same real Krishna-Arjuna background as GitaSlokaCardRenderer
        (imported constants) -- see that class's _build_background for
        the full reasoning."""
        bg_path = self._settings.gita_background_image_path
        if bg_path is not None and bg_path.exists():
            try:
                with Image.open(bg_path) as raw:
                    fitted = ImageOps.fit(raw.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
                canvas = fitted.convert("RGBA")
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, GITA_BG_OVERLAY_ALPHA))
                return bake_watermark(Image.alpha_composite(canvas, overlay))
            except (OSError, UnidentifiedImageError) as exc:
                logger.warning(
                    "Could not load Gita background image at %s (%s) -- falling back to plain gradient.",
                    bg_path, exc,
                )
        return bake_watermark(vertical_gradient(width, height, COLOR_GITA_TOP, COLOR_GITA_BOTTOM).convert("RGBA"))

    def _fit_block_to_box(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int,
        start_frac: float, min_frac: float, y0: int | None = None, zone: StickerZone | None = None,
    ) -> tuple["ImageFont.FreeTypeFont", list[str], int]:
        start_size = int(CARD_WIDTH * start_frac)
        min_size = int(CARD_WIDTH * min_frac)

        size = start_size
        while size >= min_size:
            font = self._fonts.get_font(size=size, weight="Regular")
            line_height = int(size * TEXT_LINE_SPACING)
            lines = self._wrap_para(draw, text, font, max_width, y0, line_height, zone)
            total_height = line_height * len(lines)
            if total_height <= max_height or size == min_size:
                return font, lines, total_height
            size -= 2

        font = self._fonts.get_font(size=min_size, weight="Regular")
        lines = self._wrap_para(draw, text, font, max_width, y0, int(min_size * TEXT_LINE_SPACING), zone)
        return font, lines, int(min_size * TEXT_LINE_SPACING) * len(lines)

    def _wrap_para(
        self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", max_width: int,
        y0: int | None, line_height: int, zone: StickerZone | None,
    ) -> list[str]:
        if y0 is None or zone is None:
            lines: list[str] = []
            for raw_line in text.split("\n"):
                lines.extend(self._wrap_text(draw, raw_line, font, max_width))
            return lines
        return wrap_block(draw, text, font, max_width, y0, line_height, zone,
                          lambda t: self._wrap_text(draw, t, font, max_width))

    def _draw_paragraph(
        self, draw: ImageDraw.ImageDraw, lines: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int, color: tuple[int, int, int], zone: StickerZone | None = None,
    ) -> None:
        line_height = int(font.size * TEXT_LINE_SPACING)
        y = top
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            cx = zone.cx(y, line_height, line_w, width) if zone else width // 2
            draw.text((cx - line_w // 2, y - bbox[1]), line, font=font, fill=(*color, 255))
            y += line_height

    def _draw_icon_row(
        self, canvas: Image.Image, icon_paths: list[Path], width: int, top: int, zone: StickerZone | None = None,
    ) -> None:
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
        cx = width // 2
        if zone is not None and zone.hits(top, icon_size):
            # Row would cover the product-tag sticker: shrink the ICONS (not text) to fit the column to its right.
            if total_w > zone.width:
                k = zone.width / total_w
                icons = [i.resize((max(1, int(i.width * k)), max(1, int(i.height * k)))) for i in icons]
                icon_gap = int(icon_gap * k)
                total_w = sum(i.width for i in icons) + icon_gap * (len(icons) - 1)
            cx = zone.centre
        x = cx - total_w // 2
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
