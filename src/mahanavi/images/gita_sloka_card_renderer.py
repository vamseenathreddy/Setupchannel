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

KRISHNA-ARJUNA BACKGROUND: originally an abstract line-art chariot
silhouette (images/krishna_arjuna_motif.py) drawn as a low-alpha
watermark. Replaced (explicit request, 2026-10-03: "background image i
want to change to this make it faade and text should be visible
cleanly") with the user's own real Krishna-Arjuna chariot artwork
(assets/images/gita_krishna_arjuna_bg.png, settings.
gita_background_image_path) as the actual card background, dimmed
under a dark overlay (_build_background / GITA_BG_OVERLAY_ALPHA below)
so text stays cleanly readable over it. Falls back to the old plain
gradient if that settings path is missing, so the card never breaks if
the asset isn't present.

BORDER: same thin double-line gold border technique used on every other
card on this channel.

AUTO-FIT TEXT: the Sanskrit verse and its Telugu meaning are each
fit-to-box independently (same shrink-and-rewrap approach as
PuranaShortCardRenderer/PuranaConceptCardRenderer), since verse length
varies quite a bit across the Gita.

QUIZ-COMPETITION SUBSCRIBE CTA + "YESTERDAY'S Q&A" REVEAL (explicit
request, 2026-10-03: "pratiroju oka geeta slokam nerchukondi and ma
bhagavadgeetha quiz competion lo participate cheyyataniki subscribe
cheyyandi ... also at bottom ninnati prasna and javabu"):
  - DEFAULT_SUBSCRIBE_TEXT now explicitly mentions the quiz competition
    (not just "subscribe for daily verses"), to tie the verse card back
    to the quiz-day cards (gita_quiz_card_renderer.py) as one series.
  - Every verse-day card (except the very first run ever, when there is
    no previous quiz yet) now also shows, below the subscribe line,
    yesterday's quiz question and its correct answer -- closes the loop
    for anyone who saw yesterday's quiz but didn't go check the earlier
    Short: today's new verse card confirms it for them directly.
    GitaSlokaCard.previous_quiz_sloka carries that target verse; see
    post_gita_sloka_short.py for how it's computed.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.bhagavad_gita_slokas import GitaSloka
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager
from mahanavi.images.layout import vertical_gradient

from mahanavi.images.opinion_line import OPINION_TE
logger = logging.getLogger(__name__)

# Sanskrit danda punctuation ("|" / "||", stored as plain ASCII pipes in
# bhagavad_gita_slokas.py's sanskrit_deva text) read fine in body text,
# but on-card the fit-to-box word-wrapper could push a lone "|" or "||"
# onto its own centered line -- read as a stray typo, not punctuation
# (explicit request, 2026-10-04: "remove that symbol"). strip_danda_marks
# is applied ONLY at card-render call sites below, never to the stored
# text itself -- SEO descriptions (gita_sloka_seo.py) keep the
# traditional danda convention, which reads correctly in plain text.
_DANDA_PATTERN = re.compile(r"[ \t]*\|+[ \t]*")


def strip_danda_marks(text: str) -> str:
    return "\n".join(_DANDA_PATTERN.sub(" ", line).strip() for line in text.split("\n"))

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
SUBSCRIBE_START_FONT_FRAC = 0.038
SUBSCRIBE_MIN_FONT_FRAC = 0.026
YESTERDAY_LABEL_FONT_FRAC = 0.034
YESTERDAY_ANSWER_START_FONT_FRAC = 0.036
YESTERDAY_ANSWER_MIN_FONT_FRAC = 0.026

TEXT_LINE_SPACING = 1.35

# Explicitly mentions the quiz competition (see module docstring) --
# not just a generic "subscribe for daily verses" line.
DEFAULT_SUBSCRIBE_TEXT = (
    "ప్రతిరోజు ఒక గీతా శ్లోకం నేర్చుకోండి — "
    "మా భగవద్గీత క్విజ్ పోటీలో పాల్గొనడానికి సబ్‌స్క్రైబ్ చేయండి!"
)
DEFAULT_INVOCATION = "ఓం శ్రీ కృష్ణాయ నమః"
YESTERDAY_LABEL_TEXT = "నిన్నటి ప్రశ్న & జవాబు"

# Krishna/Vishnu invocation chants, rotated day-to-day instead of always
# showing the single fixed DEFAULT_INVOCATION line above -- explicit
# request, 2026-10-03: "in bhagavadgeetha shorts also rotate krishna
# and vishnu mantras". Krishna is himself the Gita's speaker and a
# Vishnu avatar, so both are in scope for this card's invocation line.
# Same deterministic by-date rotation pattern used everywhere else in
# this codebase (pool[date.toordinal() % len(pool)]).
INVOCATION_POOL = [
    "ఓం శ్రీ కృష్ణాయ నమః",
    "ఓం నమో భగవతే వాసుదేవాయ",
    "హరే కృష్ణ హరే కృష్ణ కృష్ణ కృష్ణ హరే హరే",
    "ఓం నమో నారాయణాయ",
    "ఓం విష్ణవే నమః",
]


def pick_invocation(for_date_ordinal: int) -> str:
    """Deterministic day-to-day rotation through INVOCATION_POOL --
    reproducible for a given date, varies day to day. Used for both
    verse-day (GitaSlokaCard) and quiz-day (GitaQuizCard) cards so the
    whole series rotates together."""
    return INVOCATION_POOL[for_date_ordinal % len(INVOCATION_POOL)]

ICON_FRAC = 0.078
ICON_GAP_FRAC = 0.045

BORDER_OUTER_MARGIN_FRAC = 0.035
BORDER_ACCENT = (230, 190, 90)

# Chariot motif sizing/placement -- see images/krishna_arjuna_motif.py.
# Kept low-alpha, same watermark treatment as the Sri Chakra cards.
# No longer drawn in THIS file (superseded by the real background photo
# below), but these constants stay here since gita_quiz_card_renderer.py
# still imports them for its own (still line-art) watermark.
CHARIOT_ALPHA = 95
CHARIOT_SCALE_FRAC = 0.30       # motif "wheel diameter" as a fraction of card width
CHARIOT_BASELINE_Y_FRAC = 0.655  # where the wheel's bottom sits on the full card

# Real background photo (gita_krishna_arjuna_bg.png) dimmed under a
# flat dark overlay of this alpha so Sanskrit/Telugu text stays cleanly
# readable on top -- explicit request, 2026-10-03: "make it faade and
# text should be visible cleanly". Pure black (not tinted) for maximum,
# unambiguous text contrast regardless of the photo's own colors.
#
# Raised from 165 to 210 per explicit follow-up request (2026-10-03:
# "make gita slokas and quiz bacground image more dark 50% from
# current") -- at alpha=165 the photo showed through at (255-165)/255
# ~= 35% brightness; halving that visible brightness (~35% -> ~17.6%)
# works out to alpha=210. Shared by both the verse card (this file) and
# the quiz card (gita_quiz_card_renderer.py imports this constant), so
# both stay visually consistent.
GITA_BG_OVERLAY_ALPHA = 210


@dataclass(frozen=True, slots=True)
class GitaSlokaCard:
    sloka: GitaSloka
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    icon_paths: list[Path] = field(default_factory=list)
    # The verse the PREVIOUS quiz-day card asked about -- shown at the
    # card's bottom as "yesterday's question & answer" (see module
    # docstring). None only on the very first run ever, when there is
    # no previous quiz to reveal.
    previous_quiz_sloka: GitaSloka | None = None
    # Krishna/Vishnu invocation shown at the very top -- defaults to the
    # original fixed line, but post_gita_sloka_short.py overrides it
    # with pick_invocation(for_date) so it rotates day-to-day.
    invocation_text: str = DEFAULT_INVOCATION


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
        margin_x = int(width * 0.14)  # keeps text clear of Shorts side buttons
        content_width = width - 2 * margin_x

        try:
            canvas = self._build_background(width, height)
            self._draw_border(canvas)

            draw = ImageDraw.Draw(canvas)
            sloka = card.sloka

            content_top = int(height * 0.06)
            footer_bottom = int(height * 0.68)

            invocation_font = self._fit_font_to_width(
                draw, card.invocation_text, max_width=content_width,
                start_size=int(width * INVOCATION_FONT_FRAC), weight="Bold",
            )
            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            badge_text = f"అధ్యాయం {sloka.chapter} • శ్లోకం {sloka.verse} — {sloka.chapter_name_te}"
            badge_font = self._fit_font_to_width(
                draw, badge_text, max_width=content_width,
                start_size=int(width * BADGE_FONT_FRAC), weight="SemiBold",
            )
            source_font = self._fonts.get_font(size=int(width * SOURCE_FONT_FRAC), weight="Regular")
            subscribe_font, subscribe_lines, subscribe_h = self._fit_block_to_box(
                draw, card.subscribe_text, max_width=content_width, max_height=int(height * 0.085),
                start_frac=SUBSCRIBE_START_FONT_FRAC, min_frac=SUBSCRIBE_MIN_FONT_FRAC,
            )

            source_line = "— భగవద్గీత"

            invocation_h = int(invocation_font.size * 1.2)
            series_h = int(series_font.size * 1.2)
            badge_h = int(badge_font.size * 1.2)
            source_h = int(source_font.size * 1.2)

            block_gap = int(height * 0.020)
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
                draw, strip_danda_marks(sloka.sanskrit_deva), max_width=content_width, max_height=sanskrit_box_height,
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
            cursor_y = self._draw_centered_line(draw, card.invocation_text, invocation_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            cursor_y = self._draw_centered_line(draw, "నేటి గీతా శ్లోకం", series_font, width, cursor_y, COLOR_GOLD)
            cursor_y += block_gap
            self._draw_centered_line(draw, badge_text, badge_font, width, cursor_y, COLOR_TEXT_LIGHT)

            self._draw_paragraph(draw, sanskrit_lines, sanskrit_font, width, sanskrit_top, COLOR_GOLD)
            self._draw_paragraph(draw, meaning_lines, meaning_font, width, meaning_top, COLOR_TEXT_LIGHT)

            self._draw_centered_line(draw, source_line, source_font, width, source_top, COLOR_TEXT_LIGHT)

            if card.icon_paths:
                self._draw_icon_row(canvas, card.icon_paths, width, icon_row_top)

            self._draw_paragraph(draw, subscribe_lines, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)
            self._draw_centered_line(draw, OPINION_TE, opinion_font, width, opinion_top, COLOR_TEXT_LIGHT)

            if card.previous_quiz_sloka is not None:
                self._draw_yesterday_block(draw, card.previous_quiz_sloka, width, content_width, footer_bottom, block_gap)

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

    def _draw_yesterday_block(
        self, draw: ImageDraw.ImageDraw, previous: GitaSloka, width: int, content_width: int,
        footer_bottom: int, block_gap: int,
    ) -> None:
        """Drawn BELOW footer_bottom, in the card's lower margin (every
        other card family on this channel leaves that space blank) --
        reveals yesterday's quiz question and its correct answer. See
        module docstring."""
        label_font = self._fonts.get_font(size=int(width * YESTERDAY_LABEL_FONT_FRAC), weight="SemiBold")
        answer_text = (
            f"ప్రశ్న: ఏ అధ్యాయంలోనిది? — జవాబు: అధ్యాయం {previous.chapter}, శ్లోకం {previous.verse}"
        )
        answer_font, answer_lines, answer_h = self._fit_block_to_box(
            draw, answer_text, max_width=content_width, max_height=int(width * 0.12),
            start_frac=YESTERDAY_ANSWER_START_FONT_FRAC, min_frac=YESTERDAY_ANSWER_MIN_FONT_FRAC,
        )

        top = footer_bottom + block_gap
        top = self._draw_centered_line(draw, YESTERDAY_LABEL_TEXT, label_font, width, top, COLOR_GOLD)
        self._draw_paragraph(draw, answer_lines, answer_font, width, top, COLOR_TEXT_LIGHT)

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
        """Real Krishna-Arjuna artwork, cover-fit to the card and dimmed
        under a flat dark overlay so text stays readable -- falls back
        to the plain gradient if the configured image is missing/
        unreadable, so a missing asset never breaks the render."""
        bg_path = self._settings.gita_background_image_path
        if bg_path is not None and bg_path.exists():
            try:
                with Image.open(bg_path) as raw:
                    fitted = ImageOps.fit(raw.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
                canvas = fitted.convert("RGBA")
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, GITA_BG_OVERLAY_ALPHA))
                return Image.alpha_composite(canvas, overlay)
            except (OSError, UnidentifiedImageError) as exc:
                logger.warning(
                    "Could not load Gita background image at %s (%s) -- falling back to plain gradient.",
                    bg_path, exc,
                )
        return vertical_gradient(width, height, COLOR_GITA_TOP, COLOR_GITA_BOTTOM).convert("RGBA")

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
