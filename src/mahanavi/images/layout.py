"""Layout constants and reusable low-level drawing helpers for the renderer."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageOps

# --- Palette: warm devotional saffron/maroon/gold ---
COLOR_BG_TOP = (74, 14, 20)        # deep maroon
COLOR_BG_BOTTOM = (191, 87, 0)     # warm saffron-orange
COLOR_PANEL_BG = (255, 248, 231, 235)   # cream, semi-transparent (RGBA)
COLOR_PANEL_BORDER = (212, 160, 23)      # muted gold
COLOR_TEXT_DARK = (58, 27, 15)
COLOR_TEXT_LIGHT = (255, 250, 240)
COLOR_GOLD = (212, 160, 23)
COLOR_SHADOW = (0, 0, 0, 90)

# --- Layout geometry (fractions of canvas height, computed at render time) ---
HEADER_HEIGHT_FRAC = 0.09
IMAGE_AREA_HEIGHT_FRAC = 0.46
FOOTER_HEIGHT_FRAC = 0.055
MARGIN_X_FRAC = 0.06


def vertical_gradient(width: int, height: int, top_rgb: tuple, bottom_rgb: tuple) -> Image.Image:
    """Return an RGB image with a smooth vertical gradient background."""
    base = Image.new("RGB", (width, height), top_rgb)
    top = Image.new("RGB", (width, height), top_rgb)
    bottom = Image.new("RGB", (width, height), bottom_rgb)
    mask = Image.new("L", (width, height))
    mask_data = [int(255 * (y / max(height - 1, 1))) for y in range(height) for _ in range(width)]
    mask.putdata(mask_data)
    return Image.composite(bottom, top, mask)


def rounded_rectangle_mask(size: tuple[int, int], radius: int) -> Image.Image:
    """Return an 'L' mode mask with a filled rounded rectangle (for cropping/pasting)."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def cover_fit(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Resize+crop an image to exactly fill target_size, preserving aspect ratio (cover behaviour)."""
    return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def paste_with_rounded_corners(
    canvas: Image.Image, image: Image.Image, position: tuple[int, int], radius: int
) -> None:
    """Paste `image` onto `canvas` at `position`, clipped to rounded corners."""
    mask = rounded_rectangle_mask(image.size, radius)
    canvas.paste(image, position, mask)


def draw_drop_shadow(
    canvas: Image.Image, box: tuple[int, int, int, int], radius: int, offset: tuple[int, int] = (0, 8), blur: int = 12
) -> None:
    """Draw a soft rounded-rectangle drop shadow behind `box` directly onto an RGBA canvas."""
    from PIL import ImageFilter

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    x0, y0, x1, y1 = box
    shadow_draw.rounded_rectangle(
        [x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]],
        radius=radius,
        fill=COLOR_SHADOW,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(shadow_layer)
