"""
Shared Sri Chakra (Sri Yantra-inspired) drawing helpers -- a
programmatic, copyright-free mandala motif (an outer circle, a ring of
lotus petals, two interlocking rings of radiating star-points, and a
central bindu), replacing the earlier generic muggu/kolam roundel as the
Purana Story cards' background motif per explicit request (2026-10-02:
"i want slowly rotating sri chakram in background"). Pulled into its own
module, same pattern as images/muggu.py (which is left in place -- still
used by the Rashi Mantra backgrounds), so this motif can be drawn
directly onto a canvas OR rendered as a standalone transparent PNG for
the rotating-overlay video pipeline (see render_sri_chakra_png below,
consumed by video/assembler.py's assemble_purana_short_with_rotating_chakra).

ROTATIONAL SYMMETRY, BY DESIGN: every part of this motif (the petal
ring, both star-point rings) is built from CHAKRA_POINTS evenly-spaced
copies around the same center, at the same CHAKRA_POINTS-fold angular
period -- so the whole motif is exactly symmetric under a rotation of
360/CHAKRA_POINTS degrees (and any whole multiple of it). This was a
deliberate redesign (an earlier version used two unevenly-sized
triangle sets, which only had 60-degree symmetry) so that
video/assembler.py's rotating-chakra assembly can slow its spin down to
any fraction of a revolution that's a multiple of 1/CHAKRA_POINTS and
still land on a pixel-identical frame at the loop point -- see that
module's CHAKRA_REVOLUTIONS_PER_LOOP comment for why this matters (the
loop must stay invisible, "user should not feel" the Short restarting).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

RGBA = tuple[int, int, int, int]

# Number of points in the radiating star motif, and the petal count in
# the ring around it -- kept EQUAL and SHARED by every symmetric element
# below specifically so the whole motif's rotational symmetry period is
# a single clean value (360 / CHAKRA_POINTS degrees). Picked as a highly
# divisible number (12) so a wide range of slowdown fractions --
# 1/2, 1/3, 1/4, 1/6, 1/12 of a revolution -- all stay loop-seamless.
CHAKRA_POINTS = 12


def _spike_triangle(
    center: tuple[float, float], angle_deg: float, inner_r: float, outer_r: float, half_width_deg: float,
) -> list[tuple[float, float]]:
    """A single radial "spike" -- a narrow triangle with its tip at
    `outer_r` and its base straddling `angle_deg` at `inner_r` -- the
    building block for the star-point rings below."""
    cx, cy = center
    tip_angle = math.radians(angle_deg)
    tip = (cx + outer_r * math.cos(tip_angle), cy + outer_r * math.sin(tip_angle))
    a1 = math.radians(angle_deg - half_width_deg)
    a2 = math.radians(angle_deg + half_width_deg)
    base1 = (cx + inner_r * math.cos(a1), cy + inner_r * math.sin(a1))
    base2 = (cx + inner_r * math.cos(a2), cy + inner_r * math.sin(a2))
    return [tip, base1, base2]


def draw_sri_chakra_roundel(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    radius: int,
    accent: RGBA,
    line_width: int = 3,
    points: int = CHAKRA_POINTS,
) -> None:
    """Draws the mandala/yantra motif -- outer circle, lotus-petal ring,
    two interlocking star-point rings, and a central bindu -- all as
    outline strokes in `accent` (pass an RGBA tuple -- this is almost
    always used as a watermark at a non-opaque alpha). `points` controls
    both ring's point count AND the motif's rotational symmetry period
    (360/points degrees) -- keep it at the default unless you also
    update the caller's rotation-speed fractions to match."""
    cx, cy = center
    step = 360.0 / points

    # Outer boundary circle -- perfectly rotation-symmetric on its own.
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=accent, width=line_width,
    )

    # Lotus-petal ring just inside the boundary circle: a ring of small
    # overlapping circles, the same "petal" construction used by the
    # muggu roundel, reused here to frame the star. Uses the SAME point
    # count as the star rings below so the whole motif shares one
    # rotational symmetry period.
    petal_ring_radius = radius * 0.92
    petal_r = radius * 0.11
    for i in range(points):
        angle = math.radians(step * i)
        px = cx + petal_ring_radius * math.cos(angle)
        py = cy + petal_ring_radius * math.sin(angle)
        draw.ellipse(
            [px - petal_r, py - petal_r, px + petal_r, py + petal_r],
            outline=accent, width=max(line_width - 1, 1),
        )

    # Two interlocking rings of radiating spikes -- the Sri Yantra-
    # inspired "star" at the motif's heart. The inner ring is offset by
    # half a step so the two rings interlock visually, but each ring is
    # independently `points`-periodic, so the combined figure is too.
    half_width = step * 0.32
    for i in range(points):
        angle = step * i
        draw.polygon(
            _spike_triangle(center, angle, radius * 0.55, radius * 0.95, half_width),
            outline=accent, width=line_width,
        )
    for i in range(points):
        angle = step * i + step / 2
        draw.polygon(
            _spike_triangle(center, angle, radius * 0.22, radius * 0.58, half_width),
            outline=accent, width=line_width,
        )

    # Central bindu (the yantra's focal point) + a small ring around it
    # -- a point and a circle, both rotation-symmetric at any angle.
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
