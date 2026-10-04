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
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mahanavi.config import Settings
from mahanavi.content.rashi_current_transits import AFFECTED_RASHIS, SHANI_REMEDY_CHANT_COUNT_TE, SHANI_REMEDY_MANTRA_TE
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
# the whole card" philosophy as alert_card_renderer.py. Trimmed from an
# earlier pass (name 0.115->0.090, mantra 0.072->0.065) to make room for
# the deity icon row added below the mantra per explicit request -- the
# card was already near its vertical budget before that addition.
#
# RAISED AGAIN 2026-10-04 (explicit request: "mostly our devotional
# channel visitors are big [elderly] people, they may have eye issues" --
# bigger text across the board, mantra especially, "it will help
# readers"). This only has room because ENGLISH_NAME_FONT_FRAC below
# (one new line) made the content block taller too, and the capped-gap
# fix further down turns the previously-wasted leftover space into
# legitimate room for both. Verified via real renders (both the
# longest-name/longest-mantra worst case and a Shani-affected rashi
# with the extra status line) that nothing overflows into the icon row.
SERIES_LABEL_FONT_FRAC = 0.040
RASHI_NAME_FONT_FRAC = 0.082
ENGLISH_NAME_FONT_FRAC = 0.042  # new: English zodiac name shown under the Telugu name
PLANET_FONT_FRAC = 0.048
# Mantra now shares RASHI_NAME_FONT_FRAC as its start size (explicit
# request 2026-10-04: "same size as karkatakam") -- no separate fraction.
CHANT_COUNT_FONT_FRAC = 0.040
# Shown on EVERY card now (explicit request 2026-10-04: "we have to give
# benefits of reading it... if it's bad time it will be stable, or if
# it's good then get more benefits") -- the benefit and the chant count
# are drawn as ONE combined sentence at this same CHANT_COUNT_FONT_FRAC
# size (explicit follow-up request: "in same 108 sarlu size"), e.g.
# "మనశ్శాంతి, కుటుంబ సౌఖ్యం కోసం 108 సార్లు చదువుకోండి" -- not two
# separate lines at two different sizes. Unaffected rashis use
# content.benefit_te (the traditional benefit of their ruling-planet
# mantra); the 5 Shani-affected rashis use transit.note_te instead (the
# relief-focused framing for their harder period) -- see the
# mantra_text/benefit_text selection below. Wrapped to 1-2 lines via
# _wrap_text since the combined sentence runs long, especially for the
# Shani-affected rashis.
SUBSCRIBE_FONT_FRAC = 0.042
COMMENT_FONT_FRAC = 0.042

# "ప్రతి నెల మీ రాశి మంత్రం కోసం సబ్‌స్క్రైబ్ చేయండి" -- exact phrasing
# requested ("prathi nela me raasi mantram kosam subscribe cheyyandi"),
# i.e. "Every month, subscribe for your rashi's mantra" -- names this as
# a recurring monthly series rather than a one-off post.
DEFAULT_SUBSCRIBE_TEXT = "ప్రతి నెల మీ రాశి మంత్రం కోసం సబ్‌స్క్రైబ్ చేయండి"

ICON_FRAC = 0.068  # deity icon size, fraction of width -- trimmed from
# 0.078 to free vertical room for the merged benefit+chant-count line
# (see gap/mantra_block_gap below, same reason)
ICON_GAP_FRAC = 0.045

# Reference strings used to pick ONE shared font size across all 12
# cards (see the comment at mantra_font/name_font below for why
# per-card fitting was wrong). Longest by character count among
# RASHI_MANTRAS as of 2026-10 -- Karkataka/Vrishchika tie for name,
# Mesha/Vrishchika/Dhanussu/Meena tie for mantra.
LONGEST_RASHI_NAME_TE = "కర్కాటకం"
LONGEST_NAME_EN = "Dhanussu (Sagittarius)"
# Now the longer of the two mantra pools this card can show: a
# ruling-planet mantra, or (for a Shani-affected rashi) the Shani remedy
# mantra from rashi_current_transits.py, which is the longest of all.
LONGEST_MANTRA_TE = "ఓం ప్రాం ప్రీం ప్రౌం సః శనయే నమః"


