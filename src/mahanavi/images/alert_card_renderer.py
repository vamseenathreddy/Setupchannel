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
from mahanavi.video.watermark import bake_watermark
from mahanavi.images.flow import StickerZone
from mahanavi.images.layout import vertical_gradient

from mahanavi.images.opinion_line import OPINION_TE
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
# Deep amber/orange -- deliberately distinct from Rahu Kalam's red so the
# two "avoid this time" cards don't look identical in the channel's video
# grid, while still reading as a caution color rather than Shubha
# Ghadiyalu's green.
COLOR_DURMUHURTHAM_TOP = (130, 70, 10)
COLOR_DURMUHURTHAM_BOTTOM = (75, 38, 5)
COLOR_TEXT_LIGHT = (255, 250, 240)

ICON_SIZE = int(ALERT_CARD_WIDTH * 0.16)
ICON_GAP = int(ALERT_CARD_WIDTH * 0.06)
ICON_ROW_TOP = int(ALERT_CARD_HEIGHT * 0.06)

# Fixed, generous sizes (fraction of width) -- long content WRAPS instead
# of shrinking these, so a short line always stays this large.
TITLE_FONT_FRAC = 0.10
LABEL_FONT_FRAC = 0.048
VALUE_FONT_FRAC = 0.062
SUBSCRIBE_FONT_FRAC = 0.045
SECONDARY_FONT_FRAC = 0.032  # notably smaller than LABEL_FONT_FRAC -- for de-emphasized extra info
QUOTE_FONT_FRAC = 0.036  # devotional quote, filling the gap above the footer -- see quote_text below
QUOTE_SOURCE_FONT_FRAC = 0.026
COLOR_QUOTE_TEXT = (235, 215, 170)  # soft gold -- distinct from the plain white body text, matches DATE_BADGE_BG tone

# DATE BADGE (replaced plain small date text, 2026-10-02): real channel
# feedback was that every card uses the same template day to day, so a
# returning viewer could mistake today's post for yesterday's at a glance
# -- the date was there, but at DATE_FONT_FRAC=0.042, plain Regular
# weight, same color as everything else, it didn't stand out. Now drawn
# as a solid pill/badge instead of inline text: bigger, bold, and in the
# channel's existing gold accent (same tone as the icons/muggu artwork
# elsewhere), positioned as the very first content element right below
# the icon row -- so it reads clearly even from a single frozen thumbnail
# frame, not just on close viewing. Deliberately NOT animated: animation
# adds real ffmpeg complexity and another failure point, and doesn't even
# help the thumbnail (a single static frame), which is what most viewers
# actually judge before tapping in.
DATE_BADGE_FONT_FRAC = 0.050
DATE_BADGE_BG = (230, 190, 90)   # gold accent, matches the rest of the channel
DATE_BADGE_TEXT = (40, 20, 5)    # dark, for contrast against the gold fill
DATE_BADGE_PAD_X_FRAC = 0.035
DATE_BADGE_PAD_Y_FRAC = 0.012

# Dead in practice -- post_alert_shorts.py always passes an explicit
# subscribe_text from its own rotating per-series pools (see
# _RAHU_KALAM_SUBSCRIBE_LINES etc.), never relies on this default. Kept
# in sync anyway (2026-10-03: added the bell-icon mention, same reason
# as those pools) in case this renderer is ever called directly without
# one.
DEFAULT_SUBSCRIBE_TEXT = "ప్రతిరోజు ముహూర్తాలకొరకు సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి"  # "Subscribe and press the bell icon for daily muhurtams"


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
    comment_prompt_text: str = ""  # optional engagement line, drawn directly ABOVE subscribe_text
    quote_text: str = ""  # optional short devotional quote, filling the gap between the main
    # content and the fixed footer block (see render()'s "quote block" section) -- added
    # 2026-10-04 per explicit request to use that dead space for something devotional rather
    # than leaving it blank on days with short content. Skipped entirely (not shrunk/forced)
    # if there isn't enough vertical room, so it never risks overlapping other text.
    quote_source: str = ""  # short attribution shown smaller, directly below quote_text (e.g. "భగవద్గీత")


