"""Slide renderer for viewer-request Shorts (content/request_shorts.py).

One 1080x1920 still per slide on a twilight indigo-violet background with an ember glow, a colour no
scheduled Short uses, so a request Short is recognisable at a glance. All text stays inside the same
no-overlap safe zone as every other card (x 150-930, y 230-1385): clear of Shorts' search/menu icons at
the top, the Like/Comment buttons on the right and the title/channel row at the bottom. The channel
handle is baked into the background behind the text, like every other card.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from mahanavi.config import Settings
from mahanavi.content.request_shorts import RequestShort, Slide
from mahanavi.images.fonts import FontManager
from mahanavi.images.opinion_line import OPINION_TE
from mahanavi.video.watermark import bake_watermark

W, H = 1080, 1920
SAFE_L, SAFE_R, SAFE_TOP, SAFE_BOTTOM = 150, 930, 230, 1385
TEXT_W = SAFE_R - SAFE_L
GOLD, CREAM, SOFT = (240, 196, 92), (255, 246, 226), (214, 206, 224)
STACK_TOP, STACK_H = 560, 700   # mantra / transliteration / meaning band (ends well above the footer tag at 1318)
SUBSCRIBE_TE = "మరిన్ని మంత్రాల కోసం సబ్‌స్క్రైబ్ చేయండి"


Box = tuple[int, int, int, int]


@dataclass
class RenderedSlide:
    path: Path
    boxes: list[Box] = field(default_factory=list)  # every drawn text line, for tests


class RequestCardRenderer:
    def __init__(self, settings: Settings) -> None:
        self._fonts = FontManager(settings.telugu_font_path)
        self._probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))

    # ---- helpers -----------------------------------------------------------------------------
    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        return self._fonts.get_font(size=size, weight="Regular")

    def _greedy(self, para: str, font: ImageFont.FreeTypeFont, max_w: float) -> list[str]:
        lines: list[str] = []
        cur = ""
        for word in para.split():
            test = f"{cur} {word}".strip()
            if cur and self._probe.textlength(test, font=font) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines

    def _wrap(self, text: str, font: ImageFont.FreeTypeFont) -> list[str]:
        """Wrap to TEXT_W, then narrow the width as far as the line count allows so the lines come out
        balanced (no one-word last line). "\n" always starts a new line (verse lines stay apart)."""
        lines: list[str] = []
        for para in text.split("\n"):
            first = self._greedy(para, font, TEXT_W)
            width = TEXT_W
            while width > 200:
                trial = self._greedy(para, font, width - 12)
                if len(trial) != len(first):
                    break
                width -= 12
            lines += self._greedy(para, font, width)
        return lines

    def _fit(self, text: str, start: int, floor: int, max_h: int,
             spacing: float = 1.4) -> tuple[list[str], ImageFont.FreeTypeFont, int]:
        """Largest font size in [floor, start] at which the wrapped text fits TEXT_W x max_h."""
        size = start
        while True:
            font = self._font(size)
            lines = self._wrap(text, font)
            height = len(lines) * int(size * spacing)
            if (height <= max_h and all(self._probe.textlength(ln, font=font) <= TEXT_W for ln in lines)) or size <= floor:
                return lines, font, int(size * spacing)
            size -= 2

    @staticmethod
    def _background(spec: RequestShort, handle: str) -> Image.Image:
        top, mid, bot = spec.bg_top, spec.bg_mid, spec.bg_bottom
        im = Image.new("RGB", (W, H))
        px = ImageDraw.Draw(im)
        for y in range(H):
            t = y / (H - 1)
            a, b, u = (top, mid, t / 0.55) if t < 0.55 else (mid, bot, (t - 0.55) / 0.45)
            px.line((0, y, W, y), fill=tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse((W // 2 - 460, 620, W // 2 + 460, 1340), fill=64)
        glow = glow.filter(ImageFilter.GaussianBlur(170))
        im = Image.composite(Image.new("RGB", (W, H), spec.glow), im, glow)
        d = ImageDraw.Draw(im)
        d.rectangle((30, 30, W - 30, H - 30), outline=GOLD, width=4)
        d.rectangle((42, 42, W - 42, H - 42), outline=GOLD, width=2)
        return bake_watermark(im.convert("RGBA"), handle="@MahanaviSpirituals").convert("RGB")

    # ---- drawing -----------------------------------------------------------------------------
    def _line(self, layer: Image.Image, boxes: list[Box], text: str, font: ImageFont.FreeTypeFont, y: int,
              color: tuple[int, ...]) -> None:
        d = ImageDraw.Draw(layer)
        x = (W - d.textlength(text, font=font)) / 2
        d.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 150))
        d.text((x, y), text, font=font, fill=color)
        b = d.textbbox((x, y), text, font=font)
        boxes.append((int(b[0]), int(b[1]), int(b[2]), int(b[3])))

    def _block(self, layer: Image.Image, boxes: list[Box], lines: list[str], font: ImageFont.FreeTypeFont,
               lh: int, y: int, color: tuple[int, ...]) -> int:
        for ln in lines:
            self._line(layer, boxes, ln, font, y, color)
            y += lh
        return y

    def _dots(self, layer: Image.Image, active: int, total: int, y: int) -> None:
        d = ImageDraw.Draw(layer)
        gap, r = 44, 9
        x0 = (W - (total - 1) * gap) // 2
        for i in range(total):
            cx = x0 + i * gap
            box = (cx - r, y - r, cx + r, y + r)
            d.ellipse(box, fill=GOLD) if i == active else d.ellipse(box, outline=GOLD, width=3)

    def _ornament(self, layer: Image.Image, y: int) -> None:
        d = ImageDraw.Draw(layer)
        d.line((W // 2 - 190, y, W // 2 - 26, y), fill=GOLD, width=3)
        d.line((W // 2 + 26, y, W // 2 + 190, y), fill=GOLD, width=3)
        d.polygon([(W // 2, y - 13), (W // 2 + 13, y), (W // 2, y + 13), (W // 2 - 13, y)], fill=GOLD)

    def render(self, spec: RequestShort, index: int, out: Path) -> RenderedSlide:
        slide: Slide = spec.slides[index]
        boxes: list[Box] = []
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tag_line = f"{spec.handle} గారి కోరిక మేరకు"

        if slide.kind == "intro":
            self._line(layer, boxes, "మీ కోరిక మేరకు", self._font(60), 500, GOLD)
            lines, font, lh = self._fit(spec.deity_te + "\nమంత్రాలు", 120, 70, 420, 1.3)
            y = self._block(layer, boxes, lines, font, lh, 640, CREAM)
            self._ornament(layer, y + 40)
            lines, font, lh = self._fit("బీజ మంత్రంతో సహా 4 మంత్రాలు", 58, 36, 150)
            y = self._block(layer, boxes, lines, font, lh, y + 90, SOFT)
            lines, font, lh = self._fit(spec.handle, 60, 30, 100)
            self._block(layer, boxes, lines, font, lh, 1140, GOLD)
        elif slide.kind == "mantra":
            mantra_idx = sum(1 for s in spec.slides[:index] if s.kind == "mantra")
            total = sum(1 for s in spec.slides if s.kind == "mantra")
            self._line(layer, boxes, spec.deity_te, self._font(40), 262, SOFT)
            self._dots(layer, mantra_idx, total, 345)
            lines, font, lh = self._fit(slide.label_te, 76, 52, 110)
            self._block(layer, boxes, lines, font, lh, 420, GOLD)
            # Fit the three blocks into the band between the heading and the footer tag: shrink the mantra a
            # little at a time until the whole stack fits, so a long verse never crowds the footer.
            budget = 430
            while True:
                m_lines, m_font, m_lh = self._fit(slide.text_te, 92, 44, budget)
                t_lines, t_font, t_lh = self._fit(slide.translit, 42, 28, 190, 1.35)
                n_lines, n_font, n_lh = self._fit(slide.meaning_te, 44, 30, 150)
                heights = (len(m_lines) * m_lh, 60, len(t_lines) * t_lh, 40, len(n_lines) * n_lh)
                if sum(heights) <= STACK_H or budget <= 200:
                    break
                budget -= 30
            y = STACK_TOP + max(0, (STACK_H - sum(heights)) // 2)
            y = self._block(layer, boxes, m_lines, m_font, m_lh, y, CREAM)
            self._ornament(layer, y + 30)
            y = self._block(layer, boxes, t_lines, t_font, t_lh, y + 60, SOFT)
            self._block(layer, boxes, n_lines, n_font, n_lh, y + 40, GOLD)
            lines, font, lh = self._fit(tag_line, 38, 24, 60)
            self._block(layer, boxes, lines, font, lh, 1318, SOFT)
        else:  # outro
            self._line(layer, boxes, "ఎలా చదవాలి?", self._font(72), 460, GOLD)
            y = 610
            for text, start, color in (
                ("ప్రతి మంత్రం 11, 21 లేదా 108 సార్లు", 62, CREAM),
                ("శనివారం, నరసింహ జయంతి రోజున చదవడం శుభప్రదం", 50, CREAM),
                ("శుభ్రంగా, ప్రశాంతంగా కూర్చుని చదవండి", 50, SOFT),
            ):
                lines, font, lh = self._fit(text, start, 34, 190)
                y = self._block(layer, boxes, lines, font, lh, y, color) + 36
            self._ornament(layer, y + 10)
            lines, font, lh = self._fit(OPINION_TE, 46, 30, 150)
            y = self._block(layer, boxes, lines, font, lh, y + 60, GOLD) + 14
            lines, font, lh = self._fit(SUBSCRIBE_TE, 46, 30, 150)
            self._block(layer, boxes, lines, font, lh, y, CREAM)

        bg = self._background(spec, spec.handle).convert("RGBA")
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.alpha_composite(bg, layer).convert("RGB").save(out)
        return RenderedSlide(out, boxes)

    def render_all(self, spec: RequestShort, out_dir: Path) -> list[RenderedSlide]:
        return [self.render(spec, i, out_dir / f"{spec.slug}_{i + 1}.png") for i in range(len(spec.slides))]
