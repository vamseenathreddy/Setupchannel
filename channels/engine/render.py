"""Generic static-text Short renderer shared by every Pattern-A channel in this repo
(Jesus Worship Waves, InfoShorts Telugu, Divine Mantra Sangam, Devotional Trance Beats).
Generalized from ramana/src/render.py, which pioneered this exact look (still used as-is by
Ramana Maharshi TV): Pillow for the still image layers, ffmpeg to mux a 5s video with music.
Completely still picture and text -- no motion, no scrolling -- per explicit request ("all
shorts should be static text").

Every channel supplies a `ChannelConfig` (see channel_config.py in each channels/<name>/
folder) describing its own fonts, colors, text block order (which of text_primary/
text_secondary is drawn first -- e.g. Jesus Worship Waves draws English first and Telugu
below, the reverse of every other channel here) and asset locations. This module contains
no channel-specific text, language, or color choices of its own.
"""
import dataclasses
import datetime as dt
import glob
import hashlib
import random
import subprocess
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SAFE_TOP, SAFE_BOTTOM = 400, 1480
PHOTO_BOX_H = 1500
SHOW_SOURCE_ON_VIDEO = False
PHOTO_TEXT_BOTTOM = 1600
PHOTO_TEXT_H = 640
MAX_TEXT_W = 940
SCALES = [1.0, 0.94, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58, 0.52]

CREAM, GOLD, WHITE, SOFT = (255, 236, 196), (244, 190, 90), (245, 245, 245), (210, 205, 195)

# Default 4-layout rotation (anchor position + color roles), identical shape to ramana's
# LAYOUTS -- a channel can override via ChannelConfig.layouts.
DEFAULT_LAYOUTS = [
    dict(anchor=0.50, primary=CREAM, secondary=WHITE, accent=GOLD, ornament=True),
    dict(anchor=0.42, primary=GOLD, secondary=WHITE, accent=CREAM, ornament=False),
    dict(anchor=0.55, primary=(255, 245, 225), secondary=SOFT, accent=GOLD, ornament=True),
    dict(anchor=0.47, primary=CREAM, secondary=(255, 214, 140), accent=WHITE, ornament=False),
]
DEFAULT_PALETTES = [  # fallback gradients when no photos are in assets/backgrounds
    ((10, 16, 40), (36, 52, 104)),
    ((8, 28, 34), (22, 84, 82)),
    ((24, 12, 44), (84, 40, 112)),
    ((10, 14, 24), (46, 58, 78)),
]


@dataclasses.dataclass
class TextBlock:
    field: str            # "text_primary" or "text_secondary" on the content row
    font: Path
    size: int
    color_key: str         # "primary" | "secondary" | "accent" -- looked up in the active layout
    bold: bool = True
    strip_chars: str = ""  # characters to strip before drawing (e.g. a font with no quote-mark glyphs)


@dataclasses.dataclass
class ChannelConfig:
    channel_name: str
    assets_dir: Path                 # contains backgrounds/, fonts/, and the music files
    blocks: list[TextBlock]          # drawn top to bottom, in this order
    font_channel_label: Path         # light font for the small channel-name watermark
    music_glob: str = "*.mp3"
    layouts: list = dataclasses.field(default_factory=lambda: DEFAULT_LAYOUTS)
    palettes: list = dataclasses.field(default_factory=lambda: DEFAULT_PALETTES)
    photo_box_override: dict = dataclasses.field(default_factory=dict)  # {"photo_04.jpg": 1020}
    zoom: float = 0.0                # 0 = completely still picture


def _font(path, size):
    return ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)


def _wrap(draw, text, font, stroke):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=font, features=None) + 2 * stroke <= MAX_TEXT_W or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _seed(row, date_key):
    return int(hashlib.sha256(f"{row['id']}-{date_key}".encode()).hexdigest(), 16)


def _cover(img, top_bias=0.3):
    scale = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
    left, top = (img.width - W) // 2, int((img.height - H) * top_bias)
    return img.crop((left, top, left + W, top + H))


