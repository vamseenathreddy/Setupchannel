"""
RashiCardRenderer: renders one "Rashi Mantra of the Month" Short -- a
static (non-scrolling) traditional green card with a muggu/kolam roundel,
showing one rashi's name, ruling planet, chanting mantra, chant count,
and a one-line benefit.

BACKGROUND: loaded from Images/RashiMantra/backgrounds/bg_{1,2,3}.png,
pre-generated once by scripts/generate_rashi_backgrounds.py (programmatic
PIL artwork -- see that script's docstring for why it's generated rather
than sourced, i.e. the copyright concern raised for this series). Which
of the 3 backgrounds a given rashi gets is picked deterministically by
rashi index (index % 3), so the same rashi always gets the same
background across re-posts, while the 12-rashi rotation still shows all
3 variants.

STATIC, NOT SCROLLING: per explicit request ("no need to read") -- this
is a single still frame held for the Short's duration (see
video/assembler.py's static-frame path, the same one the alert Shorts
use), not the scrolling-text treatment purana_text_renderer.py uses for
long story narration. A rashi card's content is short enough to read at
a glance.

SAFE ZONES: reuses the same two pieces of real-world evidence already
encoded in alert_card_renderer.py -- a real screenshot of a posted Short
showed YouTube's own UI (channel handle, caption, visibility badge)
occupying roughly the bottom 25% of the frame, and the right-hand
like/comment/share rail sits in a narrow column on the right edge. This
renderer keeps all text centered within an 84%-width column (8% margin
each side, comfortably clear of the right-edge icon rail) and finishes
all content at or above height*0.68, matching the alert cards' validated
footer boundary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from mahanavi.config import Settings
from mahanavi.content.rashi_mantra_content import RashiMantraContent
from mahanavi.exceptions import ImageRenderError
from mahanavi.images.fonts import FontManager

logger = logging.getLogger(__name__)

CARD_WIDTH = 1080
CARD_HEIGHT = 1920

BACKGROUNDS_DIR = Path(__file__).resolve().parents[3] / "Images" / "RashiMantra" / "backgrounds"
BACKGROUND_FILENAMES = ["bg_1.png", "bg_2.png", "bg_3.png"]

COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (230, 190, 90)

# Fixed, generous sizes (fraction of width) -- same "wrap, don't shrink
# the whole card" philosophy as alert_card_renderer.py.
SERIES_LABEL_FONT_FRAC = 0.040
RASHI_NAME_FONT_FRAC = 0.115
PLANET_FONT_FRAC = 0.048
MANTRA_FONT_FRAC = 0.072
CHANT_COUNT_FONT_FRAC = 0.040
BENEFIT_FONT_FRAC = 0.044
SUBSCRIBE_FONT_FRAC = 0.040
COMMENT_FONT_FRAC = 0.040

DEFAULT_SUBSCRIBE_TEXT = "మీ రాశి మంత్రం కోసం సబ్‌స్క్రైబ్ చేయండి"  # "Subscribe for your rashi's mantra"

# Reference strings used to pick ONE shared font size across all 12
# cards (see the comment at mantra_font/name_font below for why
# per-card fitting was wrong). Longest by character count among
# RASHI_MANTRAS as of 2026-10 -- Karkataka/Vrishchika tie for name,
# Mesha/Vrishchika/Dhanussu/Meena tie for mantra.
LONGEST_RASHI_NAME_TE = "కర్కాటకం"
LONGEST_MANTRA_TE = "ఓం బృహస్పతయే నమః"


@dataclass(frozen=True, slots=True)
class RashiCard:
    content: RashiMantraContent
    rashi_index: int  # 0-11, position in RASHI_MANTRAS -- picks the background variant
    date_text: str = ""  # e.g. "అక్టోబర్ 2026 మాసం" (this month)
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    comment_prompt_text: str = ""


class RashiCardRenderer:
    """Renders a single RashiCard to a static 9:16 image file."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: RashiCard) -> Path:
        width, height = CARD_WIDTH, CARD_HEIGHT
        margin_x = int(width * 0.08)
        content_width = width - 2 * margin_x

        try:
            canvas = self._load_background(card.rashi_index).convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            # Content starts below the muggu roundel (drawn by the
            # background generator up to roughly height*0.26) and must
            # finish, including the subscribe/comment footer, at or
            # above height*0.68 -- same validated boundary as the alert
            # cards, which share this channel's Shorts UI overlay.
            content_top = int(height * 0.27)
            footer_bottom = int(height * 0.68)

            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            # Same shared-size reasoning as mantra_font below: fit to the
            # longest rashi NAME, not this card's own (shorter names would
            # otherwise render larger and shift every line below them up,
            # making content height inconsistent across the 12 cards).
            name_font = self._fit_font_to_width(
                draw, LONGEST_RASHI_NAME_TE, max_width=content_width,
                start_size=int(width * RASHI_NAME_FONT_FRAC), weight="Bold",
            )
            planet_font = self._fonts.get_font(size=int(width * PLANET_FONT_FRAC), weight="Regular")
            # Fit to the LONGEST mantra across all 12 rashis, not this
            # card's own mantra text, and use that same size for every
            # card. Fitting per-card let a short mantra (e.g. Karkataka's
            # "ఓం చంద్రాయ నమః") render at the full un-shrunk start size --
            # taller than a long one -- so the fixed-position footer below
            # it ended up overlapped on some rashis but not others
            # (confirmed via a real render: Mesha's longer mantra fit fine,
            # Karkataka's shorter one visibly overlapped the footer).
            # One shared size keeps every card's content height identical.
            mantra_font = self._fit_font_to_width(
                draw, LONGEST_MANTRA_TE, max_width=content_width,
                start_size=int(width * MANTRA_FONT_FRAC), weight="Bold", min_size=36,
            )
            chant_font = self._fonts.get_font(size=int(width * CHANT_COUNT_FONT_FRAC), weight="Regular")
            benefit_font = self._fonts.get_font(size=int(width * BENEFIT_FONT_FRAC), weight="Regular")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            series_label = "ఈ నెల రాశి మంత్రం"  # "This month's rashi mantra"

            lines: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]] = [
                (series_label, series_font, COLOR_GOLD),
                (card.content.name_te, name_font, COLOR_TEXT_LIGHT),
                (f"అధిపతి: {card.content.ruling_planet_te}", planet_font, COLOR_TEXT_LIGHT),
            ]

            comment_font = None
            if card.comment_prompt_text:
                comment_font = self._fit_font_to_width(
                    draw, card.comment_prompt_text, max_width=content_width,
                    start_size=int(width * COMMENT_FONT_FRAC), weight="Bold",
                )

            # Footer block (comment prompt + subscribe) is anchored to the
            # fixed, validated footer_bottom boundary -- it never moves
            # regardless of how tall the content above is.
            # Same font-size-based line height as _draw_centered_line, for
            # the same reason -- consistent regardless of which glyphs a
            # given subscribe/comment string happens to contain.
            subscribe_h = int(subscribe_font.size * 1.15)
            footer_line_gap = int(height * 0.015)

            comment_h = 0
            if card.comment_prompt_text and comment_font is not None:
                comment_h = int(comment_font.size * 1.15)

            # Measured against the real numbers that caused the overlap
            # bug above (content reached y=1238 while the footer's
            # comment line started at y=1179 -- a 59px collision, true
            # for every rashi since these sizes/gaps don't vary by card):
            # content_top moved up (0.30 -> 0.27, roundel still clears
            # with margin) and these two gaps tightened, together freeing
            # ~115px -- confirmed by rendering the three cards that
            # previously overlapped most (longest name, longest and
            # shortest mantra) after this change.
            gap = int(height * 0.022)
            mantra_block_gap = int(height * 0.035)

            # Deliberately NOT showing the benefit line on the card itself
            # -- an earlier version with 6 stacked text blocks plus a
            # 2-line footer needed its font shrunk so far to fit above
            # footer_top that it became barely legible and still nearly
            # touched the footer (confirmed via a real render). The benefit
            # text is still used in the Short's description/SEO instead --
            # see rashi_mantra_seo.py. Card content is now just: series
            # label, rashi name, ruling planet, mantra, chant count --
            # fits comfortably with room to spare, matching how the
            # competitor cards researched for this series stay punchy.
            cursor_y = content_top
            for text, font, color in lines:
                cursor_y = self._draw_centered_line(draw, text, font, width, cursor_y, color)
                cursor_y += gap

            cursor_y += mantra_block_gap
            cursor_y = self._draw_centered_line(draw, card.content.mantra_te, mantra_font, width, cursor_y, COLOR_GOLD)
            cursor_y += int(gap * 0.6)
            cursor_y = self._draw_centered_line(
                draw, f"({card.content.chant_count_te})", chant_font, width, cursor_y, COLOR_TEXT_LIGHT,
            )

            # Footer: comment prompt (optional) then subscribe, drawn at
            # the fixed boundary.
            subscribe_top = footer_bottom - subscribe_h
            self._draw_centered_line(draw, card.subscribe_text, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)

            if card.comment_prompt_text and comment_font is not None:
                comment_top = subscribe_top - footer_line_gap - comment_h
                self._draw_centered_line(draw, card.comment_prompt_text, comment_font, width, comment_top, COLOR_TEXT_LIGHT)

            output_path = self._build_output_path(card)
            final = canvas.convert("RGB")
            final.save(
                output_path,
                format=self._settings.image_output_format,
                quality=self._settings.image_output_quality,
                optimize=True,
            )
            logger.info("Rendered rashi card for %s to %s", card.content.name_en, output_path)
            return output_path

        except OSError as exc:
            raise ImageRenderError(f"Rashi card rendering/save failed: {exc}") from exc

    def _load_background(self, rashi_index: int) -> Image.Image:
        filename = BACKGROUND_FILENAMES[rashi_index % len(BACKGROUND_FILENAMES)]
        path = BACKGROUNDS_DIR / filename
        if not path.exists():
            raise ImageRenderError(
                f"Rashi background not found at {path}. "
                "Run scripts/generate_rashi_backgrounds.py first."
            )
        with Image.open(path) as raw:
            return raw.copy()

    def _wrap_text(
        self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", max_width: int,
    ) -> list[str]:
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
        """Draw one centered line at `top`. Returns the y-coordinate just
        below it, advanced by a FONT-SIZE-based line height rather than
        this specific text's own glyph ink extent.

        Why: measuring each line's vertical advance from its own
        draw.textbbox() seemed reasonable, but a real render comparing
        రాశి names of equal font size showed different ink-extent heights
        per string (e.g. "కర్కాటకం", with a stacked ర్క conjunct, measures
        taller than "మేషం") -- so two cards at IDENTICAL font sizes ended
        up with different total content heights, and since the footer
        below is anchored to a fixed boundary, some rashis' content ran
        into it while others didn't. A size-based estimate (~1.15x the
        font's point size, the usual single-line-height rule of thumb)
        gives every line the same vertical rhythm regardless of which
        glyphs happen to be in it.
        """
        bbox = draw.textbbox((0, 0), text, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text(((width - line_w) // 2, top - bbox[1]), text, font=font, fill=color)
        line_height = int(font.size * 1.15)
        return top + line_height

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

    def _build_output_path(self, card: RashiCard) -> Path:
        self._settings.output_dir.mkdir(parents=True, exist_ok=True)
        ext = "jpg" if self._settings.image_output_format.upper() == "JPEG" else self._settings.image_output_format.lower()
        slug = card.content.name_en.split(" ")[0].lower()
        filename = f"rashi_mantra_{slug}.{ext}"
        return self._settings.output_dir / filename
