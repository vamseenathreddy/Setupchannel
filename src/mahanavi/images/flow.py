"""Keep card text out of the YouTube Shopping product-tag sticker (lower-left of a Short).

Rows that touch the zone are wrapped into, and centred in, the column to its right -- same font size,
so nothing shrinks. See layout.PRODUCT_ZONE_* for the measured geometry.
"""
from __future__ import annotations

from collections.abc import Callable

from PIL import ImageDraw, ImageFont

from mahanavi.images.layout import PRODUCT_ZONE_BOTTOM_FRAC, PRODUCT_ZONE_TOP_FRAC, PRODUCT_ZONE_X1_FRAC

CARD_W = 1080


class StickerZone:
    """Lower-left rectangle YouTube's Shopping "Shop" sticker covers (see layout.PRODUCT_ZONE_*).
    Text lines whose rows touch it are centred in the column to its right instead."""

    def __init__(self, height: int, right_edge: int, card_w: int = CARD_W) -> None:
        self.top = int(height * PRODUCT_ZONE_TOP_FRAC) - 8
        self.bottom = int(height * PRODUCT_ZONE_BOTTOM_FRAC)
        self.left = int(card_w * PRODUCT_ZONE_X1_FRAC) + 30
        self.right = right_edge
        self.width = self.right - self.left
        self.centre = (self.left + self.right) // 2

    def hits(self, y: float, line_h: int) -> bool:
        return y + line_h > self.top and y < self.bottom

    def cx(self, y: float, line_h: int, line_w: float, width: int) -> int:
        if self.hits(y, line_h) and line_w <= self.width + 4:
            return self.centre
        return width // 2


def wrap_block(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, full_w: int, y0: int, line_h: int,
    zone: StickerZone, plain_wrap: Callable[[str], list[str]],
) -> list[str]:
    """Wrap a (possibly \\n-separated) block; rows in the zone use the narrow column. Paragraphs/blocks that
    never touch the zone keep the caller's normal wrap (plain_wrap, applied per paragraph)."""
    base: list[str] = []
    for para in text.split("\n"):
        base.extend(plain_wrap(para))
    if not (y0 + len(base) * line_h > zone.top and y0 < zone.bottom):
        return base
    lines: list[str] = []
    y = y0
    for para in text.split("\n"):
        current = ""
        for word in para.split(" "):
            cand = f"{current} {word}".strip()
            w = draw.textbbox((0, 0), cand, font=font)
            width = zone.width if zone.hits(y, line_h) else full_w
            if (w[2] - w[0]) <= width or not current:
                current = cand
            else:
                lines.append(current)
                y += line_h
                current = word
        if current:
            lines.append(current)
            y += line_h
    return lines
