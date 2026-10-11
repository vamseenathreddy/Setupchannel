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

# --- Product-tag sticker zone (owner request 2026-10-11) ---
# YouTube Shopping puts the tagged product's sticker + "Shop" button on the lower-left of a Short, over the
# video. Measured from a real posted Short (1080x1920 frame): x 45-350, y 940-1220. Cards keep this box free
# of text so the sticker never covers anything. Fractions of the 1080x1920 canvas.
PRODUCT_ZONE_X1_FRAC = 0.36    # right edge of the sticker box (x = 0 is the card's left edge)
PRODUCT_ZONE_TOP_FRAC = 0.482  # top of the sticker box (y = 925 of 1920; measured sticker top is ~940)
PRODUCT_ZONE_BOTTOM_FRAC = 0.64  # bottom of the sticker box incl. the "Shop" tab (y = 1229; measured ~1220)


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
