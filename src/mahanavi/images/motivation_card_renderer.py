"""Single 1080x1920 card for the daily Purana motivation word Short: blurred deity photo, sharp framed photo
in the lower half (face clear of text), big Telugu word + reason + source in the safe zone above it."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from mahanavi.config import Settings
from mahanavi.images.fonts import FontManager
from mahanavi.video.watermark import bake_watermark

W, H = 1080, 1920
GOLD = (255, 205, 110)
WHITE = (255, 255, 255)
PHOTO_W = 800
PHOTO_TOP = 965
PHOTO_MAX_H = 770
TEXT_TOP, TEXT_BOTTOM = 230, 900


class MotivationCardRenderer:
    def __init__(self, settings: Settings) -> None:
        self._fonts = FontManager(settings.telugu_font_path)

    def _font(self, size: int, weight: str = "Bold") -> Any:
        return self._fonts.get_font(size=size, weight=weight)

    def _background(self, photo: Image.Image) -> Image.Image:
        photo = photo.convert("RGB")
        s = max(W / photo.width, H / photo.height)
        base = photo.resize((int(photo.width * s) + 1, int(photo.height * s) + 1), Image.Resampling.LANCZOS)
        x, y = (base.width - W) // 2, (base.height - H) // 2
        base = base.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(30))
        base = Image.blend(base, Image.new("RGB", (W, H), (12, 6, 36)), 0.62)
        # top-to-bottom darkening so the text zone is always readable
        shade = Image.new("L", (1, H))
        for yy in range(H):
            shade.putpixel((0, yy), int(150 * max(0.0, 1 - yy / 900)))
        shade = shade.resize((W, H))
        base.paste(Image.new("RGB", (W, H), (5, 2, 20)), (0, 0), shade)
        return base

    def _photo_panel(self, canvas: Image.Image, photo: Image.Image) -> None:
        photo = photo.convert("RGB")
        h = int(photo.height * PHOTO_W / photo.width)
        p = photo.resize((PHOTO_W, h), Image.Resampling.LANCZOS)
        p = p.crop((0, 0, PHOTO_W, min(h, PHOTO_MAX_H)))  # keep the top (faces), drop the bottom
        x = (W - PHOTO_W) // 2
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle((x - 10, PHOTO_TOP - 10, x + PHOTO_W + 10, PHOTO_TOP + p.height + 10), 18, outline=GOLD, width=5)
        mask = Image.new("L", p.size, 255)
        fade = Image.new("L", (1, 90))
        for i in range(90):
            fade.putpixel((0, i), int(255 * i / 89))
        mask.paste(fade.resize((p.width, 90)), (0, 0))
        canvas.paste(p, (x, PHOTO_TOP), mask)

    def _wrap(self, d: ImageDraw.ImageDraw, text: str, font: Any, width: int) -> list[str]:
        lines: list[str] = []
        cur = ""
        for word in text.split():
            t = f"{cur} {word}".strip()
            if d.textlength(t, font=font) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def _centered(self, d: ImageDraw.ImageDraw, y: int, text: str, font: Any, fill: Any) -> int:
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], y), text, font=font, fill=fill, stroke_width=2, stroke_fill=(0, 0, 0))
        return int(y + (bb[3] - bb[1]))

    def render(self, *, photo_path: Path, label: str, word: str, reason: str, source: str,
               invocation: str, header: str, footer: str, watermark: str, out: Path) -> Path:
        photo = Image.open(photo_path)
        canvas = self._background(photo)
        self._photo_panel(canvas, photo)
        canvas = bake_watermark(canvas.convert("RGBA"), watermark).convert("RGB")
        d = ImageDraw.Draw(canvas)
        d.rectangle((40, 40, W - 40, H - 40), outline=GOLD, width=4)
        d.rectangle((54, 54, W - 54, H - 54), outline=(255, 205, 110, 120), width=1)

        y = TEXT_TOP
        y = self._centered(d, y, label, self._font(52), GOLD) + 40
        size = 160
        font = self._font(size)
        while d.textlength(word, font=font) > 900 and size > 80:
            size -= 6
            font = self._font(size)
        y = self._centered(d, y, word, font, WHITE) + 26
        d.line((W // 2 - 150, y, W // 2 + 150, y), fill=GOLD, width=3)
        d.ellipse((W // 2 - 8, y - 8, W // 2 + 8, y + 8), fill=GOLD)
        y += 34
        rf = self._font(54, "Regular")
        for ln in self._wrap(d, reason, rf, 900)[:3]:
            y = self._centered(d, y, ln, rf, (240, 232, 255)) + 16
        y += 14
        y = self._centered(d, y, f"— {source}", self._font(50), GOLD) + 28
        if y < PHOTO_TOP - 90:
            self._centered(d, y, invocation, self._font(56), WHITE)
        self._centered(d, 1800, footer, self._font(38, "Regular"), (230, 220, 250))
        out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out)
        return out
