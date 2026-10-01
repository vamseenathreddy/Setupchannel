#!/usr/bin/env python3
"""
One-off asset generator: draws 3 traditional-style 9:16 card background
PNGs for the Rashi Mantra Shorts series and saves them under
Images/RashiMantra/backgrounds/.

WHY GENERATED, NOT SOURCED: the user flagged a copyright concern for this
series. Rather than download temple/rangoli photos of uncertain license,
every pixel here is drawn programmatically with PIL (gradient fill,
circles, arcs, lines) -- entirely original artwork, zero copyright risk,
and trivially re-runnable if the look needs to change later.

DESIGN: deep green gradient card (per explicit request: "green card"),
a traditional double-line gold border with small corner flourishes, and
a symmetric muggu/kolam-style dot-and-petal roundel centered in the upper
third of the card, BEHIND where the renderer will later draw text. Kept
to the upper third deliberately -- the renderer's content zone and the
YouTube-UI-safe footer zone (see alert_card_renderer.py's footer_bottom
note, backed by a real screenshot) need the middle/lower two-thirds clear
for text, so the motif must not spill into that area.

3 VARIANTS: same base design, different accent tone (gold / rose-gold /
silver) and a different petal count on the muggu roundel (8 / 10 / 12),
purely for visual variety across posts -- rotated by rashi index in the
renderer, same pattern this codebase already uses for title/hashtag pools.

This is a static asset generator, run once (or re-run after a design
tweak), NOT part of the per-post render pipeline -- consistent with how
the channel's deity icon images (Lakshmi, Ganesha, Kubera etc.) are
pre-supplied static files rather than generated at post time.

Usage:
    python scripts/generate_rashi_backgrounds.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH = 1080
HEIGHT = 1920

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "Images" / "RashiMantra" / "backgrounds"

# Three deep, traditional "temple green" tones -- not identical, so the
# three variants are visually distinguishable in the channel's grid.
_VARIANTS = [
    {
        "name": "bg_1.png",
        "top": (14, 70, 40),
        "bottom": (6, 38, 20),
        "accent": (212, 160, 23),  # gold
        "petals": 8,
    },
    {
        "name": "bg_2.png",
        "top": (10, 60, 48),
        "bottom": (4, 30, 24),
        "accent": (205, 150, 120),  # rose-gold
        "petals": 10,
    },
    {
        "name": "bg_3.png",
        "top": (16, 78, 52),
        "bottom": (6, 40, 28),
        "accent": (210, 210, 195),  # warm silver
        "petals": 12,
    },
]


def _vertical_gradient(top_rgb: tuple[int, int, int], bottom_rgb: tuple[int, int, int]) -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), top_rgb)
    top = Image.new("RGB", (WIDTH, HEIGHT), top_rgb)
    bottom = Image.new("RGB", (WIDTH, HEIGHT), bottom_rgb)
    mask = Image.new("L", (WIDTH, HEIGHT))
    mask.putdata([int(255 * (y / max(HEIGHT - 1, 1))) for y in range(HEIGHT) for _ in range(WIDTH)])
    return Image.composite(bottom, top, mask)


def _draw_traditional_border(draw: ImageDraw.ImageDraw, accent: tuple[int, int, int]) -> None:
    """Double-line border inset from the edge, with a small quarter-arc
    flourish in each corner -- a simple, generic South Indian temple-art
    motif (not any specific copyrighted artwork)."""
    outer_margin = int(WIDTH * 0.035)
    inner_margin = outer_margin + 10

    draw.rectangle(
        [outer_margin, outer_margin, WIDTH - outer_margin, HEIGHT - outer_margin],
        outline=accent, width=4,
    )
    draw.rectangle(
        [inner_margin, inner_margin, WIDTH - inner_margin, HEIGHT - inner_margin],
        outline=accent, width=2,
    )

    corner_r = int(WIDTH * 0.07)
    corners = [
        (outer_margin, outer_margin, 180, 270),       # top-left
        (WIDTH - outer_margin - 2 * corner_r, outer_margin, 270, 360),  # top-right
        (outer_margin, HEIGHT - outer_margin - 2 * corner_r, 90, 180),  # bottom-left
        (WIDTH - outer_margin - 2 * corner_r, HEIGHT - outer_margin - 2 * corner_r, 0, 90),  # bottom-right
    ]
    for x, y, start, end in corners:
        draw.arc([x, y, x + 2 * corner_r, y + 2 * corner_r], start=start, end=end, fill=accent, width=3)


def _draw_muggu_roundel(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int, petals: int, accent: tuple[int, int, int]) -> None:
    """A simple symmetric dot-and-petal rangoli/kolam-style roundel --
    a ring of dots connected by curved petal strokes around a central
    dot, the classic muggu construction method (dots first, curves
    looped around them). Purely geometric, generated from scratch."""
    cx, cy = center

    # Outer ring of small dots.
    dot_r = max(radius // 28, 3)
    n_dots = petals * 2
    for i in range(n_dots):
        angle = 2 * math.pi * i / n_dots
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=accent)

    # Petals: looping arcs between alternating dots, like kolam strokes.
    petal_r = radius * 0.42
    for i in range(petals):
        angle = 2 * math.pi * i / petals
        px = cx + (radius * 0.58) * math.cos(angle)
        py = cy + (radius * 0.58) * math.sin(angle)
        draw.ellipse(
            [px - petal_r, py - petal_r, px + petal_r, py + petal_r],
            outline=accent, width=3,
        )

    # Central dot + ring.
    draw.ellipse([cx - dot_r * 2, cy - dot_r * 2, cx + dot_r * 2, cy + dot_r * 2], fill=accent)
    draw.ellipse([cx - radius * 0.22, cy - radius * 0.22, cx + radius * 0.22, cy + radius * 0.22], outline=accent, width=2)


def generate() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for variant in _VARIANTS:
        canvas = _vertical_gradient(variant["top"], variant["bottom"])
        draw = ImageDraw.Draw(canvas)
        _draw_traditional_border(draw, variant["accent"])
        # Roundel centered in the upper third, clear of the mid/lower
        # text zone (renderer's content starts well below this).
        _draw_muggu_roundel(
            draw, center=(WIDTH // 2, int(HEIGHT * 0.165)),
            radius=int(WIDTH * 0.14), petals=variant["petals"], accent=variant["accent"],
        )
        out_path = OUTPUT_DIR / variant["name"]
        canvas.save(out_path, format="PNG", optimize=True)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    generate()
