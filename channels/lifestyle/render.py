"""Scrolling lifestyle video: 1920x1080, a tall text strip scrolling up over a dimmed background, looped music.
Length is at least MIN_SECONDS (5 minutes) whatever the amount of text, so the scroll is slow and readable for an
older audience. Text sits inside x 260..1660 and fades under soft top and bottom bands, so nothing is cut hard."""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from channels.engine.render import _font, _mixed_font
from channels.lifestyle import topics

W, H = 1920, 1080
MIN_SECONDS = 330
COL_L, COL_R = 260, 1660
GOLD, WHITE, SOFT = (255, 214, 120), (255, 255, 255), (236, 226, 204)
REPO = Path(__file__).resolve().parents[2]
FONTS = REPO / "channels/engine/assets/fonts"
TELUGU_PLAIN = REPO / "assets/fonts/Ponnala-Regular.ttf"
TELUGU_LATIN = REPO / "assets/fonts/NotoSansTelugu-Variable.ttf"


def _fonts(lang: str, size: int, bold: bool = False):
    if lang == "te":
        return _mixed_font(TELUGU_LATIN, size, TELUGU_PLAIN, bold)
    return _font(FONTS / ("Hind-Bold.ttf" if bold else "Hind-Medium.ttf"), size)


def _wrap(draw, text: str, font, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def build_strip(lang: str, theme: dict, tops: list | None = None) -> Image.Image:
    """The whole scrolling text as one tall transparent image. `tops`, if given, is filled with each point's top y."""
    data = theme[lang]
    probe = ImageDraw.Draw(Image.new("L", (W, 10)))
    f_head, f_title = _fonts(lang, 96, True), _fonts(lang, 76, True)
    f_body, f_src, f_num = _fonts(lang, 58), _fonts(lang, 40), _fonts(lang, 64, True)
    f_cta = _fonts(lang, 60, True)
    text_l = COL_L + 140
    body_w = COL_R - text_l

    blocks = []  # (kind, lines, font, color, y_extra_after)
    blocks.append(("head", _wrap(probe, data["title"], f_head, COL_R - COL_L), f_head, GOLD, 150))
    for i, (title, body, src) in enumerate(data["points"], start=1):
        blocks.append(("num", [str(i)], f_num, (30, 20, 8), 0))
        blocks.append(("title", _wrap(probe, title, f_title, body_w), f_title, GOLD, 18))
        blocks.append(("body", _wrap(probe, body, f_body, body_w), f_body, WHITE, 16))
        blocks.append(("src", _wrap(probe, f"({src})", f_src, body_w), f_src, SOFT, 110))
    blocks.append(("cta", _wrap(probe, topics.CTA[lang], f_cta, COL_R - COL_L), f_cta, GOLD, 40))
    blocks.append(("cta", _wrap(probe, topics.DISCLAIMER[lang], f_src, COL_R - COL_L), f_src, SOFT, 0))

    total = 60
    for kind, lines, font, _c, after in blocks:
        if kind == "num":
            continue
        total += int(len(lines) * font.size * 1.5) + after
    strip = Image.new("RGBA", (W, total + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    y, point_top = 30, 0
    for kind, lines, font, color, after in blocks:
        if kind == "num":
            point_top = y
            if tops is not None:
                tops.append(y)
            r = 46
            cx, cy = COL_L + 50, point_top + 52
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
            w = d.textlength(lines[0], font=font)
            d.text((cx - w / 2, cy - font.size * 0.62), lines[0], font=font, fill=color)
            continue
        lh = int(font.size * 1.5)
        for ln in lines:
            if kind in ("head", "cta"):
                x = (W - d.textlength(ln, font=font)) / 2
            else:
                x = text_l
            d.text((x, y), ln, font=font, fill=color)
            y += lh
        y += after
    return strip.crop((0, 0, W, min(strip.height, y + 40)))


def background(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
    left, top = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(6))
    return Image.blend(img, Image.new("RGB", (W, H), (8, 6, 4)), 0.72)


def fade_bands() -> Image.Image:
    """Opaque dark bands at the top and bottom that fade into the picture, hiding the text's hard entry and exit."""
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = band.load()
    for y in range(H):
        a = 0
        if y < 150:
            a = int(235 * (1 - y / 150))
        elif y > H - 150:
            a = int(235 * ((y - (H - 150)) / 150))
        if a:
            for x in range(W):
                px[x, y] = (8, 6, 4, a)
    return band


def timing(strip_height: int, min_seconds: int = MIN_SECONDS) -> tuple[float, float]:
    """(duration, scroll speed in px/s)."""
    travel = strip_height + H - 300  # strip starts below the screen, ends mostly off the top
    duration = float(max(min_seconds, 60))
    return duration, travel / duration


def chapter_seconds(point_tops: list, strip_height: int, min_seconds: int = MIN_SECONDS) -> list[int]:
    """Second at which each point's top reaches the lower part of the screen (y=850)."""
    _d, speed = timing(strip_height, min_seconds)
    return [max(0, int((top + 80) / speed)) for top in point_tops]


def render(lang: str, theme: dict, bg_path: Path, music_path: Path, out: Path, workdir: Path,
           min_seconds: int = MIN_SECONDS, fps: int = 24, preview_seconds: int | None = None) -> float:
    workdir.mkdir(parents=True, exist_ok=True)
    strip = build_strip(lang, theme)
    strip.save(workdir / "strip.png")
    background(bg_path).save(workdir / "bg.png")
    fade_bands().save(workdir / "fade.png")
    duration, speed = timing(strip.height, min_seconds)
    run = float(preview_seconds) if preview_seconds else duration
    fc = (f"[0:v][1:v]overlay=x=0:y='{H - 150}-t*{speed:.4f}':eval=frame[a];[a][2:v]overlay=0:0,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-loop", "1", "-framerate", str(fps), "-t", f"{run}", "-i", str(workdir / "bg.png"),
           "-loop", "1", "-framerate", str(fps), "-t", f"{run}", "-i", str(workdir / "strip.png"),
           "-loop", "1", "-framerate", str(fps), "-t", f"{run}", "-i", str(workdir / "fade.png"),
           "-stream_loop", "-1", "-i", str(music_path),
           "-filter_complex", fc, "-map", "[v]", "-map", "3:a",
           "-t", f"{run}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(fps),
           "-c:a", "aac", "-b:a", "160k", "-af", "afade=t=in:d=2,afade=t=out:st=" + f"{max(run - 4, 0)}" + ":d=4",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return run