@dataclass(frozen=True, slots=True)
class RashiCard:
    content: RashiMantraContent
    rashi_index: int  # 0-11, position in RASHI_MANTRAS -- picks the background variant
    date_text: str = ""  # e.g. "అక్టోబర్ 2026 మాసం" (this month)
    subscribe_text: str = DEFAULT_SUBSCRIBE_TEXT
    comment_prompt_text: str = ""
    icon_paths: list[Path] = field(default_factory=list)  # e.g. [Lakshmi, Ganesha, Kubera], left-to-right


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

            # Content starts just below the muggu roundel (drawn by the
            # background generator up to roughly height*0.244) and must
            # finish, including the icon row and the subscribe/comment
            # footer, at or above height*0.68 -- same validated boundary
            # as the alert cards, which share this channel's Shorts UI
            # overlay.
            content_top = int(height * 0.25)
            footer_bottom = int(height * 0.68)

            # Transit-aware mantra selection ("this mantra should change
            # for them according [to] sani and other situation" --
            # explicit request): a rashi currently under Sade Sati,
            # Ashtama Shani, or Kantaka Shani (see
            # rashi_current_transits.py) gets the classic Shani remedy
            # mantra instead of its usual ruling-planet one, with
            # transit.note_te as its on-card benefit line (relief-framed
            # for a harder period) instead of the usual benefit_te
            # (more-good-fortune framed, for an unaffected rashi).
            transit = AFFECTED_RASHIS.get(card.content.name_en)
            if transit is not None:
                mantra_text = SHANI_REMEDY_MANTRA_TE
                chant_count_text = SHANI_REMEDY_CHANT_COUNT_TE
                benefit_text = transit.note_te
            else:
                mantra_text = card.content.mantra_te
                chant_count_text = card.content.chant_count_te
                benefit_text = card.content.benefit_te

            series_font = self._fonts.get_font(size=int(width * SERIES_LABEL_FONT_FRAC), weight="SemiBold")
            # Same shared-size reasoning as mantra_font below: fit to the
            # longest rashi NAME, not this card's own (shorter names would
            # otherwise render larger and shift every line below them up,
            # making content height inconsistent across the 12 cards).
            name_font = self._fit_font_to_width(
                draw, LONGEST_RASHI_NAME_TE, max_width=content_width,
                start_size=int(width * RASHI_NAME_FONT_FRAC), weight="Bold",
            )
            # English zodiac name under the Telugu one (added 2026-10-04,
            # explicit request -- the card previously showed no English
            # anywhere, which a non-Telugu-script-fluent viewer or search
            # thumbnail glance couldn't anchor on). content.name_en already
            # existed (used for file-naming/matching) but was never drawn.
            english_name_font = self._fit_font_to_width(
                draw, LONGEST_NAME_EN, max_width=content_width,
                start_size=int(width * ENGLISH_NAME_FONT_FRAC), weight="Medium", min_size=28,
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
            # Explicit request 2026-10-04: same size as the rashi name
            # (RASHI_NAME_FONT_FRAC), not its own smaller MANTRA_FONT_FRAC
            # -- still fit-to-width against the longest mantra across all
            # 12 rashis, same reasoning as before (one shared size keeps
            # every card's content height identical).
            mantra_font = self._fit_font_to_width(
                draw, LONGEST_MANTRA_TE, max_width=content_width,
                start_size=int(width * RASHI_NAME_FONT_FRAC), weight="Bold", min_size=36,
            )
            chant_font = self._fonts.get_font(size=int(width * CHANT_COUNT_FONT_FRAC), weight="Regular")
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            series_label = "ఈ నెల రాశి మంత్రం"  # "This month's rashi mantra"

            lines: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]] = [
                (series_label, series_font, COLOR_GOLD),
                (card.content.name_te, name_font, COLOR_TEXT_LIGHT),
                (card.content.name_en, english_name_font, COLOR_GOLD),
                (f"అధిపతి: {card.content.ruling_planet_te}", planet_font, COLOR_TEXT_LIGHT),
            ]

            comment_font = None
            if card.comment_prompt_text:
                comment_font = self._fit_font_to_width(
                    draw, card.comment_prompt_text, max_width=content_width,
                    start_size=int(width * COMMENT_FONT_FRAC), weight="Bold",
                )

            # Font-size-based line height, same reasoning as
            # _draw_centered_line -- consistent regardless of which
            # glyphs a given string happens to contain.
            subscribe_h = int(subscribe_font.size * 1.15)
            footer_line_gap = int(height * 0.015)
            comment_h = int(comment_font.size * 1.15) if (card.comment_prompt_text and comment_font is not None) else 0
            icon_size = int(width * ICON_FRAC)

            # Both trimmed (0.014->0.009, 0.020->0.013) to free vertical
            # room for the merged benefit+chant-count line -- it now runs
            # noticeably taller than the old two-line (small benefit +
            # chant count) layout, especially for the 3 Shani-affected
            # rashis whose combined sentence wraps to 2 lines at this
            # bigger font size (confirmed via a real render that showed
            # up to 54px of overflow before this trim).
            gap = int(height * 0.009)
            mantra_block_gap = int(height * 0.013)

            # EVERYTHING below content_top is now anchored bottom-up from
            # the fixed, validated footer_bottom boundary -- subscribe,
            # then comment (if any), then the icon row (if any) above
            # that. This replaced an earlier version where the icon row
            # was drawn wherever the content above happened to end,
            # independent of the footer's own fixed position -- a real
            # render showed the icon row landing on top of both the
            # comment line above it and the subscribe line below it,
            # because nothing reserved it a slot. Computing the whole
            # footer stack first, then handing the content above
            # whatever vertical space is LEFT, is the same fix already
            # applied once to the comment/subscribe pair -- just
            # extended to cover the icon row too.
            subscribe_top = footer_bottom - subscribe_h
            comment_top = subscribe_top - footer_line_gap - comment_h if card.comment_prompt_text else subscribe_top
            icon_row_top = comment_top - mantra_block_gap - icon_size if card.icon_paths else comment_top
            content_bottom_limit = icon_row_top

            # The benefit line WAS deliberately left off the card (an
            # earlier version with 6 stacked text blocks plus a 2-line
            # footer needed its font shrunk so far to fit above footer_top
            # that it became barely legible). Brought back 2026-10-04 per
            # explicit request ("we have to give benefits of reading it")
            # -- the recent font-size increases made the card run close to
            # its vertical budget again, so this is wrapped to 1-2 lines
            # at a small, fixed size rather than drawn as one unbroken
            # line, and still finishes at or above content_bottom_limit
            # (verified via a real render of all 12 rashis, including the
            # 5 Shani-affected ones whose benefit line -- transit.note_te
            # -- runs noticeably longer than the other 7's benefit_te).
            # Card content is now: series label, rashi name, English
            # name, ruling planet, mantra, chant count, and the benefit
            # line -- all finishing at or above content_bottom_limit,
            # with the icon row and footer below it.
            cursor_y = content_top
            for text, font, color in lines:
                cursor_y = self._draw_centered_line(draw, text, font, width, cursor_y, color)
                cursor_y += gap

            cursor_y += mantra_block_gap
            cursor_y = self._draw_centered_line(draw, mantra_text, mantra_font, width, cursor_y, COLOR_TEXT_LIGHT)
            cursor_y += int(gap * 0.4)

            # Benefit + chant-count merged into one sentence (explicit
            # request 2026-10-04), e.g. "మనశ్శాంతి, కుటుంబ సౌఖ్యం కోసం 108
            # సార్లు చదువుకోండి" -- "చదువుకోండి" (recite/read) is inserted
            # right after "సార్లు" so a chant_count_text with a trailing
            # clause (the Shani remedy's "..., శనివారం ఉత్తమం") still
            # reads naturally: "...108 సార్లు చదువుకోండి, శనివారం ఉత్తమం".
            if "సార్లు" in chant_count_text:
                chant_with_prompt = chant_count_text.replace("సార్లు", "సార్లు చదువుకోండి", 1)
            else:
                chant_with_prompt = f"{chant_count_text} చదువుకోండి"
            combined_text = f"{benefit_text} {chant_with_prompt}" if benefit_text else chant_with_prompt

            for combined_line in self._wrap_text(draw, combined_text, chant_font, content_width):
                cursor_y = self._draw_centered_line(draw, combined_line, chant_font, width, cursor_y, COLOR_GOLD)

            if cursor_y > content_bottom_limit:
                logger.warning(
                    "Rashi card content for %s ran %dpx past its budget (cursor_y=%d, limit=%d) -- "
                    "may visually crowd the icon row/footer. Check gaps/font fractions if this recurs.",
                    card.content.name_en, cursor_y - content_bottom_limit, cursor_y, content_bottom_limit,
                )

            if card.icon_paths:
                self._draw_icon_row(canvas, card.icon_paths, width, icon_row_top)

            self._draw_centered_line(draw, card.subscribe_text, subscribe_font, width, subscribe_top, COLOR_TEXT_LIGHT)
            if card.comment_prompt_text and comment_font is not None:
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

    def _draw_icon_row(self, canvas: Image.Image, icon_paths: list[Path], width: int, top: int) -> None:
        """Paste up to 3 deity icons (e.g. Lakshmi, Ganesha, Kubera) in a
        centered horizontal row at `top` -- same icon-row technique as
        alert_card_renderer.py's _draw_icon_row, reused here per explicit
        request to add them to this card too."""
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
                logger.warning("Could not load rashi card icon at %s (%s) -- skipping it.", path, exc)

        if not icons:
            return

        total_w = sum(icon.width for icon in icons) + icon_gap * (len(icons) - 1)
        x = (width - total_w) // 2
        max_h = max(icon.height for icon in icons)

        for icon in icons:
            y = top + (max_h - icon.height) // 2
            canvas.alpha_composite(icon, (x, y))
            x += icon.width + icon_gap

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
