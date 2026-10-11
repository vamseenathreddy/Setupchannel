"""
draw_krishna_arjuna_chariot: an ORIGINAL, simplified line-art silhouette
of a chariot scene (two generic standing figures on a wheeled chariot,
one holding a bow) for the Bhagavad Gita Sloka Shorts card background,
per explicit request (2026-10-02: "with krishna and Arjuna background
image").

WHY A GENERIC SILHOUETTE, NOT A REALISTIC DEPICTION: Krishna and Arjuna
are figures from Hindu scripture, not a copyrighted character or a
specific artwork -- but a REALISTIC rendering would inevitably echo some
particular existing painting's composition (there are a few famous,
widely-recognized Gita chariot paintings). This motif deliberately stays
abstract and iconographic instead: simple geometric shapes (circles,
triangles, arcs) suggesting "a chariot, a driver, an archer" rather than
facial features, clothing details, or any specific artist's composition
-- the same "original, not a copy of a known work" approach already used
for every other decorative motif on this channel (images/sri_chakra.py's
mandala, images/muggu.py's rangoli pattern). Low-alpha gold line art,
drawn behind the text, same watermark treatment as the Sri Chakra.
"""

from __future__ import annotations

import math

from PIL import ImageDraw


def draw_krishna_arjuna_chariot(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    baseline_y: int,
    scale: int,
    accent: tuple[int, int, int, int],
    line_width: int = 3,
) -> None:
    """Draws a simple chariot silhouette centered horizontally at
    center_x, with its wheel's bottom resting on baseline_y. `scale` is
    roughly the wheel's diameter in pixels -- every other dimension is
    derived from it so the whole motif scales as one unit."""
    wheel_r = scale // 2
    wheel_cx = center_x
    wheel_cy = baseline_y - wheel_r

    # Wheel: outer rim + spokes (same "radiating spokes from a bindu"
    # language as the Sri Chakra, but drawn as a literal wheel here).
    draw.ellipse(
        [wheel_cx - wheel_r, wheel_cy - wheel_r, wheel_cx + wheel_r, wheel_cy + wheel_r],
        outline=accent, width=line_width,
    )
    spokes = 8
    for i in range(spokes):
        angle = math.radians(360.0 / spokes * i)
        x2 = wheel_cx + wheel_r * math.cos(angle)
        y2 = wheel_cy + wheel_r * math.sin(angle)
        draw.line([(wheel_cx, wheel_cy), (x2, y2)], fill=accent, width=max(line_width - 1, 1))
    hub_r = max(wheel_r // 10, 4)
    draw.ellipse(
        [wheel_cx - hub_r, wheel_cy - hub_r, wheel_cx + hub_r, wheel_cy + hub_r],
        outline=accent, width=line_width,
    )

    # Chariot platform: a simple trapezoid sitting on the wheel's axle.
    platform_w = int(scale * 1.3)
    platform_h = int(scale * 0.22)
    platform_top = wheel_cy - int(scale * 0.1)
    platform = [
        (wheel_cx - platform_w // 2, platform_top),
        (wheel_cx + platform_w // 2, platform_top),
        (wheel_cx + platform_w // 2 - platform_h // 2, platform_top - platform_h),
        (wheel_cx - platform_w // 2 + platform_h // 2, platform_top - platform_h),
    ]
    draw.polygon(platform, outline=accent, width=line_width)
    deck_y = platform_top - platform_h

    # Two simple standing figures on the platform: a plain "head circle +
    # body triangle" silhouette each, not a detailed human figure --
    # Krishna (left, holding reins -- a single curved line toward where
    # the horse would be) and Arjuna (right, holding a bow -- an arc with
    # a drawn bowstring). fig_h is deliberately well under wheel_r so the
    # whole scene's total height stays close to ~2.2x the wheel diameter
    # -- callers should budget at least that much vertical room above
    # baseline_y.
    fig_h = int(scale * 0.62)
    fig_w = int(scale * 0.30)

    def _figure(cx: int) -> None:
        head_r = int(fig_w * 0.28)
        head_cy = deck_y - fig_h + head_r
        draw.ellipse(
            [cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
            outline=accent, width=line_width,
        )
        body_top = head_cy + head_r
        body = [
            (cx, body_top),
            (cx - fig_w // 2, deck_y),
            (cx + fig_w // 2, deck_y),
        ]
        draw.polygon(body, outline=accent, width=line_width)

    left_cx = wheel_cx - int(scale * 0.28)
    right_cx = wheel_cx + int(scale * 0.28)
    _figure(left_cx)
    _figure(right_cx)

    # Krishna (left figure): reins -- a simple curved line reaching
    # forward/down, suggesting he is driving rather than fighting.
    reins_start = (left_cx - fig_w // 3, deck_y - int(fig_h * 0.55))
    reins_end = (wheel_cx - int(scale * 0.9), wheel_cy)
    draw.line(
        [reins_start, ((reins_start[0] + reins_end[0]) // 2, reins_start[1] + 20), reins_end],
        fill=accent, width=max(line_width - 1, 1),
    )

    # Arjuna (right figure): a drawn bow -- an arc plus a straight
    # bowstring -- held up and to the right, the single most recognizable
    # "this is Arjuna" visual shorthand without drawing a realistic face
    # or weapon.
    bow_cx = right_cx + int(fig_w * 0.75)
    bow_cy = deck_y - int(fig_h * 0.55)
    bow_r = int(scale * 0.22)
    draw.arc(
        [bow_cx - bow_r, bow_cy - bow_r, bow_cx + bow_r, bow_cy + bow_r],
        start=250, end=110, fill=accent, width=line_width,
    )
    top = (
        bow_cx + bow_r * math.cos(math.radians(250)),
        bow_cy + bow_r * math.sin(math.radians(250)),
    )
    bottom = (
        bow_cx + bow_r * math.cos(math.radians(110)),
        bow_cy + bow_r * math.sin(math.radians(110)),
    )
    draw.line([top, bottom], fill=accent, width=max(line_width - 2, 1))

    # Horse (suggested, not detailed): a simple arched-neck silhouette
    # ahead of the chariot, pulling it -- an ellipse body + two leg lines
    # + a long neck/head line, in keeping with "shapes suggesting a
    # scene" rather than a realistic animal drawing.
    horse_cx = wheel_cx - int(scale * 1.3)
    horse_cy = wheel_cy + int(scale * 0.05)
    horse_body_w = int(scale * 0.55)
    horse_body_h = int(scale * 0.28)
    draw.ellipse(
        [horse_cx - horse_body_w // 2, horse_cy - horse_body_h // 2,
         horse_cx + horse_body_w // 2, horse_cy + horse_body_h // 2],
        outline=accent, width=line_width,
    )
    neck_start = (horse_cx + horse_body_w // 3, horse_cy - horse_body_h // 3)
    neck_end = (horse_cx + horse_body_w, horse_cy - int(scale * 0.4))
    draw.line([neck_start, neck_end], fill=accent, width=line_width)
    for leg_dx in (-horse_body_w // 3, horse_body_w // 3):
        leg_top = (horse_cx + leg_dx, horse_cy + horse_body_h // 2)
        leg_bottom = (horse_cx + leg_dx, baseline_y)
        draw.line([leg_top, leg_bottom], fill=accent, width=max(line_width - 1, 1))
