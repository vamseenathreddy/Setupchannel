"""Render one 5 second, 1080x1920 bilingual Short: image layers via Pillow, video via ffmpeg."""
import glob
import hashlib
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .common import ROOT

W, H = 1080, 1920
SAFE_TOP, SAFE_BOTTOM = 400, 1385
PHOTO_BOX_H = 1500                  # photos are fitted to the full width, this only caps very tall ones
PHOTO_BOX_OVERRIDE = {"photo_04.jpg": 1020, "photo_09.jpg": 1220}  # face-heavy photos: smaller so the chin stays above the text
SHOW_SOURCE_ON_VIDEO = False        # the source is always in the YouTube description
PHOTO_TEXT_BOTTOM = 1600            # keep clear of the Shorts UI overlays
PHOTO_TEXT_H = 680
MAX_TEXT_W = 780
ZOOM = 0.0                          # 0 = completely still picture. Try 0.03 for a slow breathing zoom (loops seamlessly)
FONT_TE = ROOT / "assets/fonts/Ponnala-Regular.ttf"  # only one weight exists; plain Regular is used (no synthetic bold, owner request 2026-10-07)
FONT_EN = ROOT / "assets/fonts/Poppins-Bold.ttf"      # bold, to match the weight of the Telugu text
FONT_EN_LIGHT = ROOT / "assets/fonts/Poppins-Regular.ttf"
CHANNEL = "Ramana Maharshi TV"
HANDLE = "@ramanamaharshitv"

CREAM, GOLD, WHITE, SOFT = (255, 236, 196), (244, 190, 90), (245, 245, 245), (210, 205, 195)

# Four layouts rotated per Short so the feed does not look mass produced.
LAYOUTS = [
    dict(anchor=0.50, te=CREAM, en=WHITE, accent=GOLD, ornament=True),
    dict(anchor=0.42, te=GOLD, en=WHITE, accent=CREAM, ornament=False),
    dict(anchor=0.55, te=(255, 245, 225), en=SOFT, accent=GOLD, ornament=True),
    dict(anchor=0.47, te=CREAM, en=(255, 214, 140), accent=WHITE, ornament=False),
]
PALETTES = [  # fallback gradients when no photos are in assets/backgrounds (no brown tones)
    ((10, 16, 40), (36, 52, 104)),   # deep indigo
    ((8, 28, 34), (22, 84, 82)),     # deep teal
    ((24, 12, 44), (84, 40, 112)),   # dark violet
    ((10, 14, 24), (46, 58, 78)),    # charcoal blue
]


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


def photo_for(date_key):
    """Rotate through every photo in order (by date) so none repeats until all have been used."""
    photos = sorted(p for ext in ("jpg", "jpeg", "png", "webp") for p in glob.glob(str(ROOT / f"assets/backgrounds/*.{ext}")))
    if not photos:
        return None
    return photos[__import__("datetime").date.fromisoformat(date_key).toordinal() % len(photos)]


