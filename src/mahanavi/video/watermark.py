"""
Channel-handle watermark for the card Shorts.

Per explicit request (2026-10-07): "add a watermark of that channel's
short. Users should not copy but readers should not feel inconvenient."

Design (revised 2026-10-07 after review of the first version): one LARGE,
very dim (~15%) "@MahanaviSpirituals" at the exact vertical middle of the
frame, deliberately overlapping the text. Being in the middle of the
content it cannot be cropped out, while its low brightness keeps it from
distracting a reader. The same look is used for every channel in this repo
(Ramana Maharshi TV -> @ramanamaharshitv; engine channels -> their handle,
or channel name until one is set).

Two full-frame transparent PNG layers (one per position) are generated
once and overlaid by ffmpeg with an `enable` time window each.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw

from mahanavi.images.fonts import FontManager

logger = logging.getLogger(__name__)

WATERMARK_TEXT = "@MahanaviSpirituals"
FRAME_W, FRAME_H = 1080, 1920
FONT_SIZE = 76
# (center_y) of each position: top margin (inside the card border, above the
# invocation line) and lower-middle (below the subscribe line, above YouTube's
# bottom caption area).
POSITIONS_Y = (960,)
SECONDS_PER_POSITION = 4
TEXT_ALPHA = 38       # ~15% -- dim: overlaps the text on purpose but never competes with it
SHADOW_ALPHA = 0
BAKED_ALPHA = 40      # sits BEHIND the text now, so a little dimmer keeps text richer than the background


# Kept for call-site compatibility: the watermark is now one dim, large mark at
# the exact vertical middle of EVERY card (2026-10-07 request), so Gita no longer
# needs its own position.
GITA_POSITIONS_Y = POSITIONS_Y


def bake_watermark(canvas: Image.Image, handle: str = WATERMARK_TEXT, alpha: int = BAKED_ALPHA) -> Image.Image:
    """Lock the channel handle INTO the background (2026-10-09 request: "stick the watermark with the
    background, lock it"). Call on the card background BEFORE any text is drawn: the handle then sits
    behind the text (never over it), is identical on every frame, and cannot be separated from the picture.
    Fixed at the exact vertical middle, centered, dim."""
    w, h = canvas.size
    font = FontManager(_default_font_path()).get_font(size=FONT_SIZE, weight="Bold")
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    pb = probe.textbbox((0, 0), handle, font=font)
    if pb[2] - pb[0] > w - 160:
        font = FontManager(_default_font_path()).get_font(size=int(FONT_SIZE * (w - 160) / (pb[2] - pb[0])), weight="Bold")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), handle, font=font)
    x, y = (w - (bb[2] - bb[0])) // 2 - bb[0], h // 2 - (bb[3] - bb[1]) // 2 - bb[1]
    d.text((x, y), handle, font=font, fill=(255, 255, 255, alpha))
    return Image.alpha_composite(canvas.convert("RGBA"), layer)


def _default_font_path() -> Path:
    from mahanavi.config import get_settings
    return get_settings().telugu_font_path


def build_watermark_layers(
    out_dir: Path, font_path: Path, positions_y: tuple[int, ...] = POSITIONS_Y,
) -> list[Path]:
    """Create one transparent frame-size PNG per watermark position."""
    out_dir.mkdir(parents=True, exist_ok=True)
    font = FontManager(font_path).get_font(size=FONT_SIZE, weight="Bold")
    _probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    _pb = _probe.textbbox((0, 0), WATERMARK_TEXT, font=font)
    if _pb[2] - _pb[0] > FRAME_W - 160:  # keep inside the card border
        font = FontManager(font_path).get_font(size=int(FONT_SIZE * (FRAME_W - 160) / (_pb[2] - _pb[0])), weight="Bold")
    paths: list[Path] = []
    for i, cy in enumerate(positions_y):
        layer = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (FRAME_W - w) // 2 - bbox[0], cy - h // 2 - bbox[1]
        draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, SHADOW_ALPHA))
        draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, TEXT_ALPHA))
        path = out_dir / f"watermark_{i}.png"
        layer.save(path)
        paths.append(path)
    return paths


def overlay_filter(base_label: str, first_input_index: int, count: int, out_label: str) -> str:
    """ffmpeg filter-graph fragment: overlay layer k (input first_input_index+k)
    only during its time slot, cycling every SECONDS_PER_POSITION seconds."""
    cycle = SECONDS_PER_POSITION * count
    parts: list[str] = []
    prev = base_label
    for k in range(count):
        last = k == count - 1
        nxt = out_label if last else f"wm{k}"
        lo, hi = k * SECONDS_PER_POSITION, (k + 1) * SECONDS_PER_POSITION
        parts.append(
            f"[{prev}][{first_input_index + k}:v]"
            f"overlay=0:0:format=auto:enable='gte(mod(t,{cycle}),{lo})*lt(mod(t,{cycle}),{hi})'[{nxt}]"
        )
        prev = nxt
    return ";".join(parts)
