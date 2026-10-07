"""
stotra_video.py: renders a weekly long-form STOTRA / MANTRA video
(landscape 1920x1080) from a deity background image + Telugu lyric
pages + the supplied audio, plus a 1280x720 thumbnail. Built 2026-10-07
after the channel analytics showed long-form devotional videos earn
about 30x more per view than Shorts, and that Kamakhya videos are
evergreen.

Design choices (audience is 35-64+, mostly on phones and TV):
  * big plain-Ponnala Telugu, high contrast, a few lines per page
  * one lyric page at a time (no scrolling), pages share the audio
    length evenly, cycling when the audio is repeated
  * every text block is laid out top to bottom inside its own zone and
    shrunk until it fits, so no text can overlap other text
  * the dim channel-handle watermark is not used here: this is a
    landscape video and the standing no-overlap rule applies

Content lives in content/stotras/<slug>.json (see _template.json).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from mahanavi.exceptions import VideoAssemblyError
from mahanavi.images.fonts import FontManager

W, H = 1920, 1080
TW, TH = 1280, 720
GOLD = (255, 214, 120)
WHITE = (255, 255, 255)
SOFT = (225, 220, 210)
TITLE_SECONDS = 6.0
END_SECONDS = 8.0
SUBSCRIBE_TE = "ప్రతి శుక్రవారం కొత్త స్తోత్రం కోసం సబ్‌స్క్రైబ్ చేయండి"
SUBSCRIBE_EN = "Subscribe for a new stotram every Friday"
HANDLE = "Mahanavi Spirituals"


@dataclass
class StotraSpec:
    slug: str
    deity_te: str
    deity_en: str
    title_te: str
    title_en: str
    pages: list[dict]
    repeat: int = 1
    audio: str = ""
    background: str = ""
    intro_te: str = ""
    intro_en: str = ""
    tags: list[str] = field(default_factory=list)

    @staticmethod
    def load(path: Path) -> "StotraSpec":
        raw = json.loads(path.read_text(encoding="utf-8"))
        spec = StotraSpec(**{k: v for k, v in raw.items() if k in StotraSpec.__dataclass_fields__})
        spec.validate()
        return spec

    def validate(self) -> None:
        if not self.pages:
            raise VideoAssemblyError("Stotra spec has no lyric pages yet: add the Telugu lyrics first.")
        for i, page in enumerate(self.pages):
            if not [ln for ln in page.get("te", []) if ln.strip()]:
                raise VideoAssemblyError(f"Lyric page {i + 1} has no Telugu lines.")
        if self.repeat < 1:
            raise VideoAssemblyError("repeat must be at least 1.")


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def _fallback_bg(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(0, w, 4):
            t = y / h
            c = (int(90 - 50 * t), int(20 - 10 * t), int(30 - 10 * t))
            for dx in range(4):
                if x + dx < w:
                    px[x + dx, y] = c
    return img


def _background(path: Path | None, w: int, h: int, brightness: float) -> Image.Image:
    img = _cover(Image.open(path), w, h) if path and path.exists() else _fallback_bg(w, h)
    img = img.filter(ImageFilter.GaussianBlur(2))
    return Image.eval(img, lambda v: int(v * brightness))


def _wrap_plain(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    words: list[str] = []
    for tok in text.split():
        # a lone danda mark stays glued to the word before it (never alone on a line)
        if tok in ("।", "॥") and words:
            words[-1] = f"{words[-1]} {tok}"
        else:
            words.append(tok)
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _fit_block(draw, fonts: FontManager, lines: list[str], max_w: int, max_h: int,
               start: int, floor: int, spacing: float = 1.5) -> tuple[list[str], object, int]:
    """Largest font size at which every (wrapped) line fits max_w and the
    block fits max_h. Returns (lines, font, line_height). Sizes at which
    every given line fits on ONE row are preferred (verse lines stay
    intact); wrapping is only used when no size down to 60 achieves it."""
    for size in range(start, max(floor, 60) - 1, -2):
        font = fonts.get_font(size)
        if all(draw.textlength(ln, font=font) <= max_w for ln in lines) and int(size * spacing) * len(lines) <= max_h:
            return list(lines), font, int(size * spacing)
    for size in range(start, floor - 1, -2):
        font = fonts.get_font(size)
        wrapped: list[str] = []
        for ln in lines:
            wrapped.extend(_wrap_plain(draw, ln, font, max_w))
        lh = int(size * spacing)
        if lh * len(wrapped) <= max_h:
            return wrapped, font, lh
    font = fonts.get_font(floor)
    wrapped = []
    for ln in lines:
        wrapped.extend(_wrap_plain(draw, ln, font, max_w))
    return wrapped, font, int(floor * spacing)


def _centered(draw, lines, font, lh, y, fill, canvas_w) -> int:
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(((canvas_w - w) / 2, y), ln, font=font, fill=fill)
        y += lh
    return y


def render_page(fonts: FontManager, bg: Image.Image, header: str, body_te: list[str],
                body_en: str = "", kind: str = "lyrics", sub_en: str = "") -> Image.Image:
    """One 1920x1080 frame. Zones (top to bottom, never shared):
    header 40-130, panel 160-960, footer 990-1050."""
    frame = bg.copy().convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([140, 160, W - 140, 960], radius=36, fill=(0, 0, 0, 150))
    frame = Image.alpha_composite(frame, overlay)
    draw = ImageDraw.Draw(frame)

    # Header zone
    hl, hf, hlh = _fit_block(draw, fonts, [header], W - 400, 90, 52, 34)
    _centered(draw, hl[:1], hf, hlh, 50, GOLD, W)

    # Panel zone, inner box with padding
    pad_x, pad_top, pad_bottom = 80, 50, 50
    inner_w = (W - 280) - 2 * pad_x
    inner_h = 800 - pad_top - pad_bottom
    en_lines: list[str] = []
    en_font = None
    en_lh = 0
    en_h = 0
    if body_en.strip():
        en_font = fonts.get_font(38)
        en_lines = _wrap_plain(draw, body_en.strip(), en_font, inner_w)[:3]
        en_lh = int(38 * 1.4)
        en_h = en_lh * len(en_lines) + 24
    te_max = inner_h - en_h
    start = 110 if kind in ("title", "end") else 88
    te_lines, te_font, te_lh = _fit_block(draw, fonts, body_te, inner_w, te_max, start, 40)
    block_h = te_lh * len(te_lines) + en_h
    y = 160 + pad_top + max(0, (inner_h - block_h) // 2)
    y = _centered(draw, te_lines, te_font, te_lh, y, WHITE if kind == "lyrics" else GOLD, W)
    if en_lines:
        y += 24
        _centered(draw, en_lines, en_font, en_lh, y, SOFT, W)
    if sub_en:
        sf = fonts.get_font(40)
        _centered(draw, [sub_en], sf, 56, 905 - 8, SOFT, W)

    # Footer zone
    ff = fonts.get_font(30)
    fw = draw.textlength(HANDLE, font=ff)
    draw.text((W - 100 - fw, 1000), HANDLE, font=ff, fill=(200, 190, 170))
    return frame.convert("RGB")


def render_thumbnail(fonts: FontManager, spec: StotraSpec, bg_path: Path | None, out: Path) -> Path:
    bg = _background(bg_path, TW, TH, 0.7)
    draw = ImageDraw.Draw(bg)
    band = Image.new("RGBA", (TW, 330), (0, 0, 0, 170))
    base = bg.convert("RGBA")
    base.alpha_composite(band, (0, TH - 330 - 30))
    bg = base.convert("RGB")
    draw = ImageDraw.Draw(bg)
    lines, font, lh = _fit_block(draw, fonts, [spec.deity_te], TW - 160, 170, 130, 60, 1.35)
    y = TH - 330 - 30 + 25
    for ln in lines[:1]:
        w = draw.textlength(ln, font=font)
        draw.text(((TW - w) / 2, y), ln, font=font, fill=GOLD, stroke_width=3, stroke_fill=(0, 0, 0))
    y += lh + 10
    sub = f"{spec.deity_en} Stotram · Telugu Lyrics" if "stot" in spec.title_en.lower() else f"{spec.deity_en} · Telugu Lyrics"
    sl, sf, slh = _fit_block(draw, fonts, [sub], TW - 160, 90, 56, 32, 1.3)
    _centered(draw, sl[:1], sf, slh, y, WHITE, TW)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out, "JPEG", quality=92)
    return out


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise VideoAssemblyError(f"{cmd[0]} failed: {proc.stderr[-800:]}")


def audio_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise VideoAssemblyError(f"ffprobe failed for {path}: {proc.stderr[-300:]}")
    return float(proc.stdout.strip())


def plan_segments(total: float, n_pages: int, repeat: int) -> list[tuple[str, int, float]]:
    """[(kind, page_index, seconds)] covering `total` exactly:
    title, then lyric pages cycled `repeat` times, then end card."""
    body = total - TITLE_SECONDS - END_SECONDS
    if body < n_pages * 3:
        raise VideoAssemblyError(f"Audio too short ({total:.0f}s) for {n_pages} lyric pages.")
    per_page = body / (repeat * n_pages)
    segs = [("title", 0, TITLE_SECONDS)]
    for _ in range(repeat):
        for i in range(n_pages):
            segs.append(("lyrics", i, per_page))
    segs.append(("end", 0, END_SECONDS))
    return segs


def build_video(spec: StotraSpec, audio_path: Path, bg_path: Path | None, work_dir: Path, out_path: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    from mahanavi.config import get_settings
    fonts = FontManager(get_settings().telugu_font_path)
    bg = _background(bg_path, W, H, 0.38)

    single = audio_duration(audio_path)
    total = single * spec.repeat
    segs = plan_segments(total, len(spec.pages), spec.repeat)

    cache: dict[tuple[str, int], Path] = {}
    entries: list[tuple[Path, float]] = []
    for kind, idx, secs in segs:
        key = (kind, idx)
        if key not in cache:
            if kind == "title":
                img = render_page(fonts, bg, "Telugu Lyrics", [spec.deity_te, spec.title_te],
                                  "", "title", sub_en=spec.title_en)
            elif kind == "end":
                img = render_page(fonts, bg, spec.deity_te, [SUBSCRIBE_TE], SUBSCRIBE_EN, "end")
            else:
                page = spec.pages[idx]
                img = render_page(fonts, bg, spec.deity_te, [ln for ln in page["te"] if ln.strip()],
                                  page.get("en", ""), "lyrics")
            p = work_dir / f"page_{kind}_{idx:02d}.png"
            img.save(p)
            cache[key] = p
        entries.append((cache[key], secs))

    concat = work_dir / "pages.txt"
    lines = []
    for p, secs in entries:
        lines.append(f"file '{p.resolve()}'\nduration {secs:.3f}\n")
    lines.append(f"file '{entries[-1][0].resolve()}'\n")
    concat.write_text("".join(lines))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat)]
    if spec.repeat > 1:
        cmd += ["-stream_loop", str(spec.repeat - 1)]
    cmd += ["-i", str(audio_path),
            "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage",
            "-preset", "veryfast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total:.3f}", "-movflags", "+faststart", str(out_path)]
    _run(cmd)
    return out_path


@dataclass
class StotraSeo:
    title: str
    hashtags: list[str]
    description: str

    def full_caption(self) -> str:
        return self.description[:4900]


def build_seo(spec: StotraSpec, playlist_url: str = "") -> StotraSeo:
    title = f"{spec.title_te} | {spec.title_en} | Telugu Lyrics"
    if len(title) > 100:
        title = f"{spec.title_te} | {spec.title_en}"[:100]
    lyric_text = "\n\n".join("\n".join(ln for ln in p["te"] if ln.strip()) for p in spec.pages)
    tags = ["#" + t.lstrip("#").replace(" ", "") for t in (spec.tags or [])]
    base = ["#TeluguDevotional", "#Stotram", "#MahanaviSpirituals"]
    hashtags = []
    for t in tags + base:
        if t not in hashtags:
            hashtags.append(t)
    parts = []
    if spec.intro_te:
        parts.append(spec.intro_te)
    if spec.intro_en:
        parts.append(spec.intro_en)
    parts.append(f"{spec.title_te}\n{spec.title_en}")
    parts.append("సాహిత్యం / Lyrics:\n\n" + lyric_text)
    parts.append(SUBSCRIBE_TE + "\n" + SUBSCRIBE_EN)
    if playlist_url:
        parts.append("మరిన్ని స్తోత్రాలు / More stotrams: " + playlist_url)
    parts.append(" ".join(hashtags[:15]))
    return StotraSeo(title=title, hashtags=hashtags[:15], description="\n\n".join(parts))
