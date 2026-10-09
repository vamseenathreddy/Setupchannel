"""Weekly Rashi table card: ONE still card, 12 rows, two columns (rashi | mantra), the week's date range
in a banner pinned at the top. Layout approved by the owner 2026-10-09. The table ends at about 69% of the
frame height and the footer at about 77%, clear of YouTube's channel/caption area, and its right edge is
well left of the Like/Comment buttons. The channel handle is baked into the background (behind the text).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from mahanavi.config import Settings
from mahanavi.images.fonts import FontManager
from mahanavi.images.layout import vertical_gradient
from mahanavi.video.watermark import bake_watermark

W, H = 1080, 1920
GOLD, LIGHT, DARK = (230, 190, 90), (255, 250, 240), (20, 50, 30)
ENGINE_FONTS = Path(__file__).resolve().parents[3] / "channels" / "engine" / "assets" / "fonts"

TEXTS = {
    "te": {"title": "ఈ వారం రాశి మంత్రాలు", "col1": "రాశి", "col2": "మంత్రం",
           "chant": "ప్రతి మంత్రం 108 సార్లు చదువుకోండి", "cta": "ఈ వీడియోపై మీ అభిప్రాయం కామెంట్ చేయండి"},
    "hi": {"title": "इस सप्ताह के राशि मंत्र", "col1": "राशि", "col2": "मंत्र",
           "chant": "हर मंत्र 108 बार जपें", "cta": "इस वीडियो पर अपनी राय कमेंट करें"},
}


@dataclass(frozen=True)
class WeeklyCard:
    date_text: str
    rows: list[dict]          # name, name_en, mantra
    lang: str = "te"
    handle: str = "@MahanaviSpirituals"


class RashiWeeklyCardRenderer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._te = FontManager(settings.telugu_font_path)

    def _font(self, lang: str, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        if lang == "te":
            return self._te.get_font(size=size, weight="Bold" if bold else "Regular")
        path = ENGINE_FONTS / ("Hind-Bold.ttf" if bold else "Hind-Regular.ttf")
        return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)

    def render(self, card: WeeklyCard) -> Path:
        t, lang = TEXTS[card.lang], card.lang
        im = vertical_gradient(W, H, (12, 70, 40), (8, 36, 22)).convert("RGBA")
        d = ImageDraw.Draw(im)
        d.rectangle((30, 30, W - 30, H - 30), outline=GOLD, width=4)
        d.rectangle((42, 42, W - 42, H - 42), outline=GOLD, width=2)
        im = bake_watermark(im, handle=card.handle)

        L, R = 70, 930
        c1 = L + 310
        y0, hh, rh = 300, 70, 80
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shade)
        for i in range(len(card.rows)):
            if i % 2 == 0:
                sd.rectangle((L, y0 + hh + i * rh, R, y0 + hh + (i + 1) * rh), fill=(255, 255, 255, 26))
        im = Image.alpha_composite(im, shade)
        d = ImageDraw.Draw(im)

        def ctr(text: str, font: ImageFont.FreeTypeFont, cx: int, y: int, color: tuple[int, ...]) -> None:
            b = d.textbbox((0, 0), text, font=font)
            d.text((cx - (b[2] - b[0]) // 2 - b[0], y - b[1]), text, font=font, fill=color)

        mid = (L + R) // 2
        d.rounded_rectangle((L, 80, R, 200), radius=40, fill=GOLD)
        date_font = self._font(lang, 64)
        if d.textlength(card.date_text, font=date_font) > R - L - 40:
            date_font = self._font(lang, 52)
        ctr(card.date_text, date_font, mid, 100, DARK)
        ctr(t["title"], self._font(lang, 54), mid, 222, GOLD)
        d.rectangle((L, y0, R, y0 + hh), fill=GOLD)
        ctr(t["col1"], self._font(lang, 46), (L + c1) // 2, y0 + 6, DARK)
        ctr(t["col2"], self._font(lang, 46), (c1 + R) // 2, y0 + 6, DARK)
        y = y0 + hh
        name_f, en_f, m_f = self._font(lang, 46), self._font("te", 26, bold=False), self._font(lang, 46)
        for row in card.rows:
            ctr(row["name"], name_f, (L + c1) // 2, y + 2, LIGHT)
            ctr(row["name_en"], en_f, (L + c1) // 2, y + 52, GOLD)
            mf = m_f
            if d.textlength(row["mantra"], font=mf) > R - c1 - 20:
                mf = self._font(lang, 40)
            ctr(row["mantra"], mf, (c1 + R) // 2, y + 16, LIGHT)
            y += rh
        d.line((c1, y0, c1, y), fill=GOLD, width=3)
        d.rectangle((L, y0, R, y), outline=GOLD, width=3)
        ctr(t["chant"], self._font(lang, 50), mid, y + 28, GOLD)
        ctr(t["cta"], self._font(lang, 44), mid, y + 100, LIGHT)

        out_dir = self._settings.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"rashi_weekly_{card.lang}.png"
        im.convert("RGB").save(out)
        return out
