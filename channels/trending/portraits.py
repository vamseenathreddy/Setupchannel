"""Portrait cut-outs (highlighted with a white outline) at the bottom of the card, and the reporter ID badge top-left."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PEOPLE = Path(__file__).resolve().parent / "assets/people"
W, H = 1080, 1920
WHO = {"chandrababu": ("cbn", "ntr"), "lokesh": ("lokesh", "cbn"), "tdp": ("ntr", "cbn"),
       "nda": ("cbn", "lokesh"), "development": ("cbn", "lokesh"), "innovations": ("lokesh", "cbn")}


def _person(name: str, height: int) -> Image.Image:
    im = Image.open(PEOPLE / f"{name}.png").convert("RGBA")
    im = im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
    a = im.getchannel("A")
    halo = a.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(2))
    out = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0))
    glow = Image.new("RGBA", out.size, (255, 255, 255, 0))
    glow.paste(Image.new("RGBA", im.size, (255, 255, 255, 255)), (20, 20), halo)
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", im.size, (90, 40, 0, 150)), (28, 30), a.filter(ImageFilter.GaussianBlur(10)))
    out = Image.alpha_composite(Image.alpha_composite(out, shadow), glow)
    out.alpha_composite(im, (20, 20))
    return out


def _badge(bg: Image.Image, font_path: str) -> None:
    d = ImageDraw.Draw(bg)
    x, y, w, h = 36, 232, 350, 118
    d.rounded_rectangle((x, y, x + w, y + h), 18, fill=(190, 20, 30, 255), outline=(255, 255, 255, 255), width=4)
    d.rectangle((x + 4, y + h - 30, x + w - 4, y + h - 8), fill=(255, 214, 0, 255))
    me = Image.open(PEOPLE / "me.png").convert("RGBA")
    # face crop: top 60% of the cut-out, square
    side = min(me.width, int(me.height * 0.55))
    me = me.crop(((me.width - side) // 2, 0, (me.width + side) // 2, side)).resize((88, 88), Image.LANCZOS)
    ring = Image.new("RGBA", (96, 96), (255, 255, 255, 255))
    mask = Image.new("L", (96, 96), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 95, 95), fill=255)
    ring.alpha_composite(me, (4, 4))
    bg.paste(ring, (x + 12, y + 10), mask)
    f1, f2 = ImageFont.truetype(font_path, 27), ImageFont.truetype(font_path, 22)
    d.text((x + 120, y + 18), "Pulse Boosting", font=f1, fill=(255, 255, 255, 255))
    d.text((x + 120, y + 58), "తెలుగు వార్తలు", font=f2, fill=(255, 235, 150, 255))


def make_overlay(font_path: str):
    def overlay(bg: Image.Image, row: dict) -> Image.Image:
        bg = bg.convert("RGBA")
        a, b = WHO.get(row.get("category", ""), ("cbn", "lokesh"))
        big, small = _person(a, 520), _person(b, 400)
        bg.alpha_composite(big, (-10, H - big.height + 30))
        bg.alpha_composite(small, (W - small.width + 10, H - small.height + 30))
        _badge(bg, font_path)
        return bg
    return overlay
