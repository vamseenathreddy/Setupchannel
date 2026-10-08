"""
PuranaConceptCardRenderer: renders one "Purana Concept" Short -- the
SIXTH short series on this channel, rotating daily through 6 content
concepts drawn from across all 18 Puranas (sloka, sacred place, vratha,
dharma Q&A, trivia list, character quiz) -- genuinely different content
from the Purana Story Shorts (which are narrative stories), per explicit
request (2026-10-02): "ok lets rotate above 6 concepts daily from all 18
puranas in another short between 11 am to 1 pm... select best background
card but should not match with existing short backgrounds also add one
mantra at top realted to that story and rotating srichakra should be
there and border also. text should be compressed upto readable for users
if its still more and occupying copay same text and put it in comment
section while posting".

BACKGROUND: a deep navy-to-violet gradient (COLOR_CONCEPT_TOP/BOTTOM
below) -- deliberately distinct from every other card family on this
channel: Rahu Kalam (red), Shubha Ghadiyalu (green), Durmuhurtham
(amber/brown), Rashi Mantra (green muggu), AND Purana Story Shorts
(indigo-to-MAROON, i.e. ends warm/red). This card stays cool blue-to-violet
throughout -- no warm maroon undertone -- so it reads as its own distinct
visual identity even sitting next to the Purana Story card.

MANTRA AT TOP: every PuranaConceptShort carries its own invocation_te
(a deity-related mantra matching that entry's content), drawn at the top
exactly like the Purana Story card's invocation line.

BORDER + ROTATING SRI CHAKRA: reuses the exact same border-drawing and
chakra-layer-building technique as purana_short_card_renderer.py (same
sri_chakra.py motif, same render_layers() three-layer split so
video/assembler.py's assemble_purana_short_with_rotating_chakra can
animate the chakra on its own layer) -- both explicitly requested again
for this series ("rotating srichakra should be there and border also").

CONCEPT LABEL BADGE: shows CONCEPT_LABEL_TE[concept_type] (e.g. "పుణ్య
క్షేత్రం") instead of an episode-number counter -- this series has no
"story number" concept, each entry is a self-contained concept card.

AUTO-FIT WITH OVERFLOW-TO-COMMENT (the new requirement this series adds,
2026-10-02: "text should be compressed upto readable for users if its
still more and occupying copay same text and put it in comment section
while posting"): body text is shrunk exactly like the Purana Story card's
story text, down to the same legibility floor (BODY_MIN_FONT_FRAC). If it
STILL doesn't fit at the floor size, the card visually truncates what it
shows (ending with an ellipsis "...") rather than silently overflowing
off-frame, and render_layers() sets PuranaConceptCardLayers.truncated=True
plus carries the full, un-truncated body_te through
PuranaConceptCardLayers.full_body_te -- scripts/post_concept_short.py
checks this flag and, when True, posts the full text as a YouTube comment
via YouTubeShortsUploader.post_comment() after a successful upload, so no
content is ever lost even when the card itself can't show all of it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.purana_concept_shorts import CONCEPT_LABEL_TE, PuranaConceptShort
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.layout import vertical_gradient
from mahanavi.images.sri_chakra import draw_sri_chakra_roundel

from mahanavi.images.opinion_line import OPINION_TE
logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# Deep navy-to-violet -- stays cool/blue throughout (no warm maroon
# undertone like the Purana Story card's indigo-to-maroon), and distinct
# from every other card family's palette. See module docstring.
COLOR_CONCEPT_TOP = (8, 22, 58)
COLOR_CONCEPT_BOTTOM = (72, 16, 102)

COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (230, 190, 90)

INVOCATION_FONT_FRAC = 0.046
SERIES_LABEL_FONT_FRAC = 0.040
TITLE_FONT_FRAC = 0.068
BODY_START_FONT_FRAC = 0.050   # starting size the auto-fit shrinks DOWN from
BODY_MIN_FONT_FRAC = 0.028     # legibility floor -- below this, truncate + overflow to comment
SOURCE_FONT_FRAC = 0.030
SUBSCRIBE_FONT_FRAC = 0.038

BODY_LINE_SPACING = 1.3

DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు పురాణ విశేషాల కోసం సబ్‌స్క్రైబ్ చేయండి"

ICON_FRAC = 0.078
ICON_GAP_FRAC = 0.045

# Same border + Sri Chakra watermark technique as purana_short_card_renderer.py
# (see that module's docstring for the full history of fixes to the
# chakra's rotation pivot and loop-seam symmetry -- this card reuses the
# already-fixed motif/approach as-is).
BORDER_OUTER_MARGIN_FRAC = 0.035
BORDER_ACCENT = (230, 190, 90)
CHAKRA_WATERMARK_ALPHA = 110
CHAKRA_ACCENT_RGB = (235, 200, 110)
CHAKRA_RADIUS_FRAC = 0.30
CHAKRA_CENTER_Y_FRAC = 0.42

ELLIPSIS_TE = "..."


@dataclass(frozen=True, slots=True)
class PuranaConceptCard:
    concept: PuranaConceptShort
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PuranaConceptCardLayers:
    """Same three-layer split as PuranaShortCardLayers (see that class's
    docstring for why chakra position/size is tracked separately), plus
    the new overflow-to-comment fields this series adds:

    truncated: True if body_te still didn't fit at the legibility floor,
        meaning the card visually shows an ellipsis-terminated excerpt.
    full_body_te: the COMPLETE, un-truncated original text -- always
        populated (even when truncated is False, for a uniform caller
        contract), so scripts/post_concept_short.py can post it as a
        YouTube comment when truncated is True.
    """
    background_path: Path
    chakra_path: Path
    text_path: Path
    chakra_width: int
    chakra_height: int
    chakra_center_x: int
    chakra_center_y: int
    truncated: bool
    full_body_te: str


class PuranaConceptCardRenderer:
    """Renders a PuranaConceptCard either as one flattened static image
    (render()) or as three separate layers for the rotating-chakra video
    pipeline (render_layers()) -- mirrors PuranaShortCardRenderer's
    structure closely, differing mainly in palette, the concept-label
    badge, and the overflow-to-comment truncation behavior."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: PuranaConceptCard) -> Path:
        background, chakra_img, chakra_cx, chakra_cy, text_layer, _truncated, _full = self._compose(card)
        canvas = background.copy()
        paste_x = chakra_cx - chakra_img.width // 2
        paste_y = chakra_cy - chakra_img.height // 2
        canvas.paste(chakra_img, (paste_x, paste_y), chakra_img)
        canvas.alpha_composite(text_layer)

        output_path = self._build_output_path(card)
        final = canvas.convert("RGB")
        final.save(
            output_path,
            format=self._settings.image_output_format,
            quality=self._settings.image_output_quality,
            optimize=True,
        )
        logger.info("Rendered purana concept card (static) for %s to %s", card.concept.title_en, output_path)
        return output_path

    def render_layers(self, card: PuranaConceptCard) -> PuranaConceptCardLayers:
        background, chakra_img, chakra_cx, chakra_cy, text_layer, truncated, full_body = self._compose(card)

        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        slug = card.concept.title_en.split(" ")[0].lower()
        background_path = self._settings.output_dir / f"purana_concept_{slug}_bg.jpg"
        chakra_path = self._settings.output_dir / f"purana_concept_{slug}_chakra.png"
        text_path = self._settings.output_dir / f"purana_concept_{slug}_text.png"

        background.convert("RGB").save(
            background_path, format="JPEG", quality=self._settings.image_output_quality, optimize=True,
        )
        chakra_img.save(chakra_path, format="PNG")
        text_layer.save(text_path, format="PNG")

        logger.info("Rendered purana concept card layers for %s to %s", card.concept.title_en, self._settings.output_dir)
        return PuranaConceptCardLayers(
            background_path, chakra_path, text_path,
            chakra_width=chakra_img.width, chakra_height=chakra_img.height,
            chakra_center_x=chakra_cx, chakra_center_y=chakra_cy,
            truncated=truncated, full_body_te=full_body,
        )

    def _compose(
        self, card: PuranaConceptCard,
    ) -> tuple[Image.Image, Image.Image, int, int, Image.Image, bool, str]:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.14)  # keeps text clear of Shorts side buttons
        content_width = width - 2 * margin_x

        try:
            background = vertical_gradient(width, height, COLOR_CONCEPT_TOP, COLOR_CONCEPT_BOTTOM).convert("RGBA")
            self._draw_border(background)

            chakra_img, chakra_cx, chakra_cy = self._build_chakra_layer(width, height)

            text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            content_top = int(height * 0.08)
            footer_bottom = int(height * 0.68)

            concept = card.concept
            invocation_font = self._fit_font_to_width(
                draw, concept.invocation_te, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            title_font = self._fit_font_to_width(
                draw, concept.title_te, max_width=content_width,
                start_size=int(width * TITLE_FONT_FRAC), weight="Bold",
            )
            source_font = self._fonts.get_font(size=int(width * SOURCE_FONT_FRAC), weight="Regular")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            series_label = CONCEPT_LABEL_TE[concept.concept_type]
            source_line = f"— {concept.purana_name_te}"

            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            title_h = int(title_font.size * 1.2)
            source_h = int(source_font.size * 1.2)
            subscribe_h = int(subscribe_font.size * 1.15)

            block_gap = int(height * 0.022)
            icon_size = int(width * ICON_FRAC)

            # Fixed engagement line ("comment your opinion on this video") sits at the validated
            # footer_bottom; the subscribe line (and everything above it) moves up by its height.
            opinion_font = self._fit_font_to_width(
                draw, OPINION_TE, max_width=content_width, start_size=int(width * 0.036), weight="Bold",
            )
            opinion_h = int(opinion_font.size * 1.15)
            opinion_top = footer_bottom - opinion_h
            subscribe_top = opinion_top - int(height * 0.012) - subscribe_h
            icon_row_top = subscribe_top - block_gap - icon_size if card.icon_paths else subscribe_top
            source_top = icon_row_top - block_gap - source_h

            body_box_top = (
                content_top + invocation_h + block_gap + series_h + block_gap + title_h + block_gap
            )
            body_box_bottom = source_top - block_gap
            body_box_height = max(body_box_bottom - body_box_top, int(height * 0.1))

            body_font, body_lines, body_block_height, truncated = self._fit_paragraph_to_box(
                draw, concept.body_te, max_width=content_width, max_height=body_box_height,
            )

            body_top = body_box_top + max((body_box_height - body_block_height) // 2, 0)

            cursor_y = content_top
            cursor_y = self._draw_centered_line(
                draw, concept.invocation_te, invocation_font, width, cursor_y, COLOR_GOLD,
            )
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, series_label, series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, concept.title_te, title_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, body_lines, body_font, width, body_top, COLOR_TEXT_LIGHT)

            self._draw_centered_line(draw, source_line, source_font, width, source_top, COLOR_TEXT_LIGHT)

            if card.icon_paths:
                self._draw_icon_row(text_layer, card.icon_paths, width, icon_row_top)

            self._draw_centered_line(draw, card.subscribe_text, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)
            self._draw_centered_line(draw, OPINION_TE, opinion_font, width, opinion_top, COLOR_TEXT_LIGHT)

            if truncated:
                logger.info(
                    "Purana concept card '%s' text truncated on-card at the legibility floor -- "
                    "full text will be posted as a YouTube comment instead.",
                    concept.title_en,
                )

            return background, chakra_img, chakra_cx, chakra_cy, text_layer, truncated, concept.body_te

        except OSError as exc:
            raise ImageRenderError(f"Purana concept card rendering/save failed: {exc}") from exc

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

    def _build_chakra_layer(self, width: int, height: int) -> tuple[Image.Image, int, int]:
        radius = int(width * CHAKRA_RADIUS_FRAC)
        size = int(radius * 2.2)
        chakra_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(chakra_img)
        draw_sri_chakra_roundel(
            draw, center=(size // 2, size // 2), radius=radius,
            accent=(*CHAKRA_ACCENT_RGB, CHAKRA_WATERMARK_ALPHA),
        )
        target_cx = width // 2
        target_cy = int(height * CHAKRA_CENTER_Y_FRAC)
        return chakra_img, target_cx, target_cy

    def _fit_paragraph_to_box(
        self, draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int,
    ) -> tuple["ImageFont.FreeTypeFont", list[str], int, bool]:
        """Same shrink-and-rewrap approach as the Purana Story card's
        _fit_paragraph_to_box, but additionally returns a `truncated`
        flag and, when True, trims `lines` to only what fits max_height
        at the floor size, replacing the tail of the last visible line
        with an ellipsis -- see module docstring for why (overflow goes
        to a YouTube comment instead of being silently clipped)."""
        start_size = int(CARD_WIDTH * BODY_START_FONT_FRAC)
        min_size = int(CARD_WIDTH * BODY_MIN_FONT_FRAC)

        size = start_size
        while size >= min_size:
            font = self._fonts.get_font(size=size, weight="Regular")
            lines = self._wrap_text(draw, text, font, max_width)
            line_height = int(size * BODY_LINE_SPACING)
            total_height = line_height * len(lines)
            if total_height <= max_height:
                return font, lines, total_height, False
            if size == min_size:
                truncated_lines, truncated_height = self._truncate_lines_to_height(
                    lines, line_height, max_height,
                )
                return font, truncated_lines, truncated_height, True
            size -= 2

        # Unreachable in practice (loop always returns at size == min_size).
        font = self._fonts.get_font(size=min_size, weight="Regular")
        lines = self._wrap_text(draw, text, font, max_width)
        line_height = int(min_size * BODY_LINE_SPACING)
        truncated_lines, truncated_height = self._truncate_lines_to_height(lines, line_height, max_height)
        return font, truncated_lines, truncated_height, True

    def _truncate_lines_to_height(
        self, lines: list[str], line_height: int, max_height: int,
    ) -> tuple[list[str], int]:
        max_lines = max(max_height // line_height, 1)
        if max_lines >= len(lines):
            return lines, line_height * len(lines)
        kept = lines[:max_lines]
        last = kept[-1].rstrip()
        # Trim a little room for the ellipsis so it doesn't itself overflow
        # the content width (a few chars is plenty at this font size).
        kept[-1] = (last[:-1] if len(last) > 1 else last) + ELLIPSIS_TE
        return kept, line_height * len(kept)

    def _draw_paragraph(
        self, draw: ImageDraw.ImageDraw, lines: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int, color: tuple[int, int, int],
    ) -> None:
        line_height = int(font.size * BODY_LINE_SPACING)
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
                logger.warning("Could not load purana concept card icon at %s (%s) -- skipping it.", path, exc)

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
        # Hard line breaks ("\n", used by the Q&A / quiz entries) must be
        # split BEFORE word-wrapping: Pillow would otherwise draw a "\n"
        # inside one wrapped "line" and the extra rows would overprint the
        # lines below (the overlap seen on the "What Is Dharma?" Short).
        lines: list[str] = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue
            current = ""
            for word in paragraph.split(" "):
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

    def _build_output_path(self, card: PuranaConceptCard) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        slug = card.concept.title_en.split(" ")[0].lower()
        filename = f"purana_concept_{slug}.{ext}"
        return self._settings.output_dir / filename
