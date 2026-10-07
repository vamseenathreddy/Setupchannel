"""
Channel-handle watermark for the card Shorts.

Per explicit request (2026-10-07): "add a watermark of that channel's
short. Users should not copy but readers should not feel inconvenient."

Design: a small, low-opacity "@MahanaviSpirituals" in the EMPTY margins of
the card (never over the story text, never in the zones YouTube's own UI
covers -- right-hand button rail and the bottom caption area). It
alternates between a top and a lower position every few seconds, so a
single crop cannot remove it from the whole video, yet a reader's eye is
never pulled away from the text.

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
FONT_SIZE = 36
# (center_y) of each position: top margin (inside the card border, above the
# invocation line) and lower-middle (below the subscribe line, above YouTube's
# bottom caption area).
POSITIONS_Y = (88, 1400)
SECONDS_PER_POSITION = 4
TEXT_ALPHA = 105      # ~41% -- visible if you look, unobtrusive if you read
SHADOW_ALPHA = 60


# Gita cards carry a "yesterday's Q&A" block down to ~y=1480, so they use a
# lower second position (still inside the card border).
GITA_POSITIONS_Y = (88, 1590)


def build_watermark_layers(
    out_dir: Path, font_path: Path, positions_y: tuple[int, ...] = POSITIONS_Y,
) -> list[Path]:
    """Create one transparent frame-size PNG per watermark position."""
    out_dir.mkdir(parents=True, exist_ok=True)
    font = FontManager(font_path).get_font(size=FONT_SIZE, weight="Bold")
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