def photo_for(date_key, cfg: ChannelConfig):
    """Rotate through every photo in order (by date) so none repeats until all have been used."""
    photos = sorted(
        p for ext in ("jpg", "jpeg", "png", "webp")
        for p in glob.glob(str(cfg.assets_dir / f"backgrounds/*.{ext}"))
    )
    if not photos:
        return None
    return photos[dt.date.fromisoformat(date_key).toordinal() % len(photos)]


def make_background(rng, date_key, cfg: ChannelConfig):
    photo = photo_for(date_key, cfg)
    if photo:
        src = Image.open(photo).convert("RGB")
        back = _cover(src).filter(ImageFilter.GaussianBlur(40))
        back = Image.blend(back, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)
        k = min(W / src.width, cfg.photo_box_override.get(Path(photo).name, PHOTO_BOX_H) / src.height)
        fg = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
        y = 0 if fg.height >= 1300 else max(120, int(H * 0.38 - fg.height / 2))
        mask = Image.new("L", fg.size, 255)
        fade = min(160, fg.height // 5)
        md = ImageDraw.Draw(mask)
        for i in range(fade):
            md.line((0, fg.height - fade + i, fg.width, fg.height - fade + i), fill=int(255 * (1 - i / fade)))
        if y > 0:
            for i in range(40):
                md.line((0, i, fg.width, i), fill=int(255 * i / 40))
        if fg.width < W:
            for i in range(30):
                v = int(255 * i / 30)
                md.line((i, 0, i, fg.height), fill=min(v, 255))
                md.line((fg.width - 1 - i, 0, fg.width - 1 - i, fg.height), fill=min(v, 255))
        back.paste(fg, ((W - fg.width) // 2, y), mask)
        shade = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(shade)
        for yy in range(900, H):
            sd.line((0, yy, W, yy), fill=int(255 * 0.70 * min(1.0, (yy - 900) / 600)))
        img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), back, shade)
    else:
        c1, c2 = rng.choice(cfg.palettes)
        grad = Image.linear_gradient("L").resize((W, H))
        img = Image.composite(Image.new("RGB", (W, H), c2), Image.new("RGB", (W, H), c1), grad)
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse((W // 2 - 420, 520, W // 2 + 420, 1360), fill=70)
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        img = Image.composite(Image.new("RGB", (W, H), (255, 210, 140)), img, glow)
    scrim = Image.new("L", (W, H), 135)
    grad = Image.linear_gradient("L").resize((W, H))
    top_dark = grad.point(lambda v: max(0, 170 - v))
    bot_dark = grad.point(lambda v: max(0, v - 90))
    scrim.paste(top_dark, (0, 0), top_dark)
    scrim.paste(bot_dark, (0, 0), bot_dark)
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, scrim)


def _blocks(row, layout, cfg: ChannelConfig):
    out = []
    for b in cfg.blocks:
        text = (row.get(b.field) or "").strip()
        if b.strip_chars:
            text = text.translate({ord(c): None for c in b.strip_chars})
        text = " ".join(s.strip() for s in text.split("|") if s.strip())
        if text:
            out.append((text, b.font, b.size, layout[b.color_key], b.bold))
    return out


def fit_text(row, layout, cfg: ChannelConfig, max_h=None):
    """Largest scale at which the text block fits. Returns (laid, total_height, fits, scale)."""
    probe = ImageDraw.Draw(Image.new("L", (W, H)))
    limit = max_h or SAFE_BOTTOM - SAFE_TOP
    blocks = _blocks(row, layout, cfg)
    for scale in SCALES:
        laid, total = [], 0
        for text, path, size, color, bold in blocks:
            px = int(size * scale)
            stroke = max(1, px // 55) if bold else 0
            font = _font(path, px)
            lines = _wrap(probe, text, font, stroke)
            lh = int(px * 1.45)
            laid.append((lines, font, color, stroke, lh))
            total += len(lines) * lh + 34
        total += 90 if SHOW_SOURCE_ON_VIDEO else 50
        if total <= limit:
            return laid, total, True, scale
    return laid, total, False, scale


def make_text_layer(row, layout, cfg: ChannelConfig, label_primary="", label_secondary="",
                     max_h=None, bottom=None, channel=True):
    laid, total, _fits, _scale = fit_text(row, layout, cfg, max_h)

    text_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("L", (W, H), 0)
    d, sd = ImageDraw.Draw(text_l), ImageDraw.Draw(shadow)
    y = int(layout["anchor"] * H - total / 2)
    y = max(SAFE_TOP + 40, min(y, (bottom or SAFE_BOTTOM) - total))

    if layout.get("ornament"):
        d.line((W // 2 - 70, y, W // 2 + 70, y), fill=layout["accent"], width=3)
    y += 40
    for lines, font, color, stroke, lh in laid:
        for ln in lines:
            w = d.textlength(ln, font=font)
            xy = ((W - w) / 2, y)
            sd.text(xy, ln, font=font, fill=255, stroke_width=stroke + 2)
            d.text(xy, ln, font=font, fill=color, stroke_width=stroke, stroke_fill=color)
            y += lh
        y += 34

    if label_primary or label_secondary:  # special day header
        label_font = cfg.blocks[0].font
        tf, ef = _font(label_font, 64), _font(cfg.font_channel_label, 34)
        for txt, f, yy, col in ((label_secondary, tf, 250, GOLD), (f"Today: {label_primary}", ef, 340, WHITE)):
            if txt:
                xy = ((W - d.textlength(txt, font=f)) / 2, yy)
                sd.text(xy, txt, font=f, fill=255, stroke_width=3)
                d.text(xy, txt, font=f, fill=col)

    if channel:
        cf = _font(cfg.font_channel_label, 30)
        d.text(((W - d.textlength(cfg.channel_name, font=cf)) / 2, 1560), cfg.channel_name, font=cf, fill=SOFT)

    blur = shadow.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.8))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    shade.putalpha(blur)
    return Image.alpha_composite(shade, text_l)


def pick_music(rng, cfg: ChannelConfig):
    clips = sorted(glob.glob(str(cfg.assets_dir / cfg.music_glob)))
    if not clips:
        raise SystemExit(f"No music matching {cfg.music_glob} found under {cfg.assets_dir}. Add music first.")
    return rng.choice(clips)


def render(row, out_mp4, date_key, cfg: ChannelConfig, special=None, workdir="out", duration=5.0):
    rng = random.Random(_seed(row, date_key))
    layout_idx = rng.randrange(len(cfg.layouts))
    layout = cfg.layouts[layout_idx]
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    bg_path, tx_path = work / "bg.png", work / "text.png"
    make_background(rng, date_key, cfg).save(bg_path)
    max_h, bottom, channel = None, None, True
    if photo_for(date_key, cfg):  # keep faces clear: text sits at the bottom, below the photo
        layout = dict(layout, anchor=0.78)
        max_h, bottom, channel = PHOTO_TEXT_H, PHOTO_TEXT_BOTTOM, False
    make_text_layer(
        row, layout, cfg,
        (special or {}).get("label_primary", ""), (special or {}).get("label_secondary", ""),
        max_h, bottom, channel,
    ).save(tx_path)
    music = pick_music(rng, cfg)
    if cfg.zoom > 0:
        bg_f = (f"[0:v]scale=2160:3840,zoompan=z='1+{cfg.zoom}*sin(PI*on/150)':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30[bg];")
    else:
        bg_f = "[0:v]scale=1080:1920,setsar=1[bg];"
    fc = bg_f + "[1:v]format=rgba[tx];[bg][tx]overlay=format=auto,format=yuv420p[v]"
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-loop", "1", "-framerate", "30", "-t", str(duration), "-i", str(bg_path),
        "-loop", "1", "-framerate", "30", "-t", str(duration), "-i", str(tx_path),
        "-i", music,
        "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
        "-t", str(duration), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return {"music": Path(music).name, "layout": layout_idx, "photo": Path(photo_for(date_key, cfg) or "gradient").name}
