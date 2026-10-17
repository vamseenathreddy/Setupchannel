"""Portrait cut-outs (highlighted with a white outline) at the bottom of the card, and the reporter ID badge top-left."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PEOPLE = Path(__file__).resolve().parent / "assets/people"
W, H = 1080, 1920
WHO = {"chandrababu": ("cbn", "lokesh"), "lokesh": ("lokesh", "cbn"), "tdp": ("cbn", "lokesh"),
       "nda": ("cbn", "lokesh"), "development": ("cbn", "lokesh"), "innovations": ("lokesh", "cbn"), "join": ("cbn", "lokesh"), "voice": ("lokesh", "cbn"),
       "janasena": ("pawan", None)}  # Janasena cards: Pawan Kalyan only


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
    fade = Image.new("L", out.size, 255)  # soft bottom edge, since the photos are cut at the shoulders
    fd = ImageDraw.Draw(fade)
    for i in range(70):
        fd.line((0, out.height - 1 - i, out.width, out.height - 1 - i), fill=int(255 * i / 70))
    out.putalpha(Image.composite(out.getchannel("A"), Image.new("L", out.size, 0), fade))
    return out


def _coin(name: str, d: int) -> Image.Image:
    """The person as a round coin: white disc, the cut-out filling it, a white ring and a red rim."""
    im = Image.open(PEOPLE / f"{name}.png").convert("RGBA")
    k = d * 1.05 / im.width
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    disc = Image.new("RGBA", (d, d), (255, 248, 225, 255))
    disc.alpha_composite(im, ((d - im.width) // 2, 6))
    mask = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    pad = 14
    out = Image.new("RGBA", (d + 2 * pad, d + 2 * pad), (0, 0, 0, 0))
    od = ImageDraw.Draw(out)
    od.ellipse((0, 0, out.width - 1, out.height - 1), fill=(190, 20, 30, 255))
    od.ellipse((6, 6, out.width - 7, out.height - 7), fill=(255, 255, 255, 255))
    out.paste(disc, (pad, pad), mask)
    return out


def _badge(bg: Image.Image, font_path: str) -> None:
    d = ImageDraw.Draw(bg)
    x, y, w, h = 30, 120, 360, 118
    d.rounded_rectangle((x, y, x + w, y + h), 18, fill=(190, 20, 30, 255), outline=(255, 255, 255, 255), width=4)
    d.rectangle((x + 4, y + h - 30, x + w - 4, y + h - 8), fill=(255, 214, 0, 255))
    me = Image.open(PEOPLE / "me_face.png").convert("RGBA").resize((104, 104), Image.LANCZOS)
    ring = Image.new("RGBA", (112, 112), (255, 255, 255, 255))
    mask = Image.new("L", (112, 112), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 111, 111), fill=255)
    ring.alpha_composite(me, (4, 4))
    bg.paste(ring, (x + 8, y + 3), mask)
    f1, f2 = ImageFont.truetype(font_path, 27), ImageFont.truetype(font_path, 22)
    d.text((x + 134, y + 18), "Pulse Boosting", font=f1, fill=(255, 255, 255, 255))
    d.text((x + 134, y + 58), "తెలుగు వార్తలు", font=f2, fill=(255, 235, 150, 255))


def make_overlay(font_path: str):
    def overlay(bg: Image.Image, row: dict) -> Image.Image:
        bg = bg.convert("RGBA")
        a, b = WHO.get(row.get("category", ""), ("cbn", "lokesh"))
        big, small = _person(a, 430), (_person(b, 340) if b else None)
        if b:  # NTR's round coin, top-right, on the TDP cards only
            ntr = _coin("ntr", 170)
            bg.alpha_composite(ntr, (W - ntr.width - 40, 150))
        bg.alpha_composite(big, (-10, H - big.height - 150))
        if small:
            bg.alpha_composite(small, (W - small.width + 10, H - small.height - 150))
        _badge(bg, font_path)
        return bg
    return overlay