def make_background(rng, date_key):
    photo = photo_for(date_key)
    if photo:
        src = Image.open(photo).convert("RGB")
        # blurred, darkened full-screen copy behind; the sharp photo is fitted to the width on top
        back = _cover(src).filter(ImageFilter.GaussianBlur(40))
        back = Image.blend(back, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)
        k = min(W / src.width, PHOTO_BOX_OVERRIDE.get(Path(photo).name, PHOTO_BOX_H) / src.height)
        fg = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
        y = 0 if fg.height >= 1300 else max(120, int(H * 0.38 - fg.height / 2))
        mask = Image.new("L", fg.size, 255)
        fade = min(160, fg.height // 5)
        md = ImageDraw.Draw(mask)
        for i in range(fade):  # soft fade of the bottom edge into the backdrop
            md.line((0, fg.height - fade + i, fg.width, fg.height - fade + i), fill=int(255 * (1 - i / fade)))
        if y > 0:
            for i in range(40):
                md.line((0, i, fg.width, i), fill=int(255 * i / 40))
        if fg.width < W:  # feather the left and right edges into the blurred backdrop
            for i in range(30):
                v = int(255 * i / 30)
                md.line((i, 0, i, fg.height), fill=min(v, 255))
                md.line((fg.width - 1 - i, 0, fg.width - 1 - i, fg.height), fill=min(v, 255))
        back.paste(fg, ((W - fg.width) // 2, y), mask)
        shade = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(shade)
        for yy in range(900, H):  # reading gradient: clear above 900, 70% dark by 1500
            sd.line((0, yy, W, yy), fill=int(255 * 0.70 * min(1.0, (yy - 900) / 600)))
        img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), back, shade)
    else:
        c1, c2 = rng.choice(PALETTES)
        grad = Image.linear_gradient("L").resize((W, H))
        img = Image.composite(Image.new("RGB", (W, H), c2), Image.new("RGB", (W, H), c1), grad)
        glow = Image.new("L", (W, H), 0)
        ImageDraw.Draw(glow).ellipse((W // 2 - 420, 520, W // 2 + 420, 1360), fill=70)
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        img = Image.composite(Image.new("RGB", (W, H), (255, 210, 140)), img, glow)
    # readability scrim: darker at top and bottom, softly dark in the middle
    scrim = Image.new("L", (W, H), 135)
    grad = Image.linear_gradient("L").resize((W, H))
    top_dark = grad.point(lambda v: max(0, 170 - v))
    bot_dark = grad.point(lambda v: max(0, v - 90))
    scrim = Image.eval(scrim, lambda v: v)
    scrim.paste(top_dark, (0, 0), top_dark)
    scrim.paste(bot_dark, (0, 0), bot_dark)
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, scrim)


ATTR_TE, ATTR_EN = "- భగవాన్ రమణ మహర్షి", "- Bhagavan Ramana Maharshi"
ATTRIBUTED = ("quote", "qa")  # his own teachings; life facts are about him, so no attribution line there

# The Om clip owner approved on 2026-10-08 ("this current audio is good, use that only").
MUSIC_FILE = "om_04.mp3"

# One fixed engagement line on every Short (2026-10-08 request), small, last in the text block.
OPINION_TE = "ఈ వీడియోపై మీ అభిప్రాయాన్ని కామెంట్ చేయండి"
OPINION_EN = "Share your thoughts on this video in the comments"


def _blocks(row, layout):
    # Ponnala has no glyphs for quote marks, they would show as empty boxes
    te_clean = row["telugu"].translate({ord(c): None for c in "'\"‘’“”`"})
    te_lines = [s.strip() for s in te_clean.split("|")]
    en_lines = [s.strip() for s in row["english"].split("|")]
    blocks = []
    attr = row["category"] in ATTRIBUTED
    if row["category"] == "qa" and len(te_lines) == 2:
        blocks.append((te_lines[0], FONT_TE, 72, layout["accent"], False))
        blocks.append((te_lines[1], FONT_TE, 104, layout["te"], False))
        if attr:
            blocks.append((ATTR_TE, FONT_TE, 54, layout["accent"], False))
        blocks.append((en_lines[0], FONT_EN, 50, layout["accent"], False))
        blocks.append((en_lines[1] if len(en_lines) > 1 else "", FONT_EN, 70, layout["en"], False))
        if attr:
            blocks.append((ATTR_EN, FONT_EN, 38, layout["accent"], False))
    else:
        blocks.append((" ".join(te_lines), FONT_TE, 130, layout["te"], False))
        if attr:
            blocks.append((ATTR_TE, FONT_TE, 62, layout["accent"], False))
        blocks.append((" ".join(en_lines), FONT_EN, 84, layout["en"], False))
        if attr:
            blocks.append((ATTR_EN, FONT_EN, 44, layout["accent"], False))
    blocks.append((OPINION_TE, FONT_TE, 44, layout["accent"], False))
    blocks.append((OPINION_EN, FONT_EN, 34, layout["accent"], False))
    return [b for b in blocks if b[0]]


SCALES = [1.0, 0.94, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58, 0.52]


def fit_text(row, layout, max_h=None):
    """Largest scale at which the text block fits. Returns (laid, total_height, fits, scale)."""
    probe = ImageDraw.Draw(Image.new("L", (W, H)))
    limit = max_h or SAFE_BOTTOM - SAFE_TOP
    for scale in SCALES:
        laid, total = [], 0
        for text, path, size, color, bold in _blocks(row, layout):
            px = int(size * scale)
            stroke = max(1, px // 55) if bold else 0
            font = _font(path, px)
            lines = _wrap(probe, text, font, stroke)
            lh = int(px * (1.45 if path == FONT_TE else 1.35))
            laid.append((lines, font, color, stroke, lh))
            total += len(lines) * lh + 34
        total += 90 if SHOW_SOURCE_ON_VIDEO else 50  # ornament (and source line)
        if total <= limit:
            return laid, total, True, scale
    return laid, total, False, scale


def make_text_layer(row, layout, label_en="", label_te="", max_h=None, bottom=None, channel=True):
    laid, total, _fits, _scale = fit_text(row, layout, max_h)

    text_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("L", (W, H), 0)
    d, sd = ImageDraw.Draw(text_l), ImageDraw.Draw(shadow)
    y = int(layout["anchor"] * H - total / 2)
    y = max(SAFE_TOP + 40, min(y, (bottom or SAFE_BOTTOM) - total))

    if layout["ornament"]:
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
    if SHOW_SOURCE_ON_VIDEO:
        src_font = _font(FONT_EN_LIGHT, 34)
        src = row["source"]
        d.text(((W - d.textlength(src, font=src_font)) / 2, y), src, font=src_font, fill=SOFT)

    if label_en:  # special day header
        tf, ef = _font(FONT_TE, 64), _font(FONT_EN, 34)
        for txt, f, yy, col in ((label_te, tf, 250, GOLD), (f"Today: {label_en}", ef, 340, WHITE)):
            if txt:
                xy = ((W - d.textlength(txt, font=f)) / 2, yy)
                sd.text(xy, txt, font=f, fill=255, stroke_width=3)
                d.text(xy, txt, font=f, fill=col)

    if channel:
        cf = _font(FONT_EN_LIGHT, 30)
        d.text(((W - d.textlength(CHANNEL, font=cf)) / 2, 1560), CHANNEL, font=cf, fill=SOFT)

    blur = shadow.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.8))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    shade.putalpha(blur)
    return Image.alpha_composite(shade, text_l)


def _watermark(text_layer, handle, font_path, size=76, alpha=38):
    """Large, dim channel-handle watermark at the vertical middle of the frame
    (2026-10-07 request: overlaps the text on purpose, ~15% opacity)."""
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wm)
    f = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
    while d.textlength(handle, font=f) > W - 160 and size > 20:
        size -= 2
        f = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
    d.text(((W - d.textlength(handle, font=f)) / 2, H / 2), handle, font=f, fill=(255, 255, 255, alpha), anchor="lm")
    return Image.alpha_composite(text_layer, wm)