class AlertCardRenderer:
    """Renders a single AlertCard to a 9:16 image file."""

    def __init__(self, settings: Settings, font_manager: FontManager | None = None) -> None:
        self._settings = settings
        self._fonts = font_manager or FontManager(settings.telugu_font_path)

    def render(self, card: AlertCard, for_date: date) -> Path:
        width = ALERT_CARD_WIDTH
        height = ALERT_CARD_HEIGHT
        margin_x = int(width * 0.14)  # 2026-10-07: keeps text clear of the Shorts side buttons (x>~940 of 1080)
        content_width = width - 2 * margin_x

        try:
            canvas = bake_watermark(vertical_gradient(width, height, card.top_color, card.bottom_color).convert("RGBA"))
            draw = ImageDraw.Draw(canvas)

            icons_bottom = self._draw_icon_row(canvas, card.icon_paths, width)

            # Fixed element, drawn before the distributed content below
            # (same treatment the icon row already gets) -- NOT part of
            # the shrink-to-fit/gap-distribution math further down, since
            # it has its own fixed size and position rather than flowing
            # with the rest of the card's content.
            badge_top_y = icons_bottom + int(height * 0.035) if icons_bottom else 0
            badge_bottom = self._draw_date_badge(draw, card.date_text, width, content_width, badge_top_y)

            title_font = self._fit_font_to_width(
                draw, card.title, max_width=content_width, start_size=int(width * TITLE_FONT_FRAC), weight="Bold",
            )
            subscribe_font = self._fit_font_to_width(
                draw, card.subscribe_text, max_width=content_width,
                start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )

            title_bbox = draw.textbbox((0, 0), card.title, font=title_font)
            title_h = int(title_bbox[3] - title_bbox[1])

            subscribe_bbox = draw.textbbox((0, 0), card.subscribe_text, font=subscribe_font)
            subscribe_h = int(subscribe_bbox[3] - subscribe_bbox[1])

            # Optional engagement line (e.g. "comment your ishta daivam"),
            # drawn directly above subscribe_text -- same single-line,
            # shrink-to-fit treatment as the subscribe line itself.
            comment_font = None
            comment_bbox = None
            comment_h = 0
            if card.comment_prompt_text:
                comment_font = self._fit_font_to_width(
                    draw, card.comment_prompt_text, max_width=content_width,
                    start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
                )
                comment_bbox = draw.textbbox((0, 0), card.comment_prompt_text, font=comment_font)
                comment_h = int(comment_bbox[3] - comment_bbox[1])

            # Real evidence from the actual mobile app (a screenshot showed
            # our own content overlapping YouTube's channel handle, caption
            # text, and visibility badge) -- those occupy roughly the
            # bottom 25% of the frame, not the ~14% originally assumed.
            # Moved up substantially so ALL our content, not just the
            # subscribe line, finishes well clear of that zone. This is the
            # BOTTOM edge of the footer block (subscribe line, plus the
            # comment line above it when present) -- kept fixed regardless
            # of whether comment_prompt_text is set, so the subscribe line
            # always lands in the same already-validated-safe spot.
            footer_bottom = int(height * 0.68)
            footer_line_gap = int(height * 0.015)
            # Fixed engagement line at the very bottom of the footer block (2026-10-08 request).
            opinion_font = self._fit_font_to_width(
                draw, OPINION_TE, max_width=content_width, start_size=int(width * SUBSCRIBE_FONT_FRAC), weight="Bold",
            )
            zone = StickerZone(height, width - margin_x)

            # Footer lines are bottom-anchored. Any that land in the product-tag sticker zone (lower-left)
            # wrap into the column to its right at the SAME font size instead of shrinking (2026-10-11).
            footer_items = [(OPINION_TE, opinion_font, False), (card.subscribe_text, subscribe_font, False)]
            if card.comment_prompt_text and comment_font is not None:
                footer_items.append((card.comment_prompt_text, comment_font, False))
            footer_lines = [[t] for t, _, _ in footer_items]
            for _ in range(4):
                y_bottom = footer_bottom
                new_lines = []
                for (text, font, _), prev in zip(footer_items, footer_lines):
                    lh = self._line_h(draw, font)
                    top = y_bottom - lh * len(prev)
                    lines = self._wrap_flow(draw, text, font, top, lh, content_width, zone)
                    top = y_bottom - lh * len(lines)
                    lines = self._wrap_flow(draw, text, font, top, lh, content_width, zone)
                    new_lines.append(lines)
                    y_bottom = y_bottom - lh * len(lines) - footer_line_gap
                if new_lines == footer_lines:
                    break
                footer_lines = new_lines
            footer_h = sum(self._line_h(draw, f) * len(ln) for (_, f, _), ln in zip(footer_items, footer_lines)) \
                + footer_line_gap * (len(footer_items) - 1)
            footer_top = footer_bottom - footer_h

            content_top = badge_bottom + int(height * 0.04) if card.date_text else (
                icons_bottom + int(height * 0.05) if icons_bottom else int(height * 0.30)
            )
            available_bottom = footer_top - int(height * 0.03)
            available_height = max(available_bottom - content_top, 0)

            n_gaps = len(card.lines) + 1 + (1 if card.secondary_info else 0)
            min_gap = 2
            line_gap = int(height * 0.012)
            max_gap = int(height * 0.045)

            def plan(font_scale: float, gap: int):
                """Wrap every block at its estimated y (zone-aware) for a given inter-block gap."""
                label_font = self._fonts.get_font(size=max(int(width * LABEL_FONT_FRAC * font_scale), 18), weight="Regular")
                value_font = self._fonts.get_font(size=max(int(width * VALUE_FONT_FRAC * font_scale), 22), weight="Bold")
                secondary_font = self._fonts.get_font(size=max(int(width * SECONDARY_FONT_FRAC * font_scale), 16), weight="Regular")
                y = content_top + title_h + gap
                blocks = []
                for label, value in card.lines:
                    llh, vlh = self._line_h(draw, label_font), self._line_h(draw, value_font)
                    lw = self._wrap_flow(draw, label, label_font, y, llh, content_width, zone)
                    y += llh * len(lw) + line_gap
                    vw = self._wrap_flow(draw, value, value_font, y, vlh, content_width, zone)
                    y += vlh * len(vw) + gap
                    blocks.append((lw, vw))
                sw: list[str] = []
                if card.secondary_info:
                    slh = self._line_h(draw, secondary_font)
                    sw = self._wrap_flow(draw, card.secondary_info, secondary_font, y, slh, content_width, zone)
                fixed = title_h + sum(
                    self._line_h(draw, label_font) * len(lw) + self._line_h(draw, value_font) * len(vw)
                    for lw, vw in blocks
                ) + (self._line_h(draw, secondary_font) * len(sw) if sw else 0)
                return label_font, value_font, secondary_font, blocks, sw, fixed

            # Shrink-to-fit is only the LAST resort now (needed only when even the zone-aware wrap
            # cannot fit): the sticker zone no longer forces smaller text.
            font_scale = 1.0
            gap = max_gap
            while True:
                for _ in range(3):
                    label_font, value_font, secondary_font, blocks, secondary_wrapped, content_fixed_height = plan(font_scale, gap)
                    ideal_gap = (available_height - content_fixed_height) // n_gaps
                    new_gap = max(min(ideal_gap, max_gap), min_gap)
                    if new_gap == gap:
                        break
                    gap = new_gap
                if content_fixed_height + n_gaps * min_gap <= available_height or font_scale <= 0.65:
                    break
                font_scale -= 0.08
                gap = max_gap

            cursor_y = content_top
            title_w = title_bbox[2] - title_bbox[0]
            draw.text(
                ((width - title_w) // 2, cursor_y - title_bbox[1]),
                card.title, font=title_font, fill=COLOR_TEXT_LIGHT,
            )
            cursor_y += title_h + gap

            for label_wrapped, value_wrapped in blocks:
                cursor_y = self._draw_flow_block(draw, label_wrapped, label_font, width, cursor_y, zone)
                cursor_y += line_gap
                cursor_y = self._draw_flow_block(draw, value_wrapped, value_font, width, cursor_y, zone)
                cursor_y += gap

            if card.secondary_info:
                cursor_y = self._draw_flow_block(draw, secondary_wrapped, secondary_font, width, cursor_y, zone)
                cursor_y += gap

            # Devotional quote block: fills whatever room is left between the main content and the
            # footer; skipped (never overlapping) if there isn't room.
            if card.quote_text:
                quote_top_margin = int(height * 0.025)
                quote_block_top = cursor_y + quote_top_margin
                quote_available = footer_top - quote_top_margin - quote_block_top
                if quote_available > int(height * 0.04):  # not worth drawing in a sliver
                    quote_scale = 1.0
                    while quote_scale >= 0.6:
                        quote_font = self._fonts.get_font(
                            size=max(int(width * QUOTE_FONT_FRAC * quote_scale), 16), weight="Medium",
                        )
                        quote_wrapped = self._wrap_flow(
                            draw, card.quote_text, quote_font, quote_block_top, self._line_h(draw, quote_font),
                            int(content_width * 0.9), zone,
                        )
                        quote_h = self._line_h(draw, quote_font) * len(quote_wrapped)

                        source_h = 0
                        source_font = None
                        if card.quote_source:
                            source_font = self._fonts.get_font(
                                size=max(int(width * QUOTE_SOURCE_FONT_FRAC * quote_scale), 14), weight="Regular",
                            )
                            source_bbox = draw.textbbox((0, 0), card.quote_source, font=source_font)
                            source_h = int(source_bbox[3] - source_bbox[1])

                        total_quote_h = quote_h + (int(height * 0.012) + source_h if card.quote_source else 0)
                        if total_quote_h <= quote_available:
                            break
                        quote_scale -= 0.1

                    if total_quote_h <= quote_available:
                        quote_y = self._draw_flow_block(draw, quote_wrapped, quote_font, width, quote_block_top, zone, fill=COLOR_QUOTE_TEXT)
                        if card.quote_source and source_font is not None:
                            quote_y += int(height * 0.012)
                            source_text = f"— {card.quote_source}"
                            source_bbox = draw.textbbox((0, 0), source_text, font=source_font)
                            source_w = source_bbox[2] - source_bbox[0]
                            sx = zone.cx(quote_y, self._line_h(draw, source_font), source_w, width)
                            draw.text(
                                (sx - source_w // 2, quote_y - source_bbox[1]),
                                source_text, font=source_font, fill=COLOR_QUOTE_TEXT,
                            )
                    # else: genuinely no room even at the smallest size -- skip silently.

            y = footer_top
            for (text, font, _), lines in zip(reversed(footer_items), reversed(footer_lines)):
                y = self._draw_flow_block(draw, lines, font, width, y, zone) + footer_line_gap

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

    def _draw_date_badge(
        self, draw: ImageDraw.ImageDraw, date_text: str, width: int, content_width: int, top_y: int,
    ) -> int:
        """Draw the date as a solid gold pill/badge (see DATE_BADGE_* docs
        above) rather than plain inline text, so it reads as a clearly
        distinct element even in a single frozen thumbnail frame. Returns
        the y-coordinate just below the badge (or top_y unchanged if
        date_text is empty, matching _draw_icon_row's "0 if nothing drawn"
        convention)."""
        if not date_text:
            return top_y

        pad_x = int(width * DATE_BADGE_PAD_X_FRAC)
        pad_y = int(width * DATE_BADGE_PAD_Y_FRAC)
        font = self._fit_font_to_width(
            draw, date_text, max_width=content_width - 2 * pad_x,
            start_size=int(width * DATE_BADGE_FONT_FRAC), weight="Bold",
        )
        bbox = draw.textbbox((0, 0), date_text, font=font)
        # PIL's textbbox is typed as returning floats -- cast to int here
        # so badge_w/badge_h (and this function's `-> int` return) stay
        # consistent; pixel coordinates don't need sub-pixel precision.
        text_w = int(bbox[2] - bbox[0])
        text_h = int(bbox[3] - bbox[1])

        badge_w = text_w + 2 * pad_x
        badge_h = text_h + 2 * pad_y
        badge_top = top_y if top_y else ICON_ROW_TOP
        badge_left = (width - badge_w) // 2

        draw.rounded_rectangle(
            [badge_left, badge_top, badge_left + badge_w, badge_top + badge_h],
            radius=badge_h // 2, fill=DATE_BADGE_BG,
        )
        draw.text(
            (badge_left + pad_x, badge_top + pad_y - bbox[1]),
            date_text, font=font, fill=DATE_BADGE_TEXT,
        )
        return badge_top + badge_h

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

    @staticmethod
    def _line_h(draw: ImageDraw.ImageDraw, font: "ImageFont.FreeTypeFont") -> int:
        return int(draw.textbbox((0, 0), "Ag", font=font)[3])

    def _wrap_flow(
        self, draw: ImageDraw.ImageDraw, text: str, font: "ImageFont.FreeTypeFont", y0: int, line_h: int,
        full_w: int, zone: "StickerZone",
    ) -> list[str]:
        """_wrap_text, but rows that fall in the sticker zone use the narrower column. Blocks that never
        touch the zone are wrapped exactly as before."""
        base = self._wrap_text(draw, text, font, full_w)
        if not (y0 + len(base) * line_h > zone.top and y0 < zone.bottom):
            return base
        lines: list[str] = []
        y, current = y0, ""
        for word in text.split(" "):
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            width = zone.width if zone.hits(y, line_h) else full_w
            if (bbox[2] - bbox[0]) <= width or not current:
                current = candidate
            else:
                lines.append(current)
                y += line_h
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_flow_block(
        self, draw: ImageDraw.ImageDraw, wrapped: list[str], font: "ImageFont.FreeTypeFont", width: int,
        top: int, zone: "StickerZone", fill: tuple[int, int, int] = COLOR_TEXT_LIGHT,
    ) -> int:
        line_height = self._line_h(draw, font)
        y = top
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            cx = zone.cx(y, line_height, line_w, width)
            draw.text((cx - line_w // 2, y - bbox[1]), line, font=font, fill=fill)
            y += line_height
        return y

    def _block_height(
        self, draw: ImageDraw.ImageDraw, wrapped: list[str], font: "ImageFont.FreeTypeFont",
    ) -> int:
        """Total rendered height of a wrapped multi-line block."""
        line_height = int(draw.textbbox((0, 0), "Ag", font=font)[3])
        return line_height * len(wrapped)

    def _draw_centered_block(
        self, draw: ImageDraw.ImageDraw, wrapped: list[str], font: "ImageFont.FreeTypeFont",
        width: int, top: int, fill: tuple[int, int, int] = COLOR_TEXT_LIGHT,
    ) -> int:
        """Draw each wrapped line centered horizontally, stacked from
        `top`. Returns the y-coordinate just below the block."""
        line_height = int(draw.textbbox((0, 0), "Ag", font=font)[3])
        y = top
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            draw.text(((width - line_w) // 2, y - bbox[1]), line, font=font, fill=fill)
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
