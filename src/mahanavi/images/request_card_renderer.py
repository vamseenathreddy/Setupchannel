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

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from mahanavi.config import Settings
from mahanavi.content.request_shorts import RequestShort, Slide
from mahanavi.images.fonts import FontManager
from mahanavi.video.watermark import bake_watermark

W, H = 1080, 1920
SAFE_L, SAFE_R, SAFE_TOP, SAFE_BOTTOM = 150, 930, 230, 1385
TEXT_W = SAFE_R - SAFE_L
GOLD, CREAM, SOFT = (240, 196, 92), (255, 246, 226), (214, 206, 224)
STACK_TOP, STACK_H = 560, 700   # mantra / transliteration / meaning band (ends well above the footer tag at 1318)
ENGINE_FONTS = Path(__file__).resolve().parents[3] / "channels" / "engine" / "assets" / "fonts"


PHOTO_DROP = 330  # px the deity photo is moved down so the face clears the mantra text
Box = tuple[int, int, int, int]


@dataclass
class RenderedSlide:
    path: Path
    boxes: list[Box] = field(default_factory=list)  # every drawn text line, for tests


class RequestCardRenderer:
    def __init__(self, settings: Settings) -> None:
        self._fonts = FontManager(settings.telugu_font_path)
        self._probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
        self._assets_dir = settings.assets_dir

    # ---- helpers -----------------------------------------------------------------------------
    lang = "te"

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if self.lang == "hi":  # Devanagari: Hind (Telugu font has no Devanagari glyphs)
            return ImageFont.truetype(str(ENGINE_FONTS / "Hind-Bold.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
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

    def _photo_background(self, spec: RequestShort) -> Image.Image | None:
        """Deity photo, cover-fit and dimmed (darker behind the text band) so the text stays readable.
        None if the file is missing/unreadable, so the plain gradient is used instead."""
        path = self._assets_dir / "images" / spec.bg_image
        try:
            with Image.open(path) as raw:
                src = raw.convert("RGB")
        except OSError:
            return None
        # Soft blurred copy fills the frame; the sharp photo sits LOWER than centre so the deity's face falls
        # below the mantra text instead of behind it (the stack above ends around y 1100).
        base = ImageOps.fit(src, (W, H), method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        sharp = ImageOps.fit(src, (W, H), method=Image.Resampling.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
        drop = PHOTO_DROP
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        for y in range(H - drop):  # fade the photo's top edge into the blurred fill
            md.line((0, y + drop, W, y + drop), fill=min(255, int(255 * y / 160)))
        base.paste(sharp.crop((0, 0, W, H - drop)).transform((W, H), Image.Transform.AFFINE, (1, 0, 0, 0, 1, -drop)), (0, 0), mask)
        im = base
        shade = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(shade)
        for y in range(H):  # darker behind the text band (y 230-1100), lighter lower where the face is
            t = 1 - abs((y - 640) / 640)
            sd.line((0, y, W, y), fill=int(70 + 130 * max(0.0, min(1.0, t))))
        im = Image.composite(Image.new("RGB", (W, H), (10, 4, 4)), im, shade)
        d = ImageDraw.Draw(im)
        d.rectangle((30, 30, W - 30, H - 30), outline=GOLD, width=4)
        d.rectangle((42, 42, W - 42, H - 42), outline=GOLD, width=2)
        return bake_watermark(im.convert("RGBA"), handle=spec.watermark).convert("RGB")

    def _background(self, spec: RequestShort) -> Image.Image:
        if spec.bg_image:
            photo = self._photo_background(spec)
            if photo is not None:
                return photo
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
        return bake_watermark(im.convert("RGBA"), handle=spec.watermark).convert("RGB")

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
        self.lang = spec.lang
        slide: Slide = spec.slides[index]
        boxes: list[Box] = []
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

        if slide.kind == "intro":
            self._line(layer, boxes, slide.label, self._font(52), 470, GOLD)
            lines, font, lh = self._fit(slide.text, 120, 70, 420, 1.3)
            y = self._block(layer, boxes, lines, font, lh, 600, CREAM)
            self._ornament(layer, y + 40)
            lines, font, lh = self._fit(slide.translit, 52, 34, 170)
            y = self._block(layer, boxes, lines, font, lh, y + 90, SOFT)
            lines, font, lh = self._fit(slide.meaning, 60, 30, 130)
            self._block(layer, boxes, lines, font, lh, y + 40, GOLD)
        elif slide.kind == "mantra":
            mantra_idx = sum(1 for x in spec.slides[:index] if x.kind == "mantra")
            total = sum(1 for x in spec.slides if x.kind == "mantra")
            if spec.header:
                if self._probe.textlength(spec.header, font=self._font(40)) <= TEXT_W:
                    self._line(layer, boxes, spec.header, self._font(40), 262, SOFT)
                else:  # long header (festival name): wrap onto two lines instead of overflowing the safe zone
                    lines, font, lh = self._fit(spec.header, 38, 26, 90)
                    self._block(layer, boxes, lines, font, lh, 250, SOFT)
            if total > 1:
                self._dots(layer, mantra_idx, total, 345)
            lines, font, lh = self._fit(slide.label, 76, 52, 110)
            self._block(layer, boxes, lines, font, lh, 420, GOLD)
            # Fit the three blocks into the band between the heading and the footer tag: shrink the mantra a
            # little at a time until the whole stack fits, so a long verse never crowds the footer.
            budget = 430
            while True:
                m_lines, m_font, m_lh = self._fit(slide.text, 92, 44, budget)
                t_lines, t_font, t_lh = self._fit(slide.translit, 42, 28, 190, 1.35)
                n_lines, n_font, n_lh = self._fit(slide.meaning, 44, 30, 150)
                heights = (len(m_lines) * m_lh, 60, len(t_lines) * t_lh, 40, len(n_lines) * n_lh)
                if sum(heights) <= STACK_H or budget <= 200:
                    break
                budget -= 30
            y = STACK_TOP + max(0, (STACK_H - sum(heights)) // 2)
            y = self._block(layer, boxes, m_lines, m_font, m_lh, y, CREAM)
            self._ornament(layer, y + 30)
            y = self._block(layer, boxes, t_lines, t_font, t_lh, y + 60, SOFT)
            self._block(layer, boxes, n_lines, n_font, n_lh, y + 40, GOLD)
            if spec.tag_footer:
                lines, font, lh = self._fit(spec.tag_footer, 38, 24, 60)
                self._block(layer, boxes, lines, font, lh, 1318, SOFT)
        elif slide.kind == "points":
            if spec.header:
                self._line(layer, boxes, spec.header, self._font(40), 262, SOFT)
            self._line(layer, boxes, slide.label, self._font(72), 360, GOLD)
            points = slide.text.split("\n")
            budget = 1290 - 520
            per = budget // len(points) - 70
            blocks = []
            size_cap = 62
            while True:
                blocks = [self._fit(pt, size_cap, 30, max(per, 80)) for pt in points]
                total = sum(len(b[0]) * b[2] for b in blocks) + 70 * (len(points) - 1)
                if total <= budget or size_cap <= 34:
                    break
                size_cap -= 4
            y = 520 + max(0, (budget - total) // 2)
            for i, (lines, font, lh) in enumerate(blocks):
                y = self._block(layer, boxes, lines, font, lh, y, CREAM if i % 2 == 0 else SOFT)
                if i < len(blocks) - 1:
                    self._ornament(layer, y + 35)
                    y += 70
        else:  # outro
            self._line(layer, boxes, slide.label, self._font(72), 460, GOLD)
            y = 610
            for k, text in enumerate(slide.text.split("\n")):
                lines, font, lh = self._fit(text, 62 if k == 0 else 50, 34, 190)
                y = self._block(layer, boxes, lines, font, lh, y, CREAM if k < 2 else SOFT) + 36
            self._ornament(layer, y + 10)
            y += 60
            for k, text in enumerate(spec.cta_lines):
                lines, font, lh = self._fit(text, 46, 30, 150)
                y = self._block(layer, boxes, lines, font, lh, y, GOLD if k == 0 else CREAM) + 14

        bg = self._background(spec).convert("RGBA")
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.alpha_composite(bg, layer).convert("RGB").save(out)
        return RenderedSlide(out, boxes)

    def render_all(self, spec: RequestShort, out_dir: Path) -> list[RenderedSlide]:
        return [self.render(spec, i, out_dir / f"{spec.slug}_{i + 1}.png") for i in range(len(spec.slides))]
