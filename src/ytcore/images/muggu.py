"""
Shared muggu/kolam-roundel drawing helpers -- the same programmatic,
copyright-free rangoli motif technique already used for the Rashi
Mantra Shorts' backgrounds (scripts/generate_rashi_backgrounds.py),
pulled out into a shared module so the Purana Story cards can reuse the
exact same geometry (dots + looping petal arcs + center ring) instead
of duplicating it, and so a standalone transparent PNG of just the
motif can be rendered for animation (see render_muggu_png below).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


def draw_muggu_roundel(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    petals: int,
    accent: tuple[int, int, int] | tuple[int, int, int, int],
) -> None:
    """A simple symmetric dot-and-petal rangoli/kolam-style roundel -- a
    ring of dots connected by curved petal strokes around a central dot,
    the classic muggu construction method (dots first, curves looped
    around them). Purely geometric, generated from scratch. `accent` can
    be RGB (opaque) or RGBA (for a semi-transparent watermark use)."""
    cx, cy = center

    dot_r = max(radius // 28, 3)
    n_dots = petals * 2
    for i in range(n_dots):
        angle = 2 * math.pi * i / n_dots
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=accent)

    petal_r = radius * 0.42
    for i in range(petals):
        angle = 2 * math.pi * i / petals
        px = cx + (radius * 0.58) * math.cos(angle)
        py = cy + (radius * 0.58) * math.sin(angle)
        draw.ellipse([px - petal_r, py - petal_r, px + petal_r, py + petal_r], outline=accent, width=3)

    draw.ellipse([cx - dot_r * 2, cy - dot_r * 2, cx + dot_r * 2, cy + dot_r * 2], fill=accent)
    draw.ellipse(
        [cx - radius * 0.22, cy - radius * 0.22, cx + radius * 0.22, cy + radius * 0.22],
        outline=accent, width=2,
    )


def render_muggu_png(
    output_path: Path,
    size: int,
    petals: int,
    accent: tuple[int, int, int],
    alpha: int = 255,
) -> Path:
    """Renders a standalone square, transparent-background PNG of just
    the roundel, centered, sized to fill the canvas -- used as a
    separate overlay layer for the (optional) rotating-muggu video
    variant, where the motif needs to exist as its own image so ffmpeg
    can rotate it independently of the static text layer beneath it."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_muggu_roundel(
        draw, center=(size // 2, size // 2), radius=int(size * 0.44),
        petals=petals, accent=(*accent, alpha),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    return output_path
