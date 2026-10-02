"""
Shared Sri Chakra (Sri Yantra) drawing helpers -- a programmatic,
copyright-free rendering of the classic interlocking-triangle yantra
(four upward "Shiva" triangles + five downward "Shakti" triangles around
a central bindu, ringed by a lotus-petal border), replacing the earlier
generic muggu/kolam roundel as the Purana Story cards' background motif
per explicit request (2026-10-02: "i want slowly rotating sri chakram in
background"). Pulled into its own module, same pattern as images/muggu.py
(which is left in place -- still used by the Rashi Mantra backgrounds),
so this motif can be drawn directly onto a canvas OR rendered as a
standalone transparent PNG for the rotating-overlay video pipeline (see
render_sri_chakra_png below, consumed by video/assembler.py's
assemble_purana_short_with_rotating_chakra).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

RGBA = tuple[int, int, int, int]

# How many upward ("Shiva") vs downward ("Shakti") triangles to draw, and
# the radius each is inscribed in (as a fraction of the overall motif
# radius) -- loosely mirrors the real Sri Yantra's nine interlocking
# triangles without attempting exact traditional proportions, which isn't
# needed for a background watermark motif.
_UPWARD_RADIUS_FRACS = (1.0, 0.80, 0.60, 0.40)
_DOWNWARD_RADIUS_FRACS = (0.92, 0.74, 0.56, 0.38, 0.20)


def _triangle_points(
    center: tuple[float, float], radius: float, point_up: bool,
) -> list[tuple[float, float]]:
    """Equilateral triangle inscribed in a circle of the given radius,
    pointing up (apex at top) or down (apex at bottom)."""
    cx, cy = center
    base_angle = -90.0 if point_up else 90.0
    points = []
    for i in range(3):
        angle = math.radians(base_angle + i * 120.0)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def draw_sri_chakra_roundel(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    accent: RGBA,
    line_width: int = 3,
) -> None:
    """Draws the interlocking-triangle yantra + lotus-petal ring + bindu,
    all as outline strokes in `accent` (pass an RGBA tuple -- this is
    almost always used as a watermark at a non-opaque alpha)."""
    cx, cy = center

    # Outer boundary circle.
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=accent, width=line_width,
    )

    # Lotus-petal ring just inside the boundary circle: a ring of small
    # overlapping circles, the same "petal" construction used by the
    # muggu roundel, reused here to frame the triangles.
    petal_count = 16
    petal_ring_radius = radius * 0.92
    petal_r = radius * 0.11
    for i in range(petal_count):
        angle = 2 * math.pi * i / petal_count
        px = cx + petal_ring_radius * math.cos(angle)
        py = cy + petal_ring_radius * math.sin(angle)
        draw.ellipse(
            [px - petal_r, py - petal_r, px + petal_r, py + petal_r],
            outline=accent, width=max(line_width - 1, 1),
        )

    # Nine interlocking triangles -- the Sri Yantra's defining feature.
    inner_radius = radius * 0.72
    for frac in _UPWARD_RADIUS_FRACS:
        pts = _triangle_points(center, inner_radius * frac, point_up=True)
        draw.polygon(pts, outline=accent, width=line_width)
    for frac in _DOWNWARD_RADIUS_FRACS:
        pts = _triangle_points(center, inner_radius * frac, point_up=False)
        draw.polygon(pts, outline=accent, width=line_width)

    # Central bindu (the yantra's focal point) + a small ring around it.
    bindu_r = max(radius // 22, 4)
    draw.ellipse([cx - bindu_r, cy - bindu_r, cx + bindu_r, cy + bindu_r], fill=accent)
    ring_r = bindu_r * 2.4
    draw.ellipse(
        [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
        outline=accent, width=max(line_width - 1, 1),
    )


def render_sri_chakra_png(
    output_path: Path,
    size: tuple[int, int],
    radius: int,
    center: tuple[int, int] | None = None,
    accent: RGBA = (230, 190, 90, 110),
    line_width: int = 3,
) -> Path:
    """Renders a standalone, transparent-background PNG the same size as
    the card canvas, with the motif centered (or at an explicit `center`)
    -- used as its own layer so ffmpeg can rotate it independently of the
    static backdrop and text layers beneath/above it."""
    width, height = size
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_sri_chakra_roundel(
        draw, center=center or (width // 2, height // 2),
        radius=radius, accent=accent, line_width=line_width,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    return output_path