def pick_music(rng):
    fixed = ROOT / "assets" / MUSIC_FILE
    if fixed.exists():
        return str(fixed)
    clips = sorted(glob.glob(str(ROOT / "assets/om_0*.mp3")))
    if not clips:
        raise SystemExit("No assets/om_0*.mp3 found. Add your Om clips first.")
    return rng.choice(clips)


def render(row, out_mp4, date_key, special=None, workdir="out"):
    rng = random.Random(_seed(row, date_key))
    layout_idx = rng.randrange(len(LAYOUTS))
    layout = LAYOUTS[layout_idx]
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    bg_path, tx_path = work / "bg.png", work / "text.png"
    make_background(rng, date_key).save(bg_path)
    max_h, bottom, channel = None, None, True
    if photo_for(date_key):  # keep faces clear: text sits at the bottom, below the photo's face
        layout = dict(layout, anchor=0.78)
        max_h, bottom, channel = PHOTO_TEXT_H, PHOTO_TEXT_BOTTOM, False
    _watermark(
        make_text_layer(row, layout, (special or {}).get("label_en", ""), (special or {}).get("label_te", ""),
                        max_h, bottom, channel),
        HANDLE, FONT_EN,
    ).save(tx_path)
    music = pick_music(rng)
    if ZOOM > 0:
        bg_f = (f"[0:v]scale=2160:3840,zoompan=z='1+{ZOOM}*sin(PI*on/150)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                ":d=1:s=1080x1920:fps=30[bg];")
    else:
        bg_f = "[0:v]scale=1080:1920,setsar=1[bg];"
    fc = bg_f + "[1:v]format=rgba[tx];[bg][tx]overlay=format=auto,format=yuv420p[v]"  # text is static for the full 5 s
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-loop", "1", "-framerate", "30", "-t", "5", "-i", str(bg_path),
        "-loop", "1", "-framerate", "30", "-t", "5", "-i", str(tx_path),
        "-i", music,
        "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
        "-t", "5", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    return {"music": Path(music).name, "layout": layout_idx, "photo": Path(photo_for(date_key) or "gradient").name}
